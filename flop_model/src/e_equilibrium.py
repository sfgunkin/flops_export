"""
Step E: Capacity-constrained equilibrium — training and inference.

Solves the market-clearing equilibrium for each specification,
assigns trade regimes, and computes shadow values.
"""

import math
from collections import defaultdict

import config


# ── Capacity conversion ──

def capacity_mw_to_gpu_hr(mw):
    """Convert MW of DC capacity to GPU-hr/yr."""
    return mw * 1000 / config.GAMMA_KW * config.H_HOURS * config.BETA


# ── Training equilibrium solver ──

DOMESTIC_LATENCY = 5.0  # default domestic RTT (ms)


def solve_training_equilibrium(costs, capacities, demand_shares, lambdas,
                               sanctioned=None, max_iter=50):
    """
    Capacity-constrained training market clearing.

    Args:
        costs: dict iso3 → unit cost ($/GPU-hr)
        capacities: dict iso3 → capacity in GPU-hr/yr
        demand_shares: dict iso3 → ω_k
        lambdas: dict (iso_i, iso_j) → lam value
        sanctioned: set of ISO3 codes excluded from export
        max_iter: maximum iterations for fixed-point

    Returns dict with:
        p_T: training equilibrium price
        exporter_volumes: dict iso3 → GPU-hr exported
        importers: set of iso3 codes that import training
        training_output: dict iso3 → total training output (domestic + export)
        shares: dict iso3 → export share
        marginal_exporter: iso3 of marginal training exporter
    """
    if sanctioned is None:
        sanctioned = set()

    countries = list(costs.keys())
    Q = config.Q_TOTAL
    alpha = config.ALPHA_TRAIN

    # Build supply stack: non-sanctioned countries sorted by cost
    supply_stack = sorted(
        [(iso, costs[iso], capacities.get(iso, 0))
         for iso in countries if iso not in sanctioned and capacities.get(iso, 0) > 0],
        key=lambda x: x[1]
    )

    if not supply_stack:
        return {
            "p_T": float("inf"), "exporter_volumes": {}, "importers": set(),
            "training_output": {iso: 0 for iso in countries},
            "shares": {}, "marginal_exporter": None,
        }

    # Initialize p_T as cheapest supplier's cost
    p_T = supply_stack[0][1]

    for iteration in range(max_iter):
        # Determine who imports: k imports if ∃ j with (1+lam_jk)·p_T < c_k
        importers = set()
        for k in countries:
            c_k = costs[k]
            for j, c_j, cap_j in supply_stack:
                if j == k:
                    continue
                lam = lambdas.get((j, k), 0)
                if lam == math.inf:
                    continue
                delivered = (1 + lam) * p_T
                if delivered < c_k:
                    importers.add(k)
                    break

        # Total training export demand
        export_demand = sum(demand_shares.get(k, 0) for k in importers) * alpha * Q

        # Walk supply stack to find marginal exporter
        remaining = export_demand
        exporter_volumes = {}
        p_T_new = supply_stack[0][1]
        marginal = supply_stack[0][0]

        for iso, cost, cap in supply_stack:
            if remaining <= 0:
                break
            allocated = min(cap, remaining)
            if allocated > 0:
                exporter_volumes[iso] = allocated
                remaining -= allocated
                p_T_new = cost
                marginal = iso

        # Check convergence
        if abs(p_T_new - p_T) < 1e-8:
            p_T = p_T_new
            break
        p_T = p_T_new

    # Compute training output for all countries
    training_output = defaultdict(float)
    # Exporters produce their export volume
    for iso, vol in exporter_volumes.items():
        training_output[iso] += vol

    # Domestic producers: non-importers produce their own demand (capped by capacity)
    for k in countries:
        if k not in importers:
            domestic = demand_shares.get(k, 0) * alpha * Q
            cap = capacities.get(k, 0)
            # Cap domestic training to available capacity
            training_output[k] += min(domestic, max(0, cap - training_output[k]))

    # Export shares
    total_export = sum(exporter_volumes.values()) if exporter_volumes else 1
    shares = {iso: vol / total_export for iso, vol in exporter_volumes.items()}

    return {
        "p_T": p_T,
        "exporter_volumes": dict(exporter_volumes),
        "importers": importers,
        "training_output": dict(training_output),
        "shares": shares,
        "marginal_exporter": marginal,
    }


# ── Inference market solver ──

def solve_inference_market(costs, lambdas, latency, residual_capacities,
                           demand_shares, sanctioned=None):
    """
    Inference market: localized by latency, capacity-constrained.

    Uses residual capacity after training allocation.

    Args:
        costs: dict iso3 → unit cost
        lambdas: dict (iso_i, iso_j) → lam value
        latency: dict (iso_from, iso_to) → RTT ms
        residual_capacities: dict iso3 → remaining GPU-hr
        demand_shares: dict iso3 → ω_k
        sanctioned: set of sanctioned ISO3

    Returns dict with:
        inference_sources: dict iso_k → iso_j (who supplies k's inference)
        inference_output: dict iso3 → total inference output
        inference_exporters: set of iso3 that export inference
    """
    if sanctioned is None:
        sanctioned = set()

    countries = list(costs.keys())
    Q = config.Q_TOTAL
    alpha_inf = 1 - config.ALPHA_TRAIN

    # Track remaining capacity
    cap_remaining = dict(residual_capacities)
    inference_output = defaultdict(float)
    inference_sources = {}

    for k in countries:
        inf_demand = demand_shares.get(k, 0) * alpha_inf * Q
        if inf_demand <= 0:
            inference_sources[k] = k
            continue

        # Find eligible suppliers: within latency threshold
        candidates = []
        for j in countries:
            if j in sanctioned and j != k:
                continue
            # Get latency
            if j == k:
                lat = latency.get((j, k), DOMESTIC_LATENCY)
            else:
                lat = latency.get((j, k))
                if lat is None:
                    lat = latency.get((k, j))  # try reverse
                if lat is None:
                    continue  # no latency data → skip
                if lat > config.L_BAR_MS:
                    continue

            # Lambda
            lam = lambdas.get((j, k), 0)
            if lam == math.inf:
                continue

            # Delivered cost
            delivered = (1 + lam) * (1 + config.TAU * lat) * costs[j]
            candidates.append((j, delivered, lat))

        # Sort by delivered cost
        candidates.sort(key=lambda x: x[1])

        # Allocate demand across suppliers in cost order
        remaining_demand = inf_demand
        best_source = k  # default: domestic

        for j, deliv_cost, lat in candidates:
            if remaining_demand <= 0:
                break
            avail = cap_remaining.get(j, 0)
            if avail <= 0:
                continue
            allocated = min(avail, remaining_demand)
            inference_output[j] += allocated
            cap_remaining[j] -= allocated
            remaining_demand -= allocated
            if best_source == k:
                best_source = j  # primary source

        # If still unmet demand, falls to domestic (even without capacity constraint check)
        if remaining_demand > 0:
            inference_output[k] += remaining_demand

        inference_sources[k] = best_source

    # Identify inference exporters
    inference_exporters = set()
    for k, src in inference_sources.items():
        if src != k:
            inference_exporters.add(src)

    return {
        "inference_sources": inference_sources,
        "inference_output": dict(inference_output),
        "inference_exporters": inference_exporters,
    }


# ── Joint equilibrium ──

def solve_joint_equilibrium(costs, capacities, demand_shares, lambdas,
                            latency, sanctioned=None):
    """
    Joint training + inference equilibrium with shared capacity.

    1. Solve training equilibrium → training volumes, p_T
    2. Compute residual capacity
    3. Solve inference market using residual capacity
    4. Verify capacity constraints
    5. Compute shadow values

    Returns combined results dict.
    """
    if sanctioned is None:
        sanctioned = set()

    # Step 1: Training
    train_res = solve_training_equilibrium(
        costs, capacities, demand_shares, lambdas, sanctioned
    )

    # Step 2: Residual capacity
    residual = {}
    for iso in costs:
        cap = capacities.get(iso, 0)
        used = train_res["training_output"].get(iso, 0)
        residual[iso] = max(0.0, cap - used)

    # Step 3: Inference with residual
    inf_res = solve_inference_market(
        costs, lambdas, latency, residual, demand_shares, sanctioned
    )

    # Step 4: Capacity check
    for iso in costs:
        total = train_res["training_output"].get(iso, 0) + inf_res["inference_output"].get(iso, 0)
        cap = capacities.get(iso, 0)
        if total > cap * 1.001 and cap > 0:
            print(f"    WARNING: {iso} total output {total:.0f} > capacity {cap:.0f}")

    # Step 5: Shadow values
    p_T = train_res["p_T"]
    shadow_values = {}
    for iso in costs:
        total = train_res["training_output"].get(iso, 0) + inf_res["inference_output"].get(iso, 0)
        cap = capacities.get(iso, 0)
        if cap > 0 and total >= cap * 0.999:
            shadow_values[iso] = max(0, p_T - costs[iso])
        else:
            shadow_values[iso] = 0.0

    return {
        "p_T": p_T,
        "exporter_volumes": train_res["exporter_volumes"],
        "importers": train_res["importers"],
        "training_output": train_res["training_output"],
        "shares": train_res["shares"],
        "marginal_exporter": train_res["marginal_exporter"],
        "inference_sources": inf_res["inference_sources"],
        "inference_output": inf_res["inference_output"],
        "inference_exporters": inf_res["inference_exporters"],
        "shadow_value": shadow_values,
        "residual_capacity": residual,
    }


# ── Regime assignment ──

def assign_regime(iso, train_res, inf_res, costs, p_T, lambdas):
    """
    Assign two-letter regime code based on equilibrium results.

    EE = exports training + inference
    IE = imports training, exports inference
    DD = domestic both
    II = imports both
    ID = imports training, domestic inference
    """
    # Training status
    is_train_exporter = iso in train_res["shares"] and train_res["shares"][iso] > 0
    is_train_importer = iso in train_res["importers"]

    # Inference status
    is_inf_exporter = iso in inf_res["inference_exporters"]
    is_inf_domestic = inf_res["inference_sources"].get(iso, iso) == iso

    if is_train_exporter:
        return "EE"  # training exporters always also export inference (Prop 4)
    elif is_inf_exporter and not is_train_exporter:
        return "IE"
    elif not is_train_importer and is_inf_domestic:
        return "DD"
    elif is_train_importer and is_inf_domestic:
        return "ID"
    else:
        return "II"


# ── Run all specifications ──

def run_specification(panel, lambdas_dict, latency, cost_column, lam_key="bilateral"):
    """
    Run full joint equilibrium for one specification.

    Args:
        panel: DataFrame with costs and capacity
        lambdas_dict: dict with 'bilateral', 'uniform', 'fdi' keys
        latency: dict of (from, to) → ms
        cost_column: which column to use for costs ('c_raw', 'c_cr', 'c_adj')
        lam_key: which lambda matrix to use

    Returns dict with all equilibrium results + regime per country.
    """
    countries = list(panel["country_iso3"])
    costs = {iso: panel.loc[iso, cost_column] for iso in countries}
    capacities = {iso: capacity_mw_to_gpu_hr(panel.loc[iso, "capacity_mw"]) for iso in countries}
    demand_shares = {iso: panel.loc[iso, "demand_share"] for iso in countries}
    lambdas = lambdas_dict[lam_key]
    sanctioned = lambdas_dict.get("sanctioned", set())

    results = solve_joint_equilibrium(
        costs, capacities, demand_shares, lambdas, latency, sanctioned
    )

    # Assign regimes
    regimes = {}
    for iso in countries:
        regimes[iso] = assign_regime(
            iso, results, results, costs, results["p_T"], lambdas
        )
    results["regime"] = regimes

    # Lambda star: lam* = c_adj / p_T − 1
    p_T = results["p_T"]
    lambda_star = {}
    for iso in countries:
        lambda_star[iso] = costs[iso] / p_T - 1
    results["lambda_star"] = lambda_star

    # HHI of training exports
    shares = results["shares"]
    hhi = sum(s ** 2 for s in shares.values()) if shares else 0
    results["hhi_training"] = hhi

    return results


def run_all_specifications(panel, lambdas_dict, latency):
    """Run equilibrium for all 6 specifications (columns 1-4, 6, 7).

    Returns dict of spec_name → results.
    """
    results = {}

    # Col (1): raw costs, no sovereignty (lam=0)
    zero_lam = {(i, j): 0.0 for i in panel["country_iso3"] for j in panel["country_iso3"]}
    zero_lam_dict = {**lambdas_dict, "zero": zero_lam}

    print("    Column (1): raw costs, lam=0...")
    results["col1"] = run_specification(panel, zero_lam_dict, latency, "c_raw", "zero")

    # Col (2): cost-recovery costs, no sovereignty
    print("    Column (2): cost-recovery costs, lam=0...")
    results["col2"] = run_specification(panel, zero_lam_dict, latency, "c_cr", "zero")

    # Col (3): efficiency-adjusted costs, no sovereignty
    print("    Column (3): efficiency-adjusted costs, lam=0...")
    results["col3"] = run_specification(panel, zero_lam_dict, latency, "c_adj", "zero")

    # Col (4): efficiency-adjusted costs, bilateral sovereignty
    print("    Column (4): efficiency-adjusted costs, bilateral lam...")
    results["col4"] = run_specification(panel, lambdas_dict, latency, "c_adj", "bilateral")

    # Col (6): efficiency-adjusted costs, uniform sovereignty
    print("    Column (6): efficiency-adjusted costs, uniform lam=0.10...")
    results["col6"] = run_specification(panel, lambdas_dict, latency, "c_adj", "uniform")

    # Col (7): efficiency-adjusted costs, FDI sovereignty
    print("    Column (7): efficiency-adjusted costs, FDI lam...")
    results["col7"] = run_specification(panel, lambdas_dict, latency, "c_adj", "fdi")

    return results
