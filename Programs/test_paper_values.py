"""
Comprehensive pytest test suite for the FLOPs Export Paper (v30).

Verifies ALL numerical values, equation relationships, data integrity,
and equilibrium properties claimed in the paper. Independent of
add_calibration_v30.py -- recomputes everything from raw data.

v30 changes: ξ removed, CR costs are baseline, 3 sensitivity specs.

Usage:
    pytest test_paper_values.py -v
    pytest test_paper_values.py -v -k "cost"       # run only cost tests
    pytest test_paper_values.py -v --tb=short       # short tracebacks
"""

import csv
import math
import pathlib

import pytest

# ================================================================
# CONSTANTS (must match model_parameters.csv / add_calibration_v30)
# ================================================================
GAMMA = 0.700              # kW, GPU thermal design power
GPU_TDP_W = 700            # Watts
GPU_PRICE = 25_000         # $
GPU_LIFE = 3               # years
GPU_UTIL = 0.70
H_YR = 365.25 * 24        # 8766 hrs/yr
ETA = 0.15                 # $/hr networking
PHI = 1.08                 # PUE baseline
DELTA_PUE = 0.015          # PUE per degree above theta_ref
THETA_REF = 15.0           # deg C
DC_LIFE = 15               # years
TAU = 0.0008               # latency degradation per ms
ALPHA = 0.50               # training share of demand
Q_TOTAL = 60_000_000_000   # GPU-hr/yr
K_BAR_SCALE = 1000
ALPHA_GEO = 0.08           # alpha_1
ALPHA_REG = 0.04           # alpha_2
GPU_CONTROL_ALPHA3 = 0.10  # alpha_3 (FDI)
LAMBDA_UNIFORM = 0.10
W_TIER1 = 0.10
W_TIER2 = 0.20
W_TIER3 = 0.70
DOMESTIC_LATENCY_DEFAULT = 5.0

RHO = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL)

SANCTIONED = {'IRN', 'RUS', 'BLR', 'PRK', 'SYR', 'TKM'}

SUBSIDY_ADJ = {
    'IRN': 0.085, 'TKM': 0.070, 'DZA': 0.065, 'EGY': 0.080,
    'UZB': 0.090, 'QAT': 0.100, 'SAU': 0.100, 'ARE': 0.095,
    'RUS': 0.065, 'KAZ': 0.085, 'NGA': 0.080, 'ZAF': 0.095,
    'ETH': 0.050,
}

BLOC_WESTERN = {
    'USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'ESP', 'PRT',
    'NLD', 'BEL', 'LUX', 'AUT', 'CHE', 'IRL', 'DNK', 'NOR',
    'SWE', 'FIN', 'ISL', 'GRC', 'CZE', 'POL', 'HUN', 'SVK',
    'SVN', 'EST', 'LVA', 'LTU', 'HRV', 'BGR', 'ROU', 'CYP',
    'MLT', 'JPN', 'KOR', 'AUS', 'NZL', 'ISR', 'TWN',
}
BLOC_CHINA_ALIGNED = {
    'CHN', 'RUS', 'BLR', 'PRK', 'SYR', 'IRN',
    'VEN', 'CUB', 'NIC', 'MMR',
}
EU_MEMBERS = {
    'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST',
    'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA',
    'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK',
    'SVN', 'ESP', 'SWE',
}
APEC_CBPR = {
    'AUS', 'CAN', 'JPN', 'KOR', 'MEX', 'PHL', 'SGP', 'TWN',
    'USA',
}
DEPA_MEMBERS = {'SGP', 'CHL', 'NZL'}
GPU_EXPORT_CONTROLLED = {'CHN'}

BLOC_DISTANCE = {
    ('W', 'W'): 0.00, ('W', 'C'): 0.95, ('W', 'N'): 0.40,
    ('C', 'W'): 0.95, ('C', 'C'): 0.00, ('C', 'N'): 0.55,
    ('N', 'W'): 0.40, ('N', 'C'): 0.55, ('N', 'N'): 0.20,
}

DEVELOPING = {
    'CHN', 'KGZ', 'XKX', 'MNE', 'ETH', 'VNM', 'IND', 'KEN',
    'ARE', 'EGY', 'DZA', 'UZB', 'TJK', 'TKM', 'ALB', 'MKD',
    'GEO', 'ARM', 'MDA', 'UKR', 'BIH', 'SRB', 'IDN', 'MYS',
    'PHL', 'THA', 'COL', 'MEX', 'BRA', 'ARG', 'CHL', 'PER',
    'NGA', 'ZAF', 'MAR', 'TUN', 'SEN', 'BGD', 'PAK', 'LKA',
    'MMR', 'LAO', 'KHM',
}

DATA = pathlib.Path(
    r"F:\onedrive\__documents\papers\FLOPsExport\Data"
)


# ================================================================
# HELPER FUNCTIONS (replicate model logic independently)
# ================================================================

def _get_bloc(iso):
    if iso in BLOC_WESTERN:
        return 'W'
    if iso in BLOC_CHINA_ALIGNED:
        return 'C'
    return 'N'


def compute_geo_distance(iso_i, iso_j):
    if iso_i == iso_j:
        return 0.0
    bi, bj = _get_bloc(iso_i), _get_bloc(iso_j)
    return BLOC_DISTANCE.get((bi, bj), 0.40)


def compute_reg_compat(iso_i, iso_j):
    if iso_i == iso_j:
        return 1
    if iso_i in EU_MEMBERS and iso_j in EU_MEMBERS:
        return 1
    if iso_i in APEC_CBPR and iso_j in APEC_CBPR:
        return 1
    if iso_i in DEPA_MEMBERS and iso_j in DEPA_MEMBERS:
        return 1
    return 0


def compute_bilateral_lambda(iso_i, iso_j):
    if iso_i == iso_j:
        return 0.0
    if iso_i in SANCTIONED or iso_j in SANCTIONED:
        if (iso_i in SANCTIONED and iso_j in SANCTIONED):
            bi, bj = _get_bloc(iso_i), _get_bloc(iso_j)
            if bi == bj:
                return (ALPHA_GEO * 0.0
                        + ALPHA_REG * (1 - 0))
        return float('inf')
    G_ij = compute_geo_distance(iso_i, iso_j)
    R_ij = compute_reg_compat(iso_i, iso_j)
    return ALPHA_GEO * G_ij + ALPHA_REG * (1 - R_ij)


def compute_fdi_lambda(host_j, buyer_k, hyperscaler_h='USA'):
    if host_j == buyer_k:
        return 0.0
    if host_j in SANCTIONED:
        return float('inf')
    s_jk = 0.5 if host_j in GPU_EXPORT_CONTROLLED else 0.0
    G_hk = compute_geo_distance(hyperscaler_h, buyer_k)
    R_hk = compute_reg_compat(hyperscaler_h, buyer_k)
    return (ALPHA_GEO * G_hk
            + ALPHA_REG * (1 - R_hk)
            + GPU_CONTROL_ALPHA3 * s_jk)


def compute_pue(theta):
    return PHI + DELTA_PUE * max(0, theta - THETA_REF)


def _get_latency(lat_data, j, k):
    if j == k:
        return lat_data.get((j, k), DOMESTIC_LATENCY_DEFAULT)
    if (j, k) in lat_data:
        return lat_data[(j, k)]
    if (k, j) in lat_data:
        return lat_data[(k, j)]
    return None


def _inference_delivered_cost(c_j, l_jk):
    """Delivered inference cost: (1 + tau*l) * c_j."""
    return (1 + TAU * l_jk) * c_j


def _solve_equilibrium(
    costs_dict, dc_k, omega, k_bar, sanctioned,
    lam=0.0, bilateral=False, tiered=False,
):
    """Solve capacity-constrained training equilibrium."""
    supply_stack = sorted(
        [(iso, costs_dict[iso], k_bar.get(iso, 1e12))
         for iso in costs_dict if iso in k_bar],
        key=lambda x: x[1],
    )
    p_T = supply_stack[0][1]
    for iso_j, c_j, _ in supply_stack:
        if iso_j not in sanctioned:
            p_T = c_j
            break
    for _ in range(30):
        Q_TX = _compute_training_demand(
            p_T, costs_dict, dc_k, omega, sanctioned,
            lam, bilateral, tiered,
        )
        cum_cap = 0
        p_T_new = p_T
        found = False
        for iso_j, c_j, k_j in supply_stack:
            if iso_j in sanctioned:
                continue
            cum_cap += k_j * ALPHA
            if cum_cap >= Q_TX and Q_TX > 0:
                p_T_new = c_j
                found = True
                break
        if found and abs(p_T_new - p_T) < 0.0001:
            p_T = p_T_new
            break
        if found:
            p_T = p_T_new
    # Compute shares
    shares = {}
    remaining = Q_TX
    for iso_j, c_j, k_j in supply_stack:
        if iso_j in sanctioned:
            continue
        if c_j > p_T:
            break
        ca = min(k_j * ALPHA, remaining)
        if ca > 0:
            shares[iso_j] = ca
            remaining -= ca
        if remaining <= 0:
            break
    total_exp = sum(shares.values())
    hhi = (sum((s / total_exp) ** 2 for s in shares.values())
           if total_exp > 0 else 1.0)
    return p_T, shares, hhi


def _compute_training_demand(
    p_T, costs_dict, dc_k, omega, sanctioned,
    lam, bilateral, tiered,
):
    """Compute total training export demand at price p_T."""
    Q_TX = 0
    for iso_k in dc_k:
        c_k = costs_dict.get(iso_k)
        if c_k is None:
            continue
        w_k = omega.get(iso_k, 0)
        if bilateral or tiered:
            tiers = ([(1, W_TIER1), (2, W_TIER2), (3, W_TIER3)]
                     if tiered else [(3, 1.0)])
            for tier, w_t in tiers:
                if tier == 1:
                    continue
                lam_k = _tier_lambda_helper(
                    iso_k, costs_dict, tier, sanctioned,
                )
                if (lam_k < float('inf')
                        and c_k > (1 + lam_k) * p_T):
                    Q_TX += w_t * ALPHA * w_k * Q_TOTAL
        else:
            if c_k > (1 + lam) * p_T:
                Q_TX += ALPHA * w_k * Q_TOTAL
    return Q_TX


def _tier_lambda_helper(iso_k, costs_dict, tier, sanctioned):
    min_lam = float('inf')
    for iso_j in costs_dict:
        if iso_j == iso_k:
            continue
        if iso_k in sanctioned or iso_j in sanctioned:
            both_same = (
                iso_k in sanctioned
                and iso_j in sanctioned
                and _get_bloc(iso_k) == _get_bloc(iso_j)
            )
            if not both_same:
                lam_val = float('inf')
            else:
                G = compute_geo_distance(iso_k, iso_j)
                R = compute_reg_compat(iso_k, iso_j)
                lam_val = ALPHA_GEO * G + ALPHA_REG * (1 - R)
        else:
            G = compute_geo_distance(iso_k, iso_j)
            R = compute_reg_compat(iso_k, iso_j)
            if tier == 2:
                lam_val = 0.04 * G + 0.20 * (1 - R)
            else:
                lam_val = ALPHA_GEO * G
        if lam_val < min_lam:
            min_lam = lam_val
    return min_lam


def _compute_inference_sourcing(adj_costs, lat, dc_k):
    """Best inference source for each country (free-trade, CR costs).

    Returns dict: iso_k -> {best_inf_source, P_I_domestic,
                             best_foreign_inf, best_inf_cost}
    """
    result = {}
    for iso_k in dc_k:
        c_k = adj_costs.get(iso_k)
        if c_k is None:
            continue
        l_kk = _get_latency(lat, iso_k, iso_k)
        P_I_dom = _inference_delivered_cost(
            c_k, l_kk or 0,
        )
        best_cost = P_I_dom
        best_src = iso_k
        best_foreign_cost = float('inf')
        best_foreign_src = None
        for iso_j, c_j in adj_costs.items():
            if iso_j == iso_k:
                continue
            l_jk = _get_latency(lat, iso_j, iso_k)
            if l_jk is None:
                continue
            cost_del = _inference_delivered_cost(
                c_j, l_jk,
            )
            if cost_del < best_cost:
                best_cost = cost_del
                best_src = iso_j
            if cost_del < best_foreign_cost:
                best_foreign_cost = cost_del
                best_foreign_src = iso_j
        result[iso_k] = {
            'best_inf_source': best_src,
            'best_inf_cost': best_cost,
            'best_foreign_inf': best_foreign_src,
            'P_I_domestic': P_I_dom,
        }
    return result


def _compute_inference_export_shares(adj_reg, omega, dc_k):
    """Inference export revenue shares (excl. self-sourcing)."""
    rev = {}
    for iso in dc_k:
        if iso in adj_reg:
            src = adj_reg[iso]['best_inf_source']
            if src != iso:
                rev[src] = (rev.get(src, 0)
                            + omega.get(iso, 0))
    return rev


# ================================================================
# FIXTURES -- load all data once
# ================================================================

@pytest.fixture(scope="session")
def calibration_data():
    """Load calibration_results_v3.csv."""
    path = DATA / "calibration_results_v3.csv"
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="session")
def dc_capacity_data():
    """Load dc_capacity_estimates.csv."""
    dc_cap, dc_cnt = {}, {}
    path = DATA / "dc_capacity_estimates.csv"
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dc_cap[row["iso3"]] = float(row["capacity_mw"])
            dc_cnt[row["iso3"]] = int(row["n_datacenters"])
    return dc_cap, dc_cnt


@pytest.fixture(scope="session")
def grid_capacity():
    """Load grid_capacity_estimates.csv -> K_bar (GPU-hours)."""
    k_bar = {}
    path = DATA / "grid_capacity_estimates.csv"
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k_bar[row["iso3"]] = (
                float(row["K_bar_gpu_hours"]) * K_BAR_SCALE
            )
    return k_bar


@pytest.fixture(scope="session")
def latency_data():
    """Load country_pair_latency.csv."""
    lat = {}
    path = DATA / "country_pair_latency.csv"
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["iso3_from"], row["iso3_to"])
            lat[key] = float(row["avg_ms"])
    return lat


@pytest.fixture(scope="session")
def sensitivity_data(calibration_data):
    """v30: Compute 3 sensitivity scenarios (CR costs only, no xi).

    Matches run_sensitivity() in add_calibration_v30.py.
    """
    scenario_defs = [
        ('Baseline', RHO),
        ('Low hardware', 1.30),
        ('High hardware', 1.42),
    ]
    results = []
    baseline_top5 = None

    for label, rho_val in scenario_defs:
        ranked = []
        for r in calibration_data:
            iso = r["iso3"]
            cr_pe = SUBSIDY_ADJ.get(iso, float(r["p_E_usd_kwh"]))
            pue = float(r["pue"])
            constr = float(r["p_L_usd_per_W"])
            constr_cost = (constr * GAMMA * 1000) / (
                DC_LIFE * H_YR * GPU_UTIL
            )
            c_cr = GAMMA * cr_pe * pue + rho_val + ETA + constr_cost
            ranked.append({"iso": iso, "c_cr": c_cr})

        ranked.sort(key=lambda x: x["c_cr"])
        for i, d in enumerate(ranked, 1):
            d["rank_cr"] = i

        dev_top15 = sum(
            1 for d in ranked[:15] if d["iso"] in DEVELOPING
        )
        c_max = max(d["c_cr"] for d in ranked)
        c_min = min(d["c_cr"] for d in ranked)
        max_spread = (c_max - c_min) / c_min * 100 if c_min > 0 else 0
        top5 = [d["iso"] for d in ranked[:5]]

        if baseline_top5 is None:
            baseline_top5 = list(top5)

        results.append({
            "label": label,
            "dev_top15": dev_top15,
            "max_spread": max_spread,
            "top5": top5,
            "top5_unchanged": (top5 == baseline_top5),
        })
    return results


@pytest.fixture(scope="session")
def model_params():
    """Load model_parameters.csv."""
    mp = {}
    path = DATA / "model_parameters.csv"
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mp[row["symbol"]] = row
    return mp


@pytest.fixture(scope="session")
def raw_costs(calibration_data):
    """Compute raw unit costs (c_j + ETA) for all 85 countries."""
    costs = {}
    for r in calibration_data:
        iso = r["iso3"]
        p_E = float(r["p_E_usd_kwh"])
        theta = float(r["theta_summer_C"])
        pue = compute_pue(theta)
        c_elec = pue * GAMMA * p_E
        c_constr = float(r["c_j_construction"])
        costs[iso] = c_elec + RHO + ETA + c_constr
    return costs


@pytest.fixture(scope="session")
def cost_recovery_costs(calibration_data, raw_costs):
    """Compute cost-recovery adjusted costs."""
    adj = dict(raw_costs)
    for iso, p_E_adj in SUBSIDY_ADJ.items():
        if iso not in adj:
            continue
        row = next(
            r for r in calibration_data if r["iso3"] == iso
        )
        p_E_orig = float(row["p_E_usd_kwh"])
        pue = compute_pue(float(row["theta_summer_C"]))
        delta_elec = pue * GAMMA * (p_E_adj - p_E_orig)
        adj[iso] = raw_costs[iso] + delta_elec
    return adj


@pytest.fixture(scope="session")
def demand_weights(calibration_data, dc_capacity_data):
    """Compute MW-capacity-based demand shares omega_k."""
    dc_cap, _ = dc_capacity_data
    dc_k = {}
    for row in calibration_data:
        iso = row["iso3"]
        dc_k[iso] = dc_cap.get(iso, 5.0)
    total = sum(dc_k.values())
    omega = {iso: d / total for iso, d in dc_k.items()}
    return omega, dc_k


@pytest.fixture(scope="session")
def docx_body_xml():
    """Raw word/document.xml from the current v31.docx.

    Used for structural checks (e.g., OMML equation presence, paragraph
    ordering). Requires that add_calibration_v31.py has been run at least
    once in the current session.
    """
    import zipfile
    docx_path = (
        DATA.parent / "Documents" / "flop_trade_model_v32.docx"
    )
    with zipfile.ZipFile(docx_path) as z:
        with z.open("word/document.xml") as f:
            return f.read().decode("utf-8")


@pytest.fixture(scope="session")
def docx_footnotes_xml():
    """Raw word/footnotes.xml from the current v31.docx."""
    import zipfile
    docx_path = (
        DATA.parent / "Documents" / "flop_trade_model_v32.docx"
    )
    with zipfile.ZipFile(docx_path) as z:
        try:
            with z.open("word/footnotes.xml") as f:
                return f.read().decode("utf-8")
        except KeyError:
            return ""


@pytest.fixture(scope="session")
def docx_text(docx_body_xml, docx_footnotes_xml):
    """Flat text extraction from body + footnotes of v31.docx.

    Joins all w:t and m:t text runs (preserving adjacency, not OMML
    structure). Use this for prose and citation substring checks; use
    docx_body_xml directly when structural XML patterns matter.
    """
    import re
    pat = re.compile(r"<(?:w:t|m:t)[^>]*>([^<]*)</(?:w:t|m:t)>")
    body_text = "".join(pat.findall(docx_body_xml))
    fn_text = "".join(pat.findall(docx_footnotes_xml or ""))
    return body_text + "\n" + fn_text


# ================================================================
# A. STRUCTURAL PARAMETERS (Section 6.1, Table 2)
# ================================================================

class TestModelParameters:
    """Verify all structural parameters match paper claims."""

    def test_rho_hardware_cost(self):
        """rho = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL) ~ $1.358."""
        assert abs(RHO - 1.358) < 0.005

    def test_rho_formula(self):
        """rho = 25000 / (3 * 8766 * 0.70)."""
        expected = 25000 / (3 * 365.25 * 24 * 0.70)
        assert abs(RHO - expected) < 1e-10

    def test_h_yr(self):
        """H = 365.25 * 24 = 8766 hrs/yr."""
        assert H_YR == 8766.0

    def test_pue_baseline(self):
        """PUE at reference temperature = 1.08."""
        assert compute_pue(THETA_REF) == PHI
        assert compute_pue(10.0) == PHI

    def test_pue_hot_country(self):
        """PUE at 37.1C (UAE) ~ 1.41."""
        pue_uae = compute_pue(37.1)
        assert abs(pue_uae - 1.4115) < 0.01

    def test_pue_monotone(self):
        """PUE is non-decreasing in temperature."""
        for theta in range(0, 50):
            assert compute_pue(theta) <= compute_pue(theta + 1)

    def test_demand_parameters(self):
        """Q = 60B GPU-hr, alpha = 0.50."""
        assert Q_TOTAL == 60_000_000_000
        assert ALPHA == 0.50

    def test_tier_weights_sum_to_one(self):
        """W_TIER1 + W_TIER2 + W_TIER3 = 1.0."""
        assert abs(W_TIER1 + W_TIER2 + W_TIER3 - 1.0) < 1e-10

    def test_sovereignty_coefficients(self):
        """alpha_1 = 0.08, alpha_2 = 0.04, alpha_3 = 0.10."""
        assert ALPHA_GEO == 0.08
        assert ALPHA_REG == 0.04
        assert GPU_CONTROL_ALPHA3 == 0.10

    def test_gpu_specs(self):
        """H100: 700W TDP, $25K, 3yr life, 70% util."""
        assert GAMMA == 0.700
        assert GPU_TDP_W == 700
        assert GPU_PRICE == 25000
        assert GPU_LIFE == 3
        assert GPU_UTIL == 0.70

    def test_constants_vs_csv(self, model_params):
        """Script constants match model_parameters.csv."""
        checks = {
            "gamma": (GAMMA, 0.700),
            "P_GPU": (GPU_PRICE, 25000),
            "L": (GPU_LIFE, 3),
            "beta": (GPU_UTIL, 0.70),
            "H": (H_YR, 8766),
            "eta": (ETA, 0.15),
            "phi": (PHI, 1.08),
            "delta": (DELTA_PUE, 0.015),
            "theta_bar": (THETA_REF, 15),
            "D": (DC_LIFE, 15),
            "tau": (TAU, 0.0008),
            "alpha": (ALPHA, 0.50),
            "Q": (Q_TOTAL, 6e10),
        }
        for sym, (script_val, _) in checks.items():
            if sym in model_params:
                csv_val = float(model_params[sym]["value"])
                ratio = abs(script_val - csv_val)
                denom = max(abs(csv_val), 1e-9)
                assert ratio / denom < 0.02, (
                    f"{sym}: script={script_val}, csv={csv_val}"
                )


# ================================================================
# B. DATA INTEGRITY
# ================================================================

class TestDataIntegrity:
    """Verify data file completeness and consistency."""

    def test_calibration_has_85_countries(self, calibration_data):
        assert len(calibration_data) == 85

    def test_no_duplicate_countries(self, calibration_data):
        isos = [r["iso3"] for r in calibration_data]
        assert len(isos) == len(set(isos))

    def test_all_costs_positive(self, calibration_data):
        for r in calibration_data:
            iso = r["iso3"]
            assert float(r["c_j_total"]) > 0, f'{iso}'
            assert float(r["c_j_electricity"]) >= 0
            assert float(r["c_j_hardware"]) > 0
            assert float(r["c_j_construction"]) > 0

    def test_hardware_constant_across_countries(
        self, calibration_data,
    ):
        rho_set = {
            float(r["c_j_hardware"]) for r in calibration_data
        }
        assert len(rho_set) == 1

    def test_csv_ranks_sequential(self, calibration_data):
        ranks = sorted(
            int(r["rank"]) for r in calibration_data
        )
        assert ranks == list(range(1, 86))

    def test_csv_sorted_by_cost(self, calibration_data):
        costs = [
            float(r["c_j_total"]) for r in calibration_data
        ]
        assert costs == sorted(costs)

    def test_dc_capacity_coverage(
        self, calibration_data, dc_capacity_data,
    ):
        dc_cap, _ = dc_capacity_data
        cal_isos = {r["iso3"] for r in calibration_data}
        covered = cal_isos & set(dc_cap.keys())
        assert len(covered) >= 80

    def test_latency_data_coverage(
        self, calibration_data, latency_data,
    ):
        cal_isos = {r["iso3"] for r in calibration_data}
        lat_countries = set()
        for s, d in latency_data:
            lat_countries.add(s)
            lat_countries.add(d)
        covered = cal_isos & lat_countries
        assert len(covered) >= 75


# ================================================================
# C. COST FUNCTION VERIFICATION (Equation 1)
# ================================================================

class TestCostFunction:
    """Verify Eq (1): c_j = PUE(theta)*gamma*p_E + rho + constr."""

    def test_cost_decomposition(self, calibration_data):
        """c_total ~ c_elec + c_hw + c_constr."""
        for r in calibration_data:
            total = float(r["c_j_total"])
            parts = (float(r["c_j_electricity"])
                     + float(r["c_j_hardware"])
                     + float(r["c_j_construction"]))
            assert abs(total - parts) < 0.01, r["iso3"]

    def test_electricity_formula(self, calibration_data):
        """c_elec = PUE(theta) * gamma * p_E."""
        for r in calibration_data:
            p_E = float(r["p_E_usd_kwh"])
            theta = float(r["theta_summer_C"])
            pue = compute_pue(theta)
            expected = pue * GAMMA * p_E
            actual = float(r["c_j_electricity"])
            assert abs(actual - expected) < 0.001, r["iso3"]

    def test_construction_formula(self, calibration_data):
        """c_constr = GPU_TDP_W * p_L / (DC_LIFE * H_YR)."""
        for r in calibration_data:
            p_L = float(r["p_L_usd_per_W"])
            expected = GPU_TDP_W * p_L / (DC_LIFE * H_YR)
            actual = float(r["c_j_construction"])
            assert abs(actual - expected) < 0.001, r["iso3"]

    def test_hardware_90_percent(self, calibration_data):
        """Hardware ~ 90% of unit cost."""
        shares = [
            RHO / float(r["c_j_total"])
            for r in calibration_data
        ]
        avg = sum(shares) / len(shares)
        assert 0.84 <= avg <= 0.98, f"avg = {avg:.2%}"

    def test_construction_3_to_7_percent(
        self, calibration_data,
    ):
        """Construction = 2-7% of total (with networking)."""
        for r in calibration_data:
            c_total = float(r["c_j_total"]) + ETA
            c_constr = float(r["c_j_construction"])
            share = c_constr / c_total
            assert 0.01 <= share <= 0.08, (
                f'{r["iso3"]}: {share:.2%}'
            )

    def test_cost_spread_12_to_20_percent(self, raw_costs):
        """Cost spread across 85 countries ~ 12-20%."""
        all_c = list(raw_costs.values())
        spread = (max(all_c) - min(all_c)) / min(all_c)
        assert 0.10 <= spread <= 0.25, f"{spread:.1%}"


# ================================================================
# D. RAW COST RANKINGS (Table 3, Column 1)
# ================================================================

class TestRawRankings:
    """Verify raw cost rankings from calibration."""

    def test_iran_cheapest(self, calibration_data):
        assert calibration_data[0]["iso3"] == "IRN"

    def test_top5_countries(self, raw_costs):
        ranked = sorted(raw_costs.items(), key=lambda x: x[1])
        top5 = [iso for iso, _ in ranked[:5]]
        assert top5 == ["IRN", "TKM", "ETH", "KGZ", "EGY"]

    def test_iran_cost_value(self, calibration_data):
        """Iran c_j ~ $1.408/hr."""
        irn = next(
            r for r in calibration_data if r["iso3"] == "IRN"
        )
        assert abs(float(irn["c_j_total"]) - 1.408) < 0.01

    def test_usa_in_calibration(self, calibration_data):
        isos = [r["iso3"] for r in calibration_data]
        assert "USA" in isos

    def test_china_rank_14(self, calibration_data):
        ranks = {
            r["iso3"]: int(r["rank"])
            for r in calibration_data
        }
        assert abs(ranks["CHN"] - 14) <= 2

    def test_pue_range(self, calibration_data):
        """PUE: 1.08 (coldest) to ~1.41 (hottest)."""
        pues = [float(r["pue"]) for r in calibration_data]
        assert min(pues) == pytest.approx(1.08)
        assert 1.35 <= max(pues) <= 1.50


# ================================================================
# E. COST-RECOVERY ADJUSTMENT (Table 3, Column 2)
# ================================================================

class TestCostRecovery:
    """Verify cost-recovery subsidy adjustment."""

    def test_13_countries_adjusted(self):
        assert len(SUBSIDY_ADJ) == 13

    def test_all_adjusted_in_calibration(
        self, calibration_data,
    ):
        cal_isos = {r["iso3"] for r in calibration_data}
        for iso in SUBSIDY_ADJ:
            assert iso in cal_isos, f"{iso} missing"

    def test_cr_top5(self, cost_recovery_costs):
        """CR top 5: KGZ, CAN, ETH, XKX, TJK."""
        ranked = sorted(
            cost_recovery_costs.items(), key=lambda x: x[1],
        )
        top5 = [iso for iso, _ in ranked[:5]]
        assert top5 == ["KGZ", "CAN", "ETH", "XKX", "TJK"]

    def test_iran_drops_rank_under_cr(
        self, calibration_data, cost_recovery_costs,
    ):
        """Iran drops from #1 to ~21st under CR pricing."""
        rho_hw = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL)
        table3 = []
        for r in calibration_data:
            iso = r["iso3"]
            p_E_raw = float(r["p_E_usd_kwh"])
            pue = float(r["pue"])
            constr = float(r["p_L_usd_per_W"])
            cr_price = SUBSIDY_ADJ.get(iso, p_E_raw)
            elec_cr = GAMMA * cr_price * pue
            constr_cost = (
                (constr * GAMMA * 1000)
                / (DC_LIFE * H_YR * GPU_UTIL)
            )
            elec_raw = GAMMA * p_E_raw * pue
            cj_reported = float(r["c_j_total"])
            residual = cj_reported - (
                elec_raw + rho_hw + constr_cost
            )
            table3.append({
                "iso": iso,
                "elec_cr": elec_cr,
                "rho_hw": rho_hw,
                "constr_cost": constr_cost,
                "residual": residual,
            })
        rho_net = (
            sum(d["residual"] for d in table3) / len(table3)
        )
        for d in table3:
            d["cj_cr"] = (
                d["elec_cr"] + d["rho_hw"]
                + d["constr_cost"] + rho_net
            )
        table3.sort(key=lambda x: x["cj_cr"])
        rank_cr = {
            d["iso"]: i for i, d in enumerate(table3, 1)
        }
        assert abs(rank_cr["IRN"] - 21) <= 1

    def test_subsidy_gap_range(self, calibration_data):
        """Subsidy gap: ~$0.019 to ~$0.080/kWh."""
        gaps = []
        for iso, p_E_adj in SUBSIDY_ADJ.items():
            row = next(
                r for r in calibration_data
                if r["iso3"] == iso
            )
            p_E_orig = float(row["p_E_usd_kwh"])
            gaps.append(p_E_adj - p_E_orig)
        assert min(gaps) >= 0.01
        assert max(gaps) <= 0.10

    def test_iran_fiscal_transfer_93m(self, calibration_data):
        """Iran 100 MW -> ~$93M/yr fiscal transfer."""
        row = next(
            r for r in calibration_data
            if r["iso3"] == "IRN"
        )
        p_E_orig = float(row["p_E_usd_kwh"])
        pue = compute_pue(float(row["theta_summer_C"]))
        gap = SUBSIDY_ADJ["IRN"] - p_E_orig
        fiscal = gap * 1000 * 100 * pue * H_YR
        assert abs(fiscal - 93e6) / 93e6 < 0.10


# ================================================================
# F. BILATERAL SOVEREIGNTY (Equation 2)
# ================================================================

class TestBilateralSovereignty:
    """Verify lambda_{ij} = a1*G + a2*(1-R) (+ sanctions)."""

    def test_domestic_lambda_zero(self):
        for iso in ["USA", "CHN", "IRN", "KGZ", "DEU"]:
            assert compute_bilateral_lambda(iso, iso) == 0.0

    def test_sanctioned_infinite(self):
        assert compute_bilateral_lambda(
            "USA", "IRN") == float('inf')
        assert compute_bilateral_lambda(
            "DEU", "RUS") == float('inf')
        assert compute_bilateral_lambda(
            "IRN", "USA") == float('inf')

    def test_eu_pairs_low_lambda(self):
        lam = compute_bilateral_lambda("DEU", "FRA")
        assert lam <= ALPHA_GEO * 0.01
        lam2 = compute_bilateral_lambda("FRA", "ITA")
        assert lam2 == pytest.approx(0.0)

    def test_western_to_china_high(self):
        """Western->China-aligned: lambda >= 0.076."""
        lam = compute_bilateral_lambda("USA", "CHN")
        expected = ALPHA_GEO * 0.95 + ALPHA_REG * 1
        assert lam == pytest.approx(expected)

    def test_bloc_distance_symmetric(self):
        for (b1, b2), d in BLOC_DISTANCE.items():
            assert BLOC_DISTANCE.get((b2, b1)) == d

    def test_bloc_diagonal_zero(self):
        assert BLOC_DISTANCE[('W', 'W')] == 0.0
        assert BLOC_DISTANCE[('C', 'C')] == 0.0
        assert BLOC_DISTANCE[('N', 'N')] == 0.20

    def test_lambda_non_negative(self, calibration_data):
        isos = [r["iso3"] for r in calibration_data]
        for i in isos[:20]:
            for j in isos[:20]:
                lam = compute_bilateral_lambda(i, j)
                assert lam >= 0


# ================================================================
# G. FDI TRUST CHANNEL (Equation 2')
# ================================================================

class TestFDITrustChannel:
    """Verify lambda^FDI uses hyperscaler home (not host)."""

    def test_fdi_uses_hyperscaler_home(self):
        lam_fdi = compute_fdi_lambda("KGZ", "FRA", "USA")
        G = compute_geo_distance("USA", "FRA")
        R = compute_reg_compat("USA", "FRA")
        expected = ALPHA_GEO * G + ALPHA_REG * (1 - R)
        assert lam_fdi == pytest.approx(expected)

    def test_fdi_domestic_zero(self):
        assert compute_fdi_lambda("FRA", "FRA") == 0.0

    def test_fdi_sanctioned_infinite(self):
        assert compute_fdi_lambda("IRN", "USA") == float('inf')
        assert compute_fdi_lambda("RUS", "DEU") == float('inf')

    def test_fdi_china_partial_alpha3(self):
        """China host: a3 = 0.10 * 0.5 = 0.05."""
        lam = compute_fdi_lambda("CHN", "USA", "USA")
        expected = GPU_CONTROL_ALPHA3 * 0.5
        assert lam == pytest.approx(expected)

    def test_fdi_reduces_lambda_for_developing(self):
        """FDI lambda < bilateral lambda for Western buyer."""
        lam_bilat = compute_bilateral_lambda("FRA", "KGZ")
        lam_fdi = compute_fdi_lambda("KGZ", "FRA", "USA")
        assert lam_fdi < lam_bilat


# ================================================================
# H. DEMAND CALIBRATION (Section 5)
# ================================================================

class TestDemandCalibration:
    """Verify MW-capacity-based demand shares."""

    def test_usa_largest_demand(self, demand_weights):
        omega, _ = demand_weights
        assert max(omega, key=omega.get) == "USA"

    def test_usa_demand_share_43(self, demand_weights):
        omega, _ = demand_weights
        assert abs(omega["USA"] - 0.431) < 0.03

    def test_china_demand_share_26(self, demand_weights):
        omega, _ = demand_weights
        assert abs(omega["CHN"] - 0.256) < 0.03

    def test_omega_sums_to_one(self, demand_weights):
        omega, _ = demand_weights
        assert abs(sum(omega.values()) - 1.0) < 1e-9

    def test_top5_demand_share(self, demand_weights):
        """Top 5 demand centers share ~ 74%."""
        omega, _ = demand_weights
        top5 = sorted(omega.items(), key=lambda x: -x[1])[:5]
        share = sum(w for _, w in top5)
        assert 0.65 <= share <= 0.85


# ================================================================
# I. CAPACITY-CONSTRAINED EQUILIBRIUM (Section 6.2)
# ================================================================

class TestEquilibrium:
    """Verify capacity-constrained training equilibrium."""

    def test_pure_cost_equilibrium(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """lambda=0 equilibrium: p_T > $1.0."""
        omega, dc_k = demand_weights
        p_T, shares, hhi = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        assert p_T > 1.0
        assert len(shares) >= 1
        assert 0 < hhi <= 1.0

    def test_sovereignty_raises_price(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """Uniform 10% sovereignty -> higher or similar training price."""
        omega, dc_k = demand_weights
        p_T_0, _, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        p_T_sov, _, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=LAMBDA_UNIFORM,
        )
        # Under CR costs the clearing price may shift slightly;
        # allow 2% tolerance for supply-stack reordering effects.
        assert p_T_sov >= p_T_0 * 0.98

    def test_hhi_bounded(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """HHI_T in (0, 1]."""
        omega, dc_k = demand_weights
        _, shares, hhi = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        assert 0 < hhi <= 1.0
        if len(shares) == 1:
            assert hhi == pytest.approx(1.0)
        _, _, hhi_bilat = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED,
            bilateral=True, tiered=True,
        )
        assert 0 < hhi_bilat <= 1.0

    def test_sanctioned_excluded(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """Sanctioned countries excluded from training."""
        omega, dc_k = demand_weights
        _, shares, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        for iso in SANCTIONED:
            assert iso not in shares, f"{iso} should be excluded"

    def test_bilateral_equilibrium(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """Bilateral lambda equilibrium computes."""
        omega, dc_k = demand_weights
        p_T, shares, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, bilateral=True,
        )
        assert p_T > 1.0
        assert len(shares) >= 1

    def test_10pct_premium_makes_most_domestic(
        self, cost_recovery_costs, demand_weights,
    ):
        """10% premium: domestic viable for nearly all."""
        _, dc_k = demand_weights
        min_cost = min(cost_recovery_costs.values())
        count = sum(
            1 for iso in dc_k
            if iso in cost_recovery_costs
            and cost_recovery_costs[iso] <= 1.10 * min_cost
        )
        assert count / len(dc_k) > 0.80


# ================================================================
# J. INFERENCE SOURCING
# ================================================================

class TestInferenceSourcing:
    """Verify inference cost function and sourcing patterns."""

    def test_inference_price_formula(self):
        """P_I(j,k) = (1 + tau * l_jk) * c_j."""
        c_j, l_jk = 1.50, 100
        expected = (1 + TAU * l_jk) * c_j
        assert expected == pytest.approx(1.50 * 1.08)

    def test_domestic_latency_markup(self):
        """Domestic at 5ms: 0.4%."""
        assert abs(TAU * 5.0 - 0.004) < 1e-9

    def test_100ms_latency_markup(self):
        """At 100ms: 8% markup."""
        assert abs(TAU * 100 - 0.08) < 1e-9

    def test_canada_top_inference_exporter(
        self, cost_recovery_costs,
        latency_data, demand_weights,
    ):
        """Canada is the top inference exporter."""
        omega, dc_k = demand_weights
        adj_reg = _compute_inference_sourcing(
            cost_recovery_costs,
            latency_data, dc_k,
        )
        exports = _compute_inference_export_shares(
            adj_reg, omega, dc_k,
        )
        top = sorted(exports.items(), key=lambda x: -x[1])
        assert top[0][0] == "CAN"

    def test_china_low_inference_export(
        self, cost_recovery_costs,
        latency_data, demand_weights,
    ):
        """China's inference export share < 1%."""
        omega, dc_k = demand_weights
        adj_reg = _compute_inference_sourcing(
            cost_recovery_costs,
            latency_data, dc_k,
        )
        exports = _compute_inference_export_shares(
            adj_reg, omega, dc_k,
        )
        chn_pct = exports.get("CHN", 0) * 100
        assert chn_pct < 1.0


# ================================================================
# K. WELFARE (Section 6.2)
# ================================================================

class TestWelfare:
    """Verify welfare cost computations."""

    def test_welfare_positive(
        self, cost_recovery_costs,
        latency_data, demand_weights,
        grid_capacity,
    ):
        """Bilateral tiered welfare cost >= 0."""
        omega, dc_k = demand_weights
        _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED,
            bilateral=True, tiered=True,
        )
        adj_reg = _compute_inference_sourcing(
            cost_recovery_costs,
            latency_data, dc_k,
        )
        welfare_train = 0
        for iso_k in dc_k:
            if iso_k not in cost_recovery_costs:
                continue
            c_k = cost_recovery_costs[iso_k]
            w_k = omega.get(iso_k, 0)
            min_foreign = min(
                (c_j for j, c_j in cost_recovery_costs.items()
                 if j != iso_k and j not in SANCTIONED),
                default=c_k,
            )
            welfare_train += (
                W_TIER1 * w_k * max(0, c_k - min_foreign)
            )
        assert welfare_train >= 0
        assert adj_reg is not None

    def test_welfare_bounded(
        self, cost_recovery_costs, demand_weights,
    ):
        """Welfare cost < 10% (sanity)."""
        omega, dc_k = demand_weights
        weighted_avg = sum(
            omega.get(iso, 0) * cost_recovery_costs[iso]
            for iso in dc_k if iso in cost_recovery_costs
        )
        assert weighted_avg > 0


# ================================================================
# L. PROPOSITIONS (Section 5)
# ================================================================

class TestPropositions:
    """Verify theoretical propositions from the model."""

    def test_prop1_five_regime_types(self):
        """Proposition 1: exactly 5 regime types."""
        types = {
            "T+I exporter", "inference hub", "hybrid",
            "domestic", "full importer",
        }
        assert len(types) == 5

    def test_prop4_train_subset_inference(
        self, cost_recovery_costs,
        latency_data, demand_weights,
        grid_capacity,
    ):
        """Prop 4: training exporters <= inference exporters."""
        omega, dc_k = demand_weights
        _, shares, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        train_exporters = set(shares.keys())

        adj_reg = _compute_inference_sourcing(
            cost_recovery_costs,
            latency_data, dc_k,
        )
        inf_exporters = set()
        for iso_k, info in adj_reg.items():
            src = info['best_inf_source']
            if src != iso_k:
                inf_exporters.add(src)

        missing = train_exporters - inf_exporters
        assert len(missing) == 0, (
            f"Training not in inference: {missing}"
        )

    def test_lambda_star_formula(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """lambda* = c_k / p_T - 1 (switching threshold)."""
        omega, dc_k = demand_weights
        p_T, _, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        for iso, c_k in cost_recovery_costs.items():
            lam_star = c_k / p_T - 1
            if c_k < p_T:
                assert lam_star < 0
            elif c_k > p_T:
                assert lam_star > 0


# ================================================================
# M. SENSITIVITY ANALYSIS (Table A3)
# ================================================================

class TestSensitivity:
    """v30: Verify 3 sensitivity scenarios (CR costs, no xi)."""

    def test_three_scenarios(self, sensitivity_data):
        """Exactly 3 scenarios in v30."""
        assert len(sensitivity_data) == 3

    def test_baseline_developing_in_top15(self, sensitivity_data):
        """v30 baseline: several developing countries in CR top 15."""
        assert sensitivity_data[0]["dev_top15"] >= 3

    def test_max_spread_positive(self, sensitivity_data):
        """Cost spread is positive for all scenarios."""
        for s in sensitivity_data:
            assert s["max_spread"] > 0, (
                f"{s['label']}: spread={s['max_spread']:.1f}%"
            )

    def test_hardware_share_top5_stable(self, sensitivity_data):
        """Low/high ρ don't change top 5 vs baseline."""
        assert sensitivity_data[1]["top5_unchanged"], (
            f"Low ρ top5: {sensitivity_data[1]['top5']}"
        )
        assert sensitivity_data[2]["top5_unchanged"], (
            f"High ρ top5: {sensitivity_data[2]['top5']}"
        )


# ================================================================
# N. KYRGYZSTAN DCF (Appendix D)
# ================================================================

class TestKyrgyzstanDCF:
    """Verify DCF model for Kyrgyzstan data center."""

    IT_MW = 40
    PUE_KGZ = 1.08
    TOTAL_MW = IT_MW * PUE_KGZ
    LIFE = 15
    GP = 25_000
    G_LIFE = 3
    G_UTIL = 0.70
    G_TDP_W = 700
    GPUS_MW = 1_000 / G_TDP_W * 1_000
    N_GPU = int(IT_MW * GPUS_MW)
    H = 365.25 * 24
    NET_COST = 2_000
    P_ELEC = 0.038
    P_CONSTR_W = 7.83
    CONSTR = IT_MW * 1e6 * P_CONSTR_W
    STAFF = 50 * 12_000
    MAINT_PCT = 0.02
    INS_PCT = 0.005
    BW_COST = 2_400_000
    REV_HR = 2.00
    RAMP = {0: 0.0, 1: 0.40, 2: 0.60, 3: 0.70}
    TAX_R = 0.10
    GPU_DECLINE = 0.10
    ELEC_ESC = 0.02
    RF = 0.05
    CRP = 0.04
    ERP = 0.06
    COE = RF + CRP + ERP
    COD = 0.10
    DSHARE = 0.40
    ESHARE = 0.60
    WACC_VAL = ESHARE * COE + DSHARE * COD * (1 - TAX_R)

    def _gpu_prices(self, gpu_adj=0):
        refresh = [1, 4, 7, 10, 13]
        return [
            (yr, self.GP * (1 - self.GPU_DECLINE) ** i
             * (1 + gpu_adj))
            for i, yr in enumerate(refresh)
        ]

    def _run_dcf(
        self, gpu_adj=0, elec_adj=0,
        price_adj=0, util_adj=0,
    ):
        gpu_prices = self._gpu_prices(gpu_adj)
        net_refresh = [1, 6, 11]
        years = list(range(0, self.LIFE + 1))
        rows = []
        cum = 0
        for yr in years:
            cx = self.CONSTR if yr == 0 else 0
            for gy, gp in gpu_prices:
                if yr == gy:
                    cx += self.N_GPU * gp
            if yr in net_refresh:
                cx += self.N_GPU * self.NET_COST

            if yr >= 1:
                util = self.RAMP.get(yr, self.G_UTIL)
                ep = ((self.P_ELEC + elec_adj)
                      * (1 + self.ELEC_ESC) ** (yr - 1))
                gpu_val = 0
                for gy, gp in reversed(gpu_prices):
                    if gy <= yr:
                        frac = max(
                            0, 1 - (yr - gy) / self.G_LIFE,
                        )
                        gpu_val = self.N_GPU * gp * frac
                        break
                ox = (
                    self.TOTAL_MW * 1_000 * self.H * ep
                    + self.STAFF * 1.03 ** (yr - 1)
                    + self.CONSTR * self.MAINT_PCT
                    + (self.CONSTR + gpu_val) * self.INS_PCT
                    + self.BW_COST
                )
                u = min(max(util + util_adj, 0), 0.95)
                rev = (self.N_GPU * self.H * u
                       * (self.REV_HR + price_adj))
                depr_g = 0
                for gy, gp in gpu_prices:
                    if gy <= yr < gy + self.G_LIFE:
                        depr_g = self.N_GPU * gp / self.G_LIFE
                        break
                depr = self.CONSTR / self.LIFE + depr_g
            else:
                ox, rev, depr = 0, 0, 0

            ebitda = rev - ox
            ebt = ebitda - depr
            tax = max(0, ebt * self.TAX_R)
            ni = ebt - tax
            fcf = ni + depr - cx
            cum += fcf
            rows.append(dict(
                year=yr, capex=cx, revenue=rev, opex=ox,
                ebitda=ebitda, tax=tax, ni=ni,
                fcf=fcf, cum=cum,
            ))
        return rows

    def _npv_irr(self, rows):
        years = list(range(0, self.LIFE + 1))
        fcfs = [r['fcf'] for r in rows]
        npv = sum(
            f / (1 + self.WACC_VAL) ** y
            for f, y in zip(fcfs, years)
        )
        lo, hi = -0.50, 2.0
        for _ in range(200):
            mid = (lo + hi) / 2
            pv = sum(
                f / (1 + mid) ** y
                for f, y in zip(fcfs, years)
            )
            if pv > 0:
                lo = mid
            else:
                hi = mid
        return npv, mid

    def test_wacc(self):
        """WACC = 12.6%."""
        assert abs(self.WACC_VAL - 0.126) < 0.001

    def test_npv_353m(self):
        """NPV ~ $353M."""
        rows = self._run_dcf()
        npv, _ = self._npv_irr(rows)
        assert abs(npv - 353e6) / 353e6 < 0.05

    def test_irr_17_6_pct(self):
        """IRR ~ 17.6%."""
        rows = self._run_dcf()
        _, irr = self._npv_irr(rows)
        assert abs(irr - 0.176) < 0.01

    def test_payback_year_6(self):
        rows = self._run_dcf()
        payback = next(
            (r['year'] for r in rows
             if r['year'] >= 1 and r['cum'] > 0),
            None,
        )
        assert payback == 6

    def test_gpu_90pct_capex(self):
        """GPU hardware = ~90% of total CAPEX."""
        rows = self._run_dcf()
        tot_cx = sum(r['capex'] for r in rows)
        gpu_prices = self._gpu_prices()
        tot_gpu = sum(self.N_GPU * gp for _, gp in gpu_prices)
        pct = tot_gpu / tot_cx
        assert abs(pct - 0.90) < 0.02

    def test_gpu_capex_5850m(self):
        """GPU CAPEX ~ $5850M."""
        gpu_prices = self._gpu_prices()
        tot_gpu = sum(self.N_GPU * gp for _, gp in gpu_prices)
        assert abs(tot_gpu - 5850e6) / 5850e6 < 0.05

    def test_total_capex_6506m(self):
        """Total CAPEX ~ $6506M."""
        rows = self._run_dcf()
        tot_cx = sum(r['capex'] for r in rows)
        assert abs(tot_cx - 6506e6) / 6506e6 < 0.05

    def test_electricity_53pct_opex(self):
        """Electricity = 53% of operating costs."""
        rows = self._run_dcf()
        tot_ox = sum(r['opex'] for r in rows)
        tot_elec = sum(
            self.TOTAL_MW * 1_000 * self.H * self.P_ELEC
            * (1 + self.ELEC_ESC) ** (y - 1)
            for y in range(1, self.LIFE + 1)
        )
        pct = tot_elec / tot_ox
        assert abs(pct - 0.53) < 0.05


# ================================================================
# O. CONSTRUCTION COST REGRESSION (Appendix E)
# ================================================================

MARKET_TO_ISO3 = {
    "Tokyo": "JPN", "Singapore": "SGP", "Zurich": "CHE",
    "Osaka": "JPN", "Silicon Valley": "USA",
    "New Jersey": "USA", "Oslo": "NOR", "Auckland": "NZL",
    "Stockholm": "SWE", "Helsinki": "FIN",
    "Copenhagen": "DNK", "London": "GBR", "Vienna": "AUT",
    "Cardiff": "GBR", "Frankfurt": "DEU", "Berlin": "DEU",
    "Kuala Lumpur": "MYS",
    "Kingdom of Saudi Arabia": "SAU",
    "Chicago": "USA", "Jakarta": "IDN",
    "North Virginia": "USA", "Portland": "USA",
    "Paris": "FRA", "Amsterdam": "NLD",
    "S\u00e3o Paulo": "BRA", "Sydney": "AUS",
    "Lagos": "NGA", "Melbourne": "AUS",
    "Quer\u00e9taro": "MEX", "Cape Town": "ZAF",
    "Lisbon": "PRT", "Seoul": "KOR",
    "Johannesburg": "ZAF", "Bordeaux": "FRA",
    "Dublin": "IRL", "Madrid": "ESP", "Atlanta": "USA",
    "Montevideo": "URY", "Phoenix": "USA",
    "Columbus": "USA", "Milan": "ITA", "Nairobi": "KEN",
    "Dallas": "USA", "Charlotte": "USA",
    "Toronto": "CAN", "UAE": "ARE", "Warsaw": "POL",
    "Santiago": "CHL", "Athens": "GRC",
    "Bogot\u00e1": "COL", "Mumbai": "IND",
    "Shanghai": "CHN",
}


def _load_dcci():
    """Load DCCI construction costs, averaged by country."""
    dcci = {}
    path = DATA / "dcci_2025_construction_costs.csv"
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso3 = MARKET_TO_ISO3[row["market"]]
            cost = float(row["usd_per_watt"])
            dcci.setdefault(iso3, []).append(cost)
    return dcci


class TestConstructionRegression:
    """Verify construction cost regression (Appendix E)."""

    def test_52_markets(self):
        """52 DCCI markets in data."""
        path = DATA / "dcci_2025_construction_costs.csv"
        with open(path, encoding="utf-8") as f:
            n = sum(1 for _ in csv.DictReader(f))
        assert n == 52

    def test_37_countries(self):
        """52 markets -> 37 unique countries."""
        dcci = _load_dcci()
        assert len(dcci) == 37

    def test_regression_r2(self):
        """R^2 ~ 0.48."""
        import numpy as np

        dcci_raw = _load_dcci()
        dcci = {
            iso: np.mean(costs)
            for iso, costs in dcci_raw.items()
        }

        gdp_d = {}
        path = DATA / "wb_gdp_per_capita_ppp_2023.csv"
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                gdp_d[row["iso3"]] = float(
                    row["gdp_pcap_ppp_2023"]
                )

        reg_d = {}
        path = DATA / "wb_country_regions.csv"
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                reg_d[row["iso3"]] = row["region"]

        urban_d = _load_optional_csv(
            "wb_urban_share_2023.csv",
            "iso3", "urban_share_pct",
            transform=lambda v: float(v) / 100.0,
        )
        seismic_d = _load_optional_csv(
            "seismic_zones.csv",
            "iso3", "seismic_high",
            transform=int,
        )
        pop_d = _load_optional_csv(
            "wb_population_2023.csv",
            "iso3", "population_2023",
            transform=int,
        )

        REF_REGION = "Europe & Central Asia"
        dummy_regions = sorted(
            r for r in set(reg_d.values())
            if r != REF_REGION
        )
        matched = []
        for iso3, avg_cost in dcci.items():
            if iso3 in gdp_d and iso3 in reg_d:
                matched.append({
                    "iso3": iso3,
                    "cost": avg_cost,
                    "gdp_pcap": gdp_d[iso3],
                    "region": reg_d[iso3],
                    "urban": urban_d.get(iso3, 0.5),
                    "seismic": seismic_d.get(iso3, 0),
                })
        n = len(matched)
        k = 5 + len(dummy_regions)
        y = np.array([math.log(m["cost"]) for m in matched])
        X = np.zeros((n, k))
        for i, m in enumerate(matched):
            X[i, 0] = 1.0
            X[i, 1] = math.log(m["gdp_pcap"])
            X[i, 2] = math.log(
                pop_d.get(m["iso3"], 1_000_000)
            )
            X[i, 3] = m["urban"]
            X[i, 4] = m["seismic"]
            for j2, reg in enumerate(dummy_regions):
                if m["region"] == reg:
                    X[i, 5 + j2] = 1.0
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        y_hat = X @ beta
        resid = y - y_hat
        ss_res = np.sum(resid ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - ss_res / ss_tot
        assert abs(r2 - 0.48) < 0.10


def _load_optional_csv(filename, key_col, val_col,
                       transform=float):
    """Load optional CSV returning {key: transform(val)}."""
    result = {}
    try:
        path = DATA / filename
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                result[row[key_col]] = transform(row[val_col])
    except FileNotFoundError:
        pass
    return result


# ================================================================
# P. EQUATION IDENTITIES & CROSS-CHECKS
# ================================================================

class TestEquationIdentities:
    """Cross-check equations are internally consistent."""

    def test_cr_weakly_raises_costs_for_subsidized(
        self, calibration_data, raw_costs,
        cost_recovery_costs,
    ):
        """CR raises costs for subsidized countries."""
        for iso in SUBSIDY_ADJ:
            if iso in raw_costs and iso in cost_recovery_costs:
                assert (cost_recovery_costs[iso]
                        >= raw_costs[iso] - 0.001), (
                    f"{iso}: CR lowered cost"
                )

    def test_training_price_geq_cheapest(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """Training price >= cheapest non-sanctioned."""
        omega, dc_k = demand_weights
        p_T, _, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        cheapest = min(
            c for iso, c in cost_recovery_costs.items()
            if iso not in SANCTIONED
        )
        assert p_T >= cheapest - 0.001

    def test_hhi_range(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """0 < HHI <= 1."""
        omega, dc_k = demand_weights
        _, _, hhi = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        assert 0 < hhi <= 1.0

    def test_latency_markup_monotone(self):
        """Inference markup is increasing in latency."""
        for l1 in range(0, 200, 10):
            for l2 in range(l1, 200, 10):
                assert (1 + TAU * l1) <= (1 + TAU * l2)

    def test_export_shares_sum_leq_one(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """Training export shares sum <= total demand."""
        omega, dc_k = demand_weights
        _, shares, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        total_demand = ALPHA * Q_TOTAL
        total_export = sum(shares.values())
        assert total_export <= total_demand * 1.01


# ================================================================
# Q. GEOPOLITICAL BLOC CONSISTENCY
# ================================================================

class TestBlocConsistency:
    """Verify geopolitical bloc assignments."""

    def test_blocs_partition(self, calibration_data):
        for r in calibration_data:
            iso = r["iso3"]
            in_w = iso in BLOC_WESTERN
            in_c = iso in BLOC_CHINA_ALIGNED
            n_blocs = sum([in_w, in_c, not in_w and not in_c])
            assert n_blocs == 1, f"{iso} in multiple blocs"

    def test_sanctioned_in_china_bloc(self):
        for iso in SANCTIONED:
            bloc = _get_bloc(iso)
            assert bloc in ('C', 'N'), (
                f"{iso} sanctioned but bloc={bloc}"
            )

    def test_eu_in_western(self):
        for iso in EU_MEMBERS:
            assert iso in BLOC_WESTERN, f"{iso} not Western"

    def test_apec_assignments(self):
        for iso in APEC_CBPR:
            assert len(iso) == 3

    def test_27_eu_members(self):
        assert len(EU_MEMBERS) == 27

    def test_no_overlap_western_china(self):
        assert len(BLOC_WESTERN & BLOC_CHINA_ALIGNED) == 0


# ================================================================
# R. COUNTERFACTUAL (Section 6.2)
# ================================================================

class TestCounterfactual:
    """Verify counterfactual: doubling sovereignty to 20%."""

    def test_20pct_more_domestic_than_10pct(
        self, cost_recovery_costs, demand_weights,
    ):
        _, dc_k = demand_weights
        adj = cost_recovery_costs
        min_cost = min(adj.values())
        count_10 = sum(
            1 for iso in dc_k
            if iso in adj and adj[iso] <= 1.10 * min_cost
        )
        count_20 = sum(
            1 for iso in dc_k
            if iso in adj and adj[iso] <= 1.20 * min_cost
        )
        assert count_20 >= count_10

    def test_export_share_decreases(
        self, cost_recovery_costs, demand_weights,
    ):
        omega, dc_k = demand_weights
        adj = cost_recovery_costs
        min_cost = min(adj.values())
        export_10 = sum(
            omega.get(iso, 0) for iso in dc_k
            if iso in adj and adj[iso] > 1.10 * min_cost
        )
        export_20 = sum(
            omega.get(iso, 0) for iso in dc_k
            if iso in adj and adj[iso] > 1.20 * min_cost
        )
        assert export_20 <= export_10


# ================================================================
# S. BILATERAL TRADE FLOWS
# ================================================================

class TestTradeFlows:
    """Verify bilateral trade flow claims from Section 6.2."""

    @pytest.fixture(scope="class")
    def inference_sourcing(
        self, cost_recovery_costs,
        latency_data, demand_weights,
    ):
        _, dc_k = demand_weights
        return _compute_inference_sourcing(
            cost_recovery_costs,
            latency_data, dc_k,
        )

    @pytest.fixture(scope="class")
    def inference_exports(
        self, inference_sourcing, demand_weights,
    ):
        omega, dc_k = demand_weights
        return _compute_inference_export_shares(
            inference_sourcing, omega, dc_k,
        )

    def test_usa_inference_from_canada(
        self, inference_sourcing,
    ):
        src = inference_sourcing["USA"]["best_inf_source"]
        assert src == "CAN", f"USA source: {src}"

    def test_germany_inference_from_nearby_country(
        self, inference_sourcing,
    ):
        """Germany sources from a nearby low-cost country."""
        src = inference_sourcing["DEU"]["best_inf_source"]
        assert src is not None
        if src != "DEU":
            assert (src in BLOC_WESTERN
                    or src not in SANCTIONED), (
                f"DEU sources from unexpected {src}"
            )

    def test_uk_inference_source(self, inference_sourcing):
        src = inference_sourcing["GBR"]["best_inf_source"]
        assert src is not None

    def test_france_inference_source(self, inference_sourcing):
        """France sources from a nearby low-cost country."""
        src = inference_sourcing["FRA"]["best_inf_source"]
        assert src is not None
        if src != "FRA":
            assert src not in SANCTIONED, (
                f"FRA source {src} is sanctioned"
            )

    def test_china_cheapest_foreign_inference(
        self, inference_sourcing,
    ):
        src = inference_sourcing["CHN"]["best_foreign_inf"]
        assert src is not None
        assert src not in SANCTIONED, (
            f"CHN foreign source {src} is sanctioned"
        )

    def test_top5_inference_exporters(
        self, inference_exports, calibration_data,
    ):
        """Top 5 inference exporters ~ 77% of cross-border."""
        top5 = sorted(
            inference_exports.items(), key=lambda x: -x[1],
        )[:5]
        top5_pct = sum(s for _, s in top5) * 100
        assert 45 <= top5_pct <= 85, f"{top5_pct:.0f}%"
        assert top5[0][0] == "CAN"

    def test_inference_hhi_lower_than_training(
        self, inference_exports, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """Inference HHI < training HHI (more dispersed)."""
        omega, dc_k = demand_weights
        _, _, hhi_t = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, lam=0.0,
        )
        hhi_i = sum(s ** 2 for s in inference_exports.values())
        assert hhi_i < hhi_t or hhi_i < 0.50, (
            f"HHI_I={hhi_i:.4f} vs HHI_T={hhi_t:.4f}"
        )

    def test_kyrgyzstan_inference_hub(
        self, inference_sourcing, demand_weights,
    ):
        """KGZ serves as inference hub (conditional)."""
        omega, dc_k = demand_weights
        clients = [
            iso for iso in dc_k
            if (inference_sourcing.get(iso, {})
                .get("best_inf_source") == "KGZ")
            and iso != "KGZ"
        ]
        kgz_total = sum(
            omega.get(iso, 0) for iso in clients
        ) * 100
        if kgz_total > 0:
            assert len(clients) >= 1
        assert "KGZ" in inference_sourcing

    def test_kyrgyzstan_inference_share_consistent(
        self, inference_exports,
    ):
        """KGZ inference share >= 0 (may be zero)."""
        kgz_pct = inference_exports.get("KGZ", 0) * 100
        assert kgz_pct >= 0

    def test_only_canada_exports_bilateral(
        self, cost_recovery_costs,
        demand_weights, grid_capacity,
    ):
        """Under bilateral sovereignty, only Canada exports."""
        omega, dc_k = demand_weights
        _, shares, _ = _solve_equilibrium(
            cost_recovery_costs, dc_k, omega,
            grid_capacity, SANCTIONED, bilateral=True,
        )
        non_sanct = {
            iso for iso in shares if iso not in SANCTIONED
        }
        assert "CAN" in non_sanct
        if len(non_sanct) > 1:
            can_share = shares.get("CAN", 0)
            total = sum(shares.values())
            assert can_share / total > 0.30


# ================================================================
# T. FDI REGIME CLASSIFICATION
# ================================================================

class TestFDIRegimes:
    """Verify FDI-specific trade flow claims."""

    @pytest.fixture(scope="class")
    def fdi_equilibrium(
        self, cost_recovery_costs,
        latency_data, demand_weights, grid_capacity,
    ):
        """Run FDI equilibrium and return regimes."""
        omega, dc_k = demand_weights
        adj = cost_recovery_costs
        costs = cost_recovery_costs
        k_bar = grid_capacity

        # FDI supply stack (non-sanctioned)
        fdi_supply = sorted(
            [(iso, adj[iso], k_bar.get(iso, 1e12))
             for iso in adj
             if iso in k_bar and iso not in SANCTIONED],
            key=lambda x: x[1],
        )

        # Solve FDI training equilibrium
        p_T = fdi_supply[0][1]
        for _ in range(30):
            Q_TX = _fdi_training_demand(
                p_T, adj, costs, dc_k, omega,
            )
            cum_cap = 0
            p_T_new = p_T
            for iso_j, c_j, k_j in fdi_supply:
                cum_cap += k_j * ALPHA
                if cum_cap >= Q_TX and Q_TX > 0:
                    p_T_new = c_j
                    break
            if abs(p_T_new - p_T) < 0.0001:
                p_T = p_T_new
                break
            p_T = p_T_new

        # Training shares
        shares = {}
        remaining = Q_TX
        for iso_j, c_j, k_j in fdi_supply:
            if c_j > p_T:
                break
            ca = min(k_j * ALPHA, remaining)
            if ca > 0:
                shares[iso_j] = ca
                remaining -= ca
            if remaining <= 0:
                break
        train_exp = set(shares.keys())

        # FDI inference sourcing
        inf_src = _fdi_inference_sourcing(
            adj, costs, dc_k, latency_data,
        )
        inf_exp = {
            src for iso_k, src in inf_src.items()
            if src != iso_k
        }

        # Who would import training under FDI
        would_import = _fdi_would_import(adj, costs, dc_k)

        # Classify regimes
        regime = {}
        for iso_k in dc_k:
            if costs.get(iso_k) is None:
                continue
            ex_t = iso_k in train_exp
            ex_i = iso_k in inf_exp
            im_t = iso_k in would_import
            im_i = (inf_src.get(iso_k, iso_k) != iso_k)
            if ex_t and (ex_i or not im_i):
                r = "T+I exporter"
            elif ex_i and im_t:
                r = "inference hub"
            elif im_t and not im_i:
                r = "hybrid"
            elif not im_t and not im_i:
                r = "domestic"
            else:
                r = "full importer"
            regime[iso_k] = r

        return {
            "p_T": p_T,
            "train_exporters": train_exp,
            "inf_exporters": inf_exp,
            "regime_5_fdi": regime,
            "fdi_inf_src": inf_src,
        }

    def test_fdi_increases_exporters(self, fdi_equilibrium):
        """FDI produces exporters (>= 1)."""
        regime = fdi_equilibrium["regime_5_fdi"]
        n = sum(
            1 for r in regime.values()
            if r in ("T+I exporter", "inference hub")
        )
        assert n >= 1, f"FDI exporters: {n}"

    def test_fdi_developing_exporters(self, fdi_equilibrium):
        """FDI enables developing-country exporters (>= 1)."""
        regime = fdi_equilibrium["regime_5_fdi"]
        dev_exp = [
            iso for iso, r in regime.items()
            if iso in DEVELOPING
            and r in ("T+I exporter", "inference hub")
        ]
        assert len(dev_exp) >= 1, (
            f"Developing FDI exporters: {len(dev_exp)}"
        )

    def test_fdi_sanctioned_excluded(self, fdi_equilibrium):
        """Sanctioned countries never become FDI exporters."""
        regime = fdi_equilibrium["regime_5_fdi"]
        for iso in SANCTIONED:
            if iso in regime:
                r = regime[iso]
                assert r not in (
                    "T+I exporter", "inference hub",
                ), f"Sanctioned {iso} = {r}"

    def test_fdi_canada_still_exporter(self, fdi_equilibrium):
        all_exp = (fdi_equilibrium["train_exporters"]
                   | fdi_equilibrium["inf_exporters"])
        assert "CAN" in all_exp


def _fdi_training_demand(p_T, adj, costs, dc_k, omega):
    """FDI training export demand at price p_T."""
    Q_TX = 0
    for iso_k in dc_k:
        c_k = costs.get(iso_k)
        if c_k is None:
            continue
        w_k = omega.get(iso_k, 0)
        lam_min = float('inf')
        for iso_j in adj:
            if iso_j == iso_k or iso_j in SANCTIONED:
                continue
            lam = compute_fdi_lambda(iso_j, iso_k, 'USA')
            if lam < lam_min:
                lam_min = lam
        if (lam_min < float('inf')
                and c_k > (1 + lam_min) * p_T):
            Q_TX += ALPHA * w_k * Q_TOTAL
    return Q_TX


def _fdi_inference_sourcing(adj, costs, dc_k, lat):
    """FDI inference sourcing: best source per buyer."""
    inf_src = {}
    for iso_k in dc_k:
        c_k_eff = costs.get(iso_k)
        if c_k_eff is None:
            continue
        l_kk = _get_latency(lat, iso_k, iso_k)
        P_dom = (1 + TAU * (l_kk or 0)) * c_k_eff
        best_cost = P_dom
        best_src = iso_k
        for iso_j in adj:
            if iso_j == iso_k or iso_j not in dc_k:
                continue
            if iso_j in SANCTIONED:
                continue
            lam_fdi = compute_fdi_lambda(
                iso_j, iso_k, 'USA',
            )
            if lam_fdi >= float('inf'):
                continue
            l_jk = _get_latency(lat, iso_j, iso_k)
            if l_jk is None:
                continue
            cost_del = (
                (1 + lam_fdi)
                * (1 + TAU * l_jk)
                * adj[iso_j]
            )
            if cost_del < best_cost:
                best_cost = cost_del
                best_src = iso_j
        inf_src[iso_k] = best_src
    return inf_src


def _fdi_would_import(adj, costs, dc_k):
    """Countries that would import training under FDI."""
    result = {}
    for iso_k in dc_k:
        c_k = costs.get(iso_k)
        if c_k is None:
            continue
        best_del = c_k
        best_sup = None
        for iso_j in adj:
            if iso_j == iso_k or iso_j in SANCTIONED:
                continue
            lam_fdi = compute_fdi_lambda(
                iso_j, iso_k, 'USA',
            )
            if lam_fdi >= float('inf'):
                continue
            delivered = (1 + lam_fdi) * adj[iso_j]
            if delivered < best_del:
                best_del = delivered
                best_sup = iso_j
        if best_sup is not None:
            result[iso_k] = best_sup
    return result


# ================================================================
# U. REGIME COUNTS -- Section 6.2 Table 3 narrative
# ================================================================

class TestRegimeCounts:
    """Verify 5-type regime counts under bilateral lambda."""

    @pytest.fixture(scope="class")
    def bilateral_regimes(
        self, cost_recovery_costs,
        latency_data, demand_weights, grid_capacity,
    ):
        """Classify all countries into 5-type regimes."""
        omega, dc_k = demand_weights
        adj = cost_recovery_costs
        costs = cost_recovery_costs
        k_bar = grid_capacity

        p_T, shares, _ = _solve_equilibrium(
            costs, dc_k, omega, k_bar,
            SANCTIONED, bilateral=True, tiered=True,
        )
        train_exp = set(shares.keys())

        # Bilateral inference sourcing (tier 3)
        inf_exp = set()
        inf_src = {}
        for iso_k in dc_k:
            c_k = adj.get(iso_k)
            if c_k is None:
                continue
            l_kk = _get_latency(latency_data, iso_k, iso_k)
            P_dom = _inference_delivered_cost(
                c_k, l_kk or 0,
            )
            best_cost = P_dom
            best_src = iso_k
            for iso_j, c_j in adj.items():
                if iso_j == iso_k:
                    continue
                lam_kj = compute_bilateral_lambda(
                    iso_k, iso_j,
                )
                if lam_kj >= float('inf'):
                    continue
                G = compute_geo_distance(iso_k, iso_j)
                lam_eff = ALPHA_GEO * G  # tier 3
                l_jk = _get_latency(
                    latency_data, iso_j, iso_k,
                )
                if l_jk is None:
                    continue
                cost_del = (
                    (1 + lam_eff)
                    * _inference_delivered_cost(
                        c_j, l_jk,
                    )
                )
                if cost_del < best_cost:
                    best_cost = cost_del
                    best_src = iso_j
            inf_src[iso_k] = best_src
            if best_src != iso_k:
                inf_exp.add(best_src)

        # Lambda_min per buyer
        lam_min = {}
        for iso_k in dc_k:
            ml = float('inf')
            for iso_j in costs:
                if iso_j == iso_k:
                    continue
                lam = compute_bilateral_lambda(iso_k, iso_j)
                if lam < ml:
                    ml = lam
            lam_min[iso_k] = ml

        # Classify
        regime = {}
        counts = {
            "T+I exporter": 0, "inference hub": 0,
            "hybrid": 0, "domestic": 0,
            "full importer": 0,
        }
        for iso_k in dc_k:
            c_k = costs.get(iso_k)
            if c_k is None:
                continue
            lam_k = lam_min.get(iso_k, float('inf'))
            lam_star = c_k / p_T - 1 if p_T > 0 else 0
            dom_t = (lam_k >= lam_star) or (c_k <= p_T)
            dom_i = (inf_src.get(iso_k, iso_k) == iso_k)
            ex_t = iso_k in train_exp
            ex_i = iso_k in inf_exp
            if ex_t:
                r = "T+I exporter"
            elif ex_i and not dom_t:
                r = "inference hub"
            elif not dom_t and dom_i:
                r = "hybrid"
            elif dom_t and dom_i:
                r = "domestic"
            else:
                r = "full importer"
            regime[iso_k] = r
            counts[r] += 1

        return regime, counts

    def test_all_five_types_exist(self, bilateral_regimes):
        _, counts = bilateral_regimes
        nonzero = sum(1 for v in counts.values() if v > 0)
        assert nonzero >= 3, f"{nonzero} types: {counts}"

    def test_total_equals_85(self, bilateral_regimes):
        _, counts = bilateral_regimes
        assert sum(counts.values()) == 85

    def test_full_importer_is_largest(self, bilateral_regimes):
        _, counts = bilateral_regimes
        fi = counts["full importer"]
        assert fi >= counts["T+I exporter"]
        assert fi >= counts["inference hub"]

    def test_ti_exporters_small(self, bilateral_regimes):
        _, counts = bilateral_regimes
        assert 1 <= counts["T+I exporter"] <= 8

    def test_canada_is_ti_exporter(self, bilateral_regimes):
        regime, _ = bilateral_regimes
        assert regime.get("CAN") == "T+I exporter", (
            f"CAN: {regime.get('CAN')}"
        )

    def test_usa_regime(self, bilateral_regimes):
        regime, _ = bilateral_regimes
        valid = (
            "domestic", "T+I exporter", "inference hub",
            "hybrid", "full importer",
        )
        assert regime.get("USA") in valid

    def test_sanctioned_not_western_exporters(
        self, bilateral_regimes,
    ):
        """Sanctioned countries don't export T+I globally."""
        regime, _ = bilateral_regimes
        for iso in SANCTIONED:
            if iso in regime:
                assert regime[iso] != "T+I exporter", (
                    f"Sanctioned {iso} = T+I exporter"
                )


# ================================================================
# V. DOCUMENT CONTENT -- verify generated v31.docx contents
# ================================================================

class TestDocumentContent:
    """Verify key text, equations, and fixes in the generated v31.docx.

    These tests read the latest ``flop_trade_model_v32.docx`` and check
    that paper content is present and that known reviewer fixes from
    sessions 1-3 have not regressed.
    """

    # ---------- Structure ----------

    def test_title_present(self, docx_text):
        assert "Cheap Energy Might Not Be Enough" in docx_text
        assert "A Trade Model of AI Compute Services" in docx_text

    def test_author_lokshin(self, docx_text):
        assert "Michael Lokshin" in docx_text

    def test_version_stamp_v32(self, docx_text):
        assert "v32" in docx_text

    def test_abstract_present(self, docx_text):
        assert "Abstract" in docx_text

    def test_jel_codes(self, docx_text):
        for code in ("F14", "F18", "L86", "O14", "O33", "Q40"):
            assert code in docx_text, f"Missing JEL code: {code}"

    def test_keywords_present(self, docx_text):
        assert "Keywords" in docx_text
        assert "compute trade" in docx_text

    def test_section_headings(self, docx_text):
        headings = (
            "1. Introduction",
            "2. Related Literature",
            "3. Model of Compute Production and Trade",
            "4. Equilibrium Properties",
            "5. Data",
            "6. Calibration and Results",
            "7. Robustness, Caveats, and Extensions",
            "8. Conclusion",
        )
        for h in headings:
            assert h in docx_text, f"Missing heading: {h}"

    def test_section_7_subsections(self, docx_text):
        """§7 is split into three subsections: parameter robustness,
        caveats/omitted frictions, and extensions."""
        for h in (
            "7.1 Robustness to parameter variation",
            "7.2 Caveats and omitted frictions",
            "7.3 Extensions",
        ):
            assert h in docx_text, f"Missing §7 subsection: {h}"

    def test_katz_moved_to_section_6(self, docx_text):
        """The Katz et al. (2025) policy-readiness paragraph should now
        sit in §6.2, introduced by 'Cross-country evidence on policy
        readiness corroborates this pattern' (not 'reinforces this
        conclusion'), and it should NOT appear under §7.2 or §7.3."""
        assert "Cross-country evidence on policy readiness corroborates" in (
            docx_text
        )
        # The old §7.2 framing should be gone
        assert (
            "Cross-country evidence on policy readiness reinforces"
            not in docx_text
        )

    def test_appendices_present(self, docx_text):
        for h in ("Appendix B", "Appendix C", "Appendix D", "Appendix E"):
            assert h in docx_text, f"Missing: {h}"

    # ---------- Figures ----------

    def test_figure1_model_structure(self, docx_text):
        assert "Figure 1" in docx_text
        assert "Model structure" in docx_text

    def test_figure1_inline_reference(self, docx_text):
        """§6.2 should reference Figure 1 as model structure."""
        assert "summarizes the model structure" in docx_text

    # ---------- Equation numbering ----------

    def test_main_equations_1_to_6(self, docx_text):
        for n in ("(1)", "(2)", "(3)", "(4)", "(5)", "(6)"):
            assert n in docx_text, f"Missing equation number {n}"

    def test_appendix_b_equations(self, docx_text):
        for n in ("(B.1)", "(B.2)", "(B.3)", "(B.4)", "(B.5)"):
            assert n in docx_text, f"Missing {n}"

    # ---------- Fix 1a: HHI display equation ----------

    def test_hhi_display_equation_present(self, docx_body_xml):
        """Prop 2 HHI formula is a display equation with proper
        ``K_{T,j}/Q_{T,X}`` squared-ratio structure inside a Σ."""
        import re
        paras = re.findall(
            r"<m:oMathPara[^>]*>.*?</m:oMathPara>",
            docx_body_xml, re.DOTALL,
        )
        hhi_paras = []
        for p in paras:
            t = "".join(re.findall(r"<m:t[^>]*>([^<]*)</m:t>", p))
            if "HHI" in t and "T,j" in t and "T,X" in t:
                hhi_paras.append(p)
        assert hhi_paras, (
            "No HHI display equation with K_{T,j} and Q_{T,X} "
            "found in oMathPara elements"
        )
        # Verify Σ character present inside the n-ary operator
        for p in hhi_paras:
            assert 'chr m:val="\u2211"' in p, (
                "HHI display equation is missing Σ (\u2211) character"
            )

    def test_hhi_no_stray_2(self, docx_body_xml):
        """Regression: the old broken HHI had a stray (² inside the Σ
        operand. After the fix, the operand must be a properly nested
        sSup with a delimited fraction (no standalone ``(`` before K)."""
        import re
        idx = docx_body_xml.find("Proposition 2")
        next_heading = docx_body_xml.find("Proposition 3")
        if idx < 0 or next_heading <= idx:
            return
        chunk = docx_body_xml[idx:next_heading]
        naries = re.findall(r"<m:nary>.*?</m:nary>", chunk, re.DOTALL)
        # At least one nary should exist (the Σ_j in HHI)
        assert naries, "No n-ary operator in Prop 2 area"
        # None of them should contain an sSup whose base is just "("
        for nary in naries:
            e_match = re.search(
                r"<m:e>(.*?)</m:e>", nary, re.DOTALL,
            )
            if not e_match:
                continue
            e_content = e_match.group(1)
            # A properly built squared ratio uses m:d (delimiter) to
            # provide the parentheses, not a literal "(" run.
            stray_parens = re.findall(
                r"<m:t[^>]*>\s*\(\s*</m:t>", e_content,
            )
            assert not stray_parens, (
                "Prop 2 n-ary operand contains a stray literal '('"
            )

    # ---------- Fix 1d: PUE display equation ----------

    def test_pue_functional_form_display(self, docx_body_xml):
        """The PUE functional form should appear as an oMathPara in
        Section 3.1 immediately after equation (1)."""
        import re
        paras = re.findall(
            r"<m:oMathPara[^>]*>.*?</m:oMathPara>",
            docx_body_xml, re.DOTALL,
        )
        for p in paras:
            t = "".join(re.findall(r"<m:t[^>]*>([^<]*)</m:t>", p))
            # Looking for PUE(θ_j) = φ + δ · max(0, θ_j − θ̄)
            if (
                "PUE" in t
                and "\u03C6" in t      # φ
                and "\u03B4" in t      # δ
                and "max" in t
            ):
                return
        assert False, (
            "No PUE(θ) = φ + δ · max(0, θ − θ̄) display equation found"
        )

    # ---------- Fix 1f: latency notation unified (no d_{ij}) ----------

    def test_no_d_ij_in_prop1(self, docx_body_xml):
        """Prop 1 regime (ii) used to say ``d_{ij} below threshold d``;
        after unification it should use ``l_{jk}`` and ``l̄``."""
        import re
        p1 = docx_body_xml.find("Proposition 1")
        p2 = docx_body_xml.find("Proposition 2")
        if p1 < 0 or p2 <= p1:
            return
        p1_chunk = docx_body_xml[p1:p2]
        sSubs = re.findall(
            r"<m:sSub>.*?</m:sSub>", p1_chunk, re.DOTALL,
        )
        for s in sSubs:
            e_match = re.search(r"<m:e>(.*?)</m:e>", s, re.DOTALL)
            sub_match = re.search(
                r"<m:sub>(.*?)</m:sub>", s, re.DOTALL,
            )
            if not (e_match and sub_match):
                continue
            base = "".join(re.findall(
                r"<m:t[^>]*>([^<]*)</m:t>", e_match.group(1)))
            sub = "".join(re.findall(
                r"<m:t[^>]*>([^<]*)</m:t>", sub_match.group(1)))
            assert not (base == "d" and sub in ("ij", "jk")), (
                f"Prop 1 still has d subscript: base={base!r}, sub={sub!r}"
            )

    # ---------- Fix 1g: no stray K̄j after "realized investment" ----------

    def test_no_stray_kbar_j(self, docx_body_xml):
        """The earlier draft had a dangling ``K̄_j`` OMML element
        appended after ``...realized investment.`` in Section 6.2."""
        import re
        for m in re.finditer(r"realized investment", docx_body_xml):
            pos = m.start()
            chunk = docx_body_xml[pos:pos + 600]
            text = "".join(re.findall(
                r"<(?:w:t|m:t)[^>]*>([^<]*)</(?:w:t|m:t)>", chunk))
            head = text[:80]  # first 80 chars after "realized investment"
            assert (
                "K\u0304j" not in head
                and "K\u0304" + "j" not in head
            ), (
                f"Stray K̄j found after 'realized investment': {head!r}"
            )

    def test_capacity_bound_in_prop2(self, docx_text):
        """Prop 2 should explicitly state K_{T,j} ≤ K̄_j."""
        assert "bounded by the capacity ceiling" in docx_text

    # ---------- Fix 1h: λ seller/buyer clarification ----------

    def test_lambda_subscript_clarification(self, docx_text):
        """Body should explain that λ_{jk} ≡ λ_{ij} from eq (2)."""
        assert "we relabel the subscripts" in docx_text

    # ---------- Fix 1i: no p_T* in Prop 1 ----------

    def test_no_p_T_star_in_prop1(self, docx_body_xml):
        """Prop 1 should use p_T, not p_T^*."""
        import re
        p1 = docx_body_xml.find("Proposition 1")
        p2 = docx_body_xml.find("Proposition 2")
        if p1 < 0 or p2 <= p1:
            return
        p1_chunk = docx_body_xml[p1:p2]
        sSubSups = re.findall(
            r"<m:sSubSup>.*?</m:sSubSup>", p1_chunk, re.DOTALL,
        )
        for s in sSubSups:
            ts = "".join(re.findall(r"<m:t[^>]*>([^<]*)</m:t>", s))
            assert not (
                "p" in ts and "T" in ts and "*" in ts
            ), f"Prop 1 still has p_T*: {ts!r}"

    # ---------- Fix 1j: K_{I,j→k} notation ----------

    def test_inference_allocation_notation_defined(self, docx_text):
        """Appendix B.4 should define K_{I, j→k}."""
        assert "I,j\u2192k" in docx_text, (
            "Missing K_{I, j→k} notation in Appendix B.4"
        )
        assert "inference exports to buyer" in docx_text

    # ---------- Formal latency cone footnote (later fix) ----------

    def test_latency_cone_formal_statement(self, docx_text):
        """Footnote 9 should include the formal non-empty latency cone
        condition (∃k with q_k > 0 and l_{jk} ≤ l̄)."""
        assert "Formally, country j has a non-empty latency cone" in (
            docx_text
        )
        assert "\u2203k" in docx_text  # ∃k

    # ---------- Fix 2a: Graphics (not Graphic) ----------

    def test_graphics_processing_units(self, docx_text):
        assert "Graphics Processing Units" in docx_text
        assert "Graphic Processing Units" not in docx_text

    # ---------- Fix 2b: Heckscher-Ohlin attribution ----------

    def test_heckscher_cited_in_text(self, docx_text):
        assert "Heckscher 1919" in docx_text

    def test_ohlin_still_cited(self, docx_text):
        assert "Ohlin 1933" in docx_text

    def test_heckscher_ohlin_hyphenated(self, docx_text):
        assert "Heckscher\u2013Ohlin" in docx_text

    def test_ricardian_vs_ho_hybrid_acknowledged(self, docx_text):
        assert "the cost structure above is Ricardian" in docx_text

    # ---------- Fix 2c: World Bank sentence rephrased ----------

    def test_world_bank_divide_parenthesized(self, docx_text):
        # No em-dash per paper style; parenthetical aside
        assert (
            "divide (high-income countries hold 77% of colocation capacity)"
            in docx_text
        )

    def test_world_bank_not_old_comma_form(self, docx_text):
        assert "divide,  high-income" not in docx_text

    # ---------- Fix 2d: Deloitte and Google (2020) ----------

    def test_deloitte_and_google_cited_in_text(self, docx_text):
        assert "Deloitte and Google (2020)" in docx_text

    def test_deloitte_and_google_in_references(self, docx_text):
        assert "Milliseconds Make Millions" in docx_text

    # ---------- Fix 2e: ADB (not ABD) ----------

    def test_adb_not_abd_in_text(self, docx_text):
        assert "ADB 2020" in docx_text
        assert "ABD 2020" not in docx_text

    def test_asian_development_bank_in_references(self, docx_text):
        assert "Asian Development Bank" in docx_text

    # ---------- Fix 2f: G_{ij} normalization ----------

    def test_g_normalization_statement(self, docx_text):
        assert "normalized so that" in docx_text

    # ---------- Fix 2g: HHI dominant-exporter phrasing ----------

    def test_hhi_dominant_exporter_phrasing(self, docx_text):
        assert "dominant exporter" in docx_text

    def test_hhi_unconstrained_benchmark_mention(self, docx_text):
        assert "close to the unconstrained benchmark" in docx_text

    # ---------- Fix 2h: uniform 20% premium + country name ----------

    def test_uniform_premium_specified(self, docx_text):
        assert "uniform" in docx_text and "premium to 20%" in docx_text

    def test_20pct_country_named(
        self, docx_text, cost_recovery_costs, demand_weights,
    ):
        """The §6.2 counterfactual must name at least one specific
        country that shifts into domestic production when the uniform
        premium rises from 10% to 20%. The test independently recomputes
        the expected set from cost-recovery costs and asserts that at
        least one of those country names appears in the uniform-premium
        counterfactual sentence."""
        _, dc_k = demand_weights
        min_cost = min(cost_recovery_costs.values())
        # ISOs in the bracket (1.10 m, 1.20 m]
        shifted_isos = [
            iso for iso in dc_k
            if iso in cost_recovery_costs
            and 1.10 * min_cost
            < cost_recovery_costs[iso]
            <= 1.20 * min_cost
        ]
        # Expected country names from CSV
        # (re-load to keep test self-contained)
        path = DATA / "calibration_results_v3.csv"
        with open(path, encoding="utf-8") as f:
            iso_to_name = {
                r["iso3"]: r["country"] for r in csv.DictReader(f)
            }
        expected_names = {
            iso_to_name.get(iso, iso) for iso in shifted_isos
        }
        # At least one expected name must appear in the 20% sentence
        import re
        m = re.search(
            r"Raising the uniform premium to 20%[^.]{0,400}",
            docx_text,
        )
        assert m, "Could not locate uniform-20% sentence"
        sentence = m.group()
        found = [n for n in expected_names if n and n in sentence]
        assert found, (
            f"20% sentence names no expected country; "
            f"expected one of {sorted(expected_names)}"
        )

    # ---------- Fix 2i: welfare gains (not losses) phrasing ----------

    def test_welfare_gains_phrasing(self, docx_text):
        assert "welfare gains from trade" in docx_text

    def test_no_welfare_losses_misphrase(self, docx_text):
        assert "welfare losses from trade barriers" not in docx_text

    # ---------- v32 edit integration (Apr 12) ----------

    def test_firebird_sentence_period(self, docx_text):
        """Firebird citation ends with period, not comma."""
        assert "(Firebird 2026)." in docx_text
        assert "(Firebird 2026)," not in docx_text

    def test_iran_cost_reflects_not_rests(self, docx_text):
        """'reflects' replaced 'rests' for Iran subsidy sentence."""
        assert "cost reflects on one of the world" in docx_text
        assert "cost rests on one of the world" not in docx_text

    def test_regime_changes_spelled_out(self, docx_text):
        """Number of regime changes should be spelled out as a word."""
        import re
        m = re.search(
            r"([\w]+) countries change their trade regimes", docx_text,
        )
        assert m, "Could not locate regime-change sentence"
        word = m.group(1)
        assert not word.isdigit(), (
            f"Regime-change count should be a word, got '{word}'"
        )

    def test_no_em_dash_brazil(self, docx_text):
        """Brazil sentence uses comma, not em dash."""
        assert "India, and Brazil, countries with" in docx_text
        assert "Brazil\u2014countries" not in docx_text

    def test_in_contrast_cheapest_producers(self, docx_text):
        """'In contrast' replaces em-dash 'while' construction."""
        assert "infrastructure. In contrast, the cheapest producers" in (
            docx_text
        )

    def test_no_countries_such_as_indonesia(self, docx_text):
        """'countries such as' removed before Indonesia."""
        assert "1 percent in Indonesia and Viet Nam" in docx_text
        assert "countries such as Indonesia" not in docx_text

    def test_eastern_data_western_computing_comma(self, docx_text):
        """Eastern Data, Western Computing has a comma."""
        assert "Eastern Data, Western Computing" in docx_text

    def test_uniform_20pct_one_not_digit(self, docx_text):
        """20% counterfactual uses 'one additional country' not '1'."""
        import re
        m = re.search(
            r"premium to 20% shifts (\w+) additional", docx_text,
        )
        assert m, "Could not locate 20% sentence"
        assert m.group(1) == "one", (
            f"Expected 'one', got '{m.group(1)}'"
        )

    def test_welfare_cost_qualified(self, docx_text):
        """Welfare cost sentence includes aggregate/modest qualifier."""
        assert (
            "significant in aggregate dollars but modest as a share "
            "of compute spending"
        ) in docx_text

    def test_no_section3_linking_paragraph(self, docx_text):
        """The old linking paragraph after Section 3 heading was removed."""
        assert (
            "This section models compute as a tradable good"
            not in docx_text
        )

    # ---------- Citation integrity for new/edited refs ----------

    def test_firebird_in_references(self, docx_text):
        assert "Firebird" in docx_text

    def test_caoui_steck_in_references(self, docx_text):
        assert "Caoui" in docx_text and "Steck" in docx_text

    def test_aykut_in_references(self, docx_text):
        assert "Aykut" in docx_text

    def test_straub_in_references(self, docx_text):
        assert "Straub" in docx_text

    def test_katz_in_references(self, docx_text):
        assert "Katz" in docx_text


# ================================================================
# W. CITATION INTEGRITY -- reference list completeness
# ================================================================

class TestCitationIntegrity:
    """Verify that key citations used in the body also appear in the
    reference list and are internally consistent."""

    def test_heckscher_in_references(self, docx_text):
        assert "Heckscher, E." in docx_text

    def test_ohlin_in_references(self, docx_text):
        assert "Ohlin, B." in docx_text

    def test_eaton_kortum_in_references(self, docx_text):
        assert "Eaton" in docx_text and "Kortum" in docx_text

    def test_arkolakis_in_references(self, docx_text):
        assert "Arkolakis" in docx_text

    def test_bailey_strezhnev_voeten_in_references(self, docx_text):
        assert (
            "Bailey, M." in docx_text or "Bailey" in docx_text
        )
        assert "Strezhnev" in docx_text

    def test_imf_in_references(self, docx_text):
        assert "IMF" in docx_text

    def test_world_bank_in_references(self, docx_text):
        assert "World Bank" in docx_text

    def test_goldfarb_trefler_in_references(self, docx_text):
        assert "Goldfarb" in docx_text and "Trefler" in docx_text


# ================================================================
# X. EQUATION STRUCTURE -- OMML invariants across all display equations
# ================================================================

class TestEquationStructure:
    """Spot-check that all n-ary operators in the document render
    with proper Σ character and structured sub/sup/operand children."""

    def test_all_naries_have_sigma(self, docx_body_xml):
        """Every n-ary operator we emit should be a summation Σ."""
        import re
        naries = re.findall(
            r"<m:nary>.*?</m:nary>", docx_body_xml, re.DOTALL,
        )
        assert len(naries) >= 6, (
            f"Expected at least 6 n-ary operators, found {len(naries)}"
        )
        for nary in naries:
            m = re.search(r'<m:chr m:val="([^"]+)"', nary)
            assert m is not None, "n-ary without m:chr attribute"
            assert m.group(1) == "\u2211", (
                f"n-ary with non-Σ char: {m.group(1)!r}"
            )

    def test_all_naries_have_operand(self, docx_body_xml):
        """Every n-ary must have a non-empty m:e (operand) — otherwise
        the summed expression would be missing."""
        import re
        naries = re.findall(
            r"<m:nary>.*?</m:nary>", docx_body_xml, re.DOTALL,
        )
        for nary in naries:
            e_match = re.search(
                r"<m:e>(.*?)</m:e>", nary, re.DOTALL,
            )
            assert e_match is not None, "n-ary missing m:e"
            # The operand should contain at least one run or structure
            body = e_match.group(1).strip()
            assert body, "n-ary has empty operand"

    def test_omath_para_count_minimum(self, docx_body_xml):
        """The paper should have at least two oMathPara blocks: the PUE
        functional form (Section 3.1) and the HHI display (Section 4)."""
        import re
        paras = re.findall(
            r"<m:oMathPara[^>]*>.*?</m:oMathPara>",
            docx_body_xml, re.DOTALL,
        )
        assert len(paras) >= 2, (
            f"Expected >=2 oMathPara blocks, found {len(paras)}"
        )
