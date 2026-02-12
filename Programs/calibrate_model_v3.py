"""
Calibrate the FLOP trade model v3 — fixes construction cost bug, adds countries.

Changes from v2:
  - Construction cost formula: GPU_TDP_KW * 1000 * p_L (convert kW→W for $/W data)
  - Additional countries beyond ECA (SAU, KEN, MAR, MYS, IDN, ZAF, MEX, CHL, THA, EGY, NGA, PAK)
  - Outputs v3 CSVs

Model:
  c_j = PUE(θ_j) · γ · p_{E,j} + ρ + γ · 1000 · p_{L,j} / (D · H)
  Training:  P_T(j,k) = c_j  (latency = 0)
  Inference: P_I(j,k) = (1 + τ · l_jk) · c_j
  With sovereignty: multiply foreign by (1 + λ)
"""

import csv
import pathlib
import sys
import io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA = pathlib.Path(r"F:\onedrive\__documents\papers\FLOPsExport\Data")
OUT = DATA

# ═══════════════════════════════════════════════════════════════════════
# STRUCTURAL PARAMETERS
# ═══════════════════════════════════════════════════════════════════════

# GPU hardware
GPU_TDP_KW = 0.700       # kW (700 watts)
GPU_TDP_W = GPU_TDP_KW * 1000  # = 700 watts
GPU_PRICE = 25_000
GPU_LIFE_YR = 3
GPU_UTIL = 0.90
GPU_HOURS = GPU_LIFE_YR * 365.25 * 24 * GPU_UTIL
R_HARDWARE = GPU_PRICE / GPU_HOURS  # $/GPU-hr

# PUE model
PUE_BASE = 1.08
PUE_SLOPE = 0.015
THETA_REF = 15.0

# DC construction
DC_LIFE_YR = 15

# Latency degradation (1/ms)
TAU = 0.0008

# Fixed costs and sovereignty
LAMBDA = 0.10        # 10% sovereignty premium

DOMESTIC_LATENCY_DEFAULT = 5.0  # ms

print("=" * 70)
print("STRUCTURAL PARAMETERS (v3 — construction cost fix)")
print("=" * 70)
print(f"  GPU: H100, {GPU_TDP_W:.0f}W TDP, ${GPU_PRICE:,}, "
      f"{GPU_LIFE_YR}yr life, {GPU_UTIL:.0%} util")
print(f"  Hardware cost (ρ): ${R_HARDWARE:.4f}/GPU-hr")
print(f"  PUE model: {PUE_BASE} + {PUE_SLOPE} × max(0, θ − {THETA_REF})")
print(f"  DC lifetime: {DC_LIFE_YR} years")
print("  Construction: GPU_TDP_W × p_L / (DC_LIFE × H)")
print("  Training: P_T(j,k) = c_j  (latency = 0)")
print("  Inference: P_I(j,k) = (1 + τ · l_jk) · c_j")
print(f"  τ = {TAU}/ms")
print(f"  Sovereignty premium λ = {LAMBDA:.0%}")

# ═══════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════

print("\nLoading data...")

# Electricity prices
electricity = {}
elec_source = {}
with open(DATA / "country_electricity_prices.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        electricity[row["iso3"]] = float(row["price_usd_kwh"])
        elec_source[row["iso3"]] = row.get("source", "")

# Additional countries (industrial electricity prices from public sources)
additional_elec = {
    "SAU": (0.053, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "KEN": (0.088, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "MAR": (0.108, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "MYS": (0.099, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "IDN": (0.067, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "ZAF": (0.040, "Climatescope/BloombergNEF 2025, Eskom Megaflex avg"),
    "MEX": (0.095, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "CHL": (0.130, "Statista/Climatescope 2025, industrial Jan 2024"),
    "THA": (0.108, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "EGY": (0.038, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "NGA": (0.042, "Climatescope/BloombergNEF 2025, weighted avg industrial"),
    "PAK": (0.134, "Climatescope/BloombergNEF 2025, industrial 2024"),
    "ARG": (0.060, "CAMMESA Argentina 2024, large industrial avg"),
    "COL": (0.075, "XM Colombia 2024, industrial non-regulated"),
    "NZL": (0.095, "MBIE New Zealand 2024, industrial avg"),
    "ISR": (0.108, "IEC Israel 2024, general industrial TOU"),
    "VNM": (0.073, "EVN Vietnam 2024, industrial peak/off-peak avg"),
    "PHL": (0.115, "MERALCO Philippines 2024, industrial"),
    "IRN": (0.005, "TAVANIR Iran 2024, heavily subsidized industrial"),
    "DZA": (0.033, "Sonelgaz Algeria 2024, subsidized industrial"),
    "QAT": (0.036, "Kahramaa Qatar 2024, industrial tariff"),
    "TWN": (0.094, "Taipower Taiwan 2024, industrial avg"),
    "ETH": (0.030, "EEU Ethiopia 2024, industrial tariff, hydro-dominated"),
    "GHA": (0.120, "ECG Ghana 2024, industrial tariff"),
    "SEN": (0.180, "Senelec Senegal 2024, industrial tariff"),
}

for iso3, (price, source) in additional_elec.items():
    if iso3 not in electricity:
        electricity[iso3] = price
        elec_source[iso3] = source

print(f"  Electricity: {len(electricity)} countries")

# Temperature
temperature = {}
with open(DATA / "country_temperatures.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        temperature[row["iso3"]] = {
            "country": row["country"],
            "theta_summer": float(row["temp_summer_peak_C"]),
        }

# Construction costs
construction = {}
cost_source = {}
with open(DATA / "predicted_construction_costs.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        iso3 = row["iso3"]
        actual = row.get("actual_usd_per_watt", "")
        predicted = row.get("predicted_usd_per_watt", "")
        if actual and actual.strip():
            construction[iso3] = float(actual)
            cost_source[iso3] = "DCCI"
        elif predicted and predicted.strip():
            construction[iso3] = float(predicted)
            cost_source[iso3] = "predicted"

# Latency
latency = {}
with open(DATA / "country_pair_latency.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        key = (row["iso3_from"], row["iso3_to"])
        latency[key] = float(row["avg_ms"])

# ═══════════════════════════════════════════════════════════════════════
# COMPUTE c_j FOR EACH COUNTRY
# ═══════════════════════════════════════════════════════════════════════

calibration_set = set(electricity.keys()) & set(temperature.keys()) & set(construction.keys())
print(f"Calibration set: {len(calibration_set)} countries")

results = {}
names = {}
H_YR = 365.25 * 24

for iso3 in sorted(calibration_set):
    p_E = electricity[iso3]
    theta = temperature[iso3]["theta_summer"]
    p_L = construction[iso3]  # $/W
    name = temperature[iso3]["country"]
    names[iso3] = name

    pue = PUE_BASE + PUE_SLOPE * max(0, theta - THETA_REF)
    c_elec = pue * GPU_TDP_KW * p_E
    c_hw = R_HARDWARE
    # FIX: multiply by 1000 to convert kW→W (p_L is in $/W)
    c_constr = GPU_TDP_W * p_L / (DC_LIFE_YR * H_YR)
    c_total = c_elec + c_hw + c_constr

    results[iso3] = {
        "total": c_total, "elec": c_elec, "hw": c_hw, "constr": c_constr,
        "pue": pue, "p_E": p_E, "theta": theta, "p_L": p_L,
        "source": cost_source.get(iso3, "predicted"),
    }

# Rank
ranked = sorted(results.items(), key=lambda x: x[1]["total"])

# Save results
outpath = OUT / "calibration_results_v3.csv"
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rank", "iso3", "country", "c_j_total", "c_j_electricity",
                "c_j_hardware", "c_j_construction", "pue", "p_E_usd_kwh",
                "theta_summer_C", "p_L_usd_per_W", "cost_source"])
    for rank, (iso3, c) in enumerate(ranked, 1):
        w.writerow([rank, iso3, names[iso3],
                    round(c["total"], 5), round(c["elec"], 5),
                    round(c["hw"], 5), round(c["constr"], 5),
                    round(c["pue"], 3), c["p_E"], round(c["theta"], 1),
                    round(c["p_L"], 2), c["source"]])

print(f"\nSaved {outpath}")
print(f"\n{'Rank':>4} {'ISO3':<5} {'Country':<24} {'c_j':>8} {'Elec':>8} "
      f"{'Constr':>8} {'PUE':>5} {'p_E':>7}")
print("-" * 80)
for rank, (iso3, c) in enumerate(ranked[:20], 1):
    print(f"{rank:>4} {iso3:<5} {names[iso3]:<24} ${c['total']:.4f} "
          f"${c['elec']:.4f} ${c['constr']:.4f} {c['pue']:>5.2f} ${c['p_E']:.4f}")
print("...")
for rank, (iso3, c) in enumerate(ranked, 1):
    if iso3 in {'USA', 'CHN', 'IND', 'BRA', 'GBR', 'DEU', 'FRA', 'JPN', 'KOR', 'AUS',
                'SAU', 'KEN', 'MAR', 'MYS', 'IDN', 'ZAF', 'MEX'}:
        print(f"{rank:>4} {iso3:<5} {names[iso3]:<24} ${c['total']:.4f} "
              f"${c['elec']:.4f} ${c['constr']:.4f} {c['pue']:>5.2f} ${c['p_E']:.4f}")

# ═══════════════════════════════════════════════════════════════════════
# COMPUTE REGIMES USING ICEBERG TRADE COST
# ═══════════════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("REGIME ASSIGNMENT (iceberg trade cost)")
print("=" * 70)

latency_countries = set()
for (src, dst) in latency:
    latency_countries.add(src)
    latency_countries.add(dst)

cal_with_latency = calibration_set & latency_countries
print(f"Countries with cost + latency data: {len(cal_with_latency)}")


def delivered_cost(tau, l_jk, c_j):
    return (1 + tau * l_jk) * c_j


def get_latency(j, k):
    if j == k:
        return latency.get((j, k), DOMESTIC_LATENCY_DEFAULT)
    key = (j, k)
    if key in latency:
        return latency[key]
    rev = (k, j)
    if rev in latency:
        return latency[rev]
    return None


regime_rows = []
regime_counts = defaultdict(int)
regime_sov_counts = defaultdict(int)
inf_hub_counts = defaultdict(int)
train_hub_counts = defaultdict(int)

for k in sorted(cal_with_latency):
    c_k = results[k]["total"]
    l_kk = get_latency(k, k) or DOMESTIC_LATENCY_DEFAULT

    # Training: P_T(j,k) = c_j (latency = 0)
    P_T_domestic = c_k
    # Inference: P_I(j,k) = (1 + τ · l_jk) · c_j
    P_I_domestic = (1 + TAU * l_kk) * c_k

    # Best source for training: purely cheapest c_j
    best_train_j = k
    best_train_cost = c_k
    for j in sorted(cal_with_latency):
        if j == k:
            continue
        c_j = results[j]["total"]
        if c_j < best_train_cost:
            best_train_cost = c_j
            best_train_j = j

    # Best source for inference: min (1 + τ · l_jk) · c_j
    best_inf_j = k
    best_inf_cost = P_I_domestic
    for j in sorted(cal_with_latency):
        if j == k:
            continue
        l_jk = get_latency(j, k)
        if l_jk is None:
            continue
        cost = delivered_cost(TAU, l_jk, results[j]["total"])
        if cost < best_inf_cost:
            best_inf_cost = cost
            best_inf_j = j

    is_dom_train = (best_train_j == k)
    is_dom_inf = (best_inf_j == k)

    if is_dom_train and is_dom_inf:
        regime = "full domestic"
    elif not is_dom_train and not is_dom_inf:
        regime = "full import"
    elif not is_dom_train and is_dom_inf:
        regime = "import training + build inference"
    else:
        regime = "build training + import inference"

    # With sovereignty premium
    best_foreign_train = min(
        (results[j]["total"] for j in cal_with_latency if j != k),
        default=c_k
    )
    best_foreign_inf = min(
        (delivered_cost(TAU, get_latency(j, k) or 9999, results[j]["total"])
         for j in cal_with_latency if j != k and get_latency(j, k) is not None),
        default=P_I_domestic
    )

    sov_dom_train = c_k <= (1 + LAMBDA) * best_foreign_train
    sov_dom_inf = P_I_domestic <= (1 + LAMBDA) * best_foreign_inf

    if sov_dom_train and sov_dom_inf:
        regime_sov = "full domestic"
    elif not sov_dom_train and not sov_dom_inf:
        regime_sov = "full import"
    elif not sov_dom_train and sov_dom_inf:
        regime_sov = "import training + build inference"
    else:
        regime_sov = "build training + import inference"

    regime_counts[regime] += 1
    regime_sov_counts[regime_sov] += 1

    if best_inf_j != k:
        inf_hub_counts[best_inf_j] += 1
    if best_train_j != k:
        train_hub_counts[best_train_j] += 1

    regime_rows.append({
        "iso3": k, "country": names[k],
        "c_k": round(c_k, 5),
        "P_T_domestic": round(P_T_domestic, 5),
        "P_I_domestic": round(P_I_domestic, 5),
        "best_train_source": best_train_j,
        "best_train_cost": round(best_train_cost, 5),
        "best_inf_source": best_inf_j,
        "best_inf_cost": round(best_inf_cost, 5),
        "regime": regime,
        "regime_with_sovereignty": regime_sov,
    })

# Save regimes
outpath2 = OUT / "calibration_regimes_v3.csv"
with open(outpath2, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=regime_rows[0].keys())
    w.writeheader()
    w.writerows(regime_rows)

print(f"\nSaved {len(regime_rows)} countries to {outpath2}")

n = len(regime_rows)
print("\nRegime distribution (pure cost):")
for reg, c in sorted(regime_counts.items(), key=lambda x: -x[1]):
    print(f"  {reg:<45} {c:>2} ({100 * c / n:.0f}%)")

print(f"\nRegime distribution (with {LAMBDA:.0%} sovereignty premium):")
for reg, c in sorted(regime_sov_counts.items(), key=lambda x: -x[1]):
    print(f"  {reg:<45} {c:>2} ({100 * c / n:.0f}%)")

print("\nTop training sources:")
for j, cnt in sorted(train_hub_counts.items(), key=lambda x: -x[1])[:5]:
    print(f"  {j} ({names.get(j, '')[:20]}): serves {cnt} countries, "
          f"c_j=${results[j]['total']:.4f}")

print("\nInference hubs:")
for j, cnt in sorted(inf_hub_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {j} ({names.get(j, '')[:20]}): serves {cnt} countries, "
          f"c_j=${results[j]['total']:.4f}")

# ═══════════════════════════════════════════════════════════════════════
# SENSITIVITY: TAU
# ═══════════════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("SENSITIVITY: τ")
print("=" * 70)

for tau in [0.0004, 0.0008, 0.0016, 0.004]:
    n_import = 0
    n_domestic = 0
    for k in cal_with_latency:
        c_k = results[k]["total"]
        l_kk = get_latency(k, k) or DOMESTIC_LATENCY_DEFAULT
        P_I_dom = (1 + tau * l_kk) * c_k
        best_foreign = P_I_dom
        for j in cal_with_latency:
            if j == k:
                continue
            l_jk = get_latency(j, k)
            if l_jk is None:
                continue
            cost = (1 + tau * l_jk) * results[j]["total"]
            if cost < best_foreign:
                best_foreign = cost
        if best_foreign < P_I_dom:
            n_import += 1
        else:
            n_domestic += 1
    print(f"  τ = {tau:.4f}/ms: "
          f"{n_import} import inference, {n_domestic} domestic inference "
          f"(markup at 100ms: {tau * 100:.1%})")
