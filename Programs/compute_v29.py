"""Phase 1: Compute new xi and costs for v29 (floor removal)."""
import csv
import math
import pathlib

DATA = pathlib.Path(r"F:\onedrive\__documents\papers\FLOPsExport\Data")

# ── Model parameters ──
GPU_PRICE = 25_000
GPU_LIFE = 3
GPU_UTIL = 0.70
H_YR = 365.25 * 24
RHO = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL)
ETA = 0.15
GAMMA = 0.700
PHI = 1.08
DELTA_PUE = 0.015
THETA_REF = 15.0
OMEGA = 0.50
XI_FLOOR_OLD = 0.30

SUBSIDY_ADJ = {
    'IRN': 0.085, 'TKM': 0.070, 'DZA': 0.065, 'EGY': 0.080,
    'UZB': 0.090, 'QAT': 0.100, 'SAU': 0.100, 'ARE': 0.095,
    'RUS': 0.065, 'KAZ': 0.085, 'NGA': 0.080, 'ZAF': 0.095,
    'ETH': 0.050,
}

HIGH_INCOME = {
    'Norway', 'Finland', 'Canada', 'Sweden', 'Iceland', 'New Zealand',
    'United States of America', 'Australia', 'United Kingdom', 'Denmark',
    'France', 'Luxembourg', 'Netherlands', 'Belgium', 'Estonia', 'Latvia',
    'Switzerland', 'Portugal', 'Japan', 'Germany', 'Austria', 'Ireland',
    'Singapore', 'South Korea', 'Israel', 'Czech Republic', 'Czechia',
    'Slovenia', 'Lithuania', 'Spain', 'Italy', 'Greece', 'Poland',
    'Hungary', 'Croatia', 'Slovakia', 'Chile', 'Uruguay', 'Romania',
    'Bulgaria', 'United Arab Emirates', 'Saudi Arabia', 'Qatar', 'Bahrain',
    'Kuwait', 'Oman', 'Brunei',
}

# ── Load calibration data ──
print("Loading calibration_results_v3.csv...")
cal = {}
with open(DATA / "calibration_results_v3.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        iso = row["iso3"]
        cal[iso] = {
            "country": row["country"],
            "p_E": float(row["p_E_usd_kwh"]),
            "theta": float(row["theta_summer_C"]),
            "pue": float(row["pue"]),
            "constr_per_w": float(row["p_L_usd_per_W"]),
            "c_j_total": float(row["c_j_total"]),
        }

# ── Load G and R from xi_scenarios_data.csv ──
print("Loading xi_scenarios_data.csv...")
xi_data = {}
with open(DATA / "xi_scenarios_data.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        iso = row["iso"]
        xi_data[iso] = {
            "G": float(row["G_RoL"]),
            "R": float(row["R_grid"]),
        }

# ── Load MW capacity ──
print("Loading dc_capacity_estimates.csv...")
mw_cap = {}
with open(DATA / "dc_capacity_estimates.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        mw_cap[row["iso3"]] = float(row["capacity_mw"])

# ── Compute demand shares ──
dc_k = {}
for iso in cal:
    dc_k[iso] = mw_cap.get(iso, 5.0)
total_dc = sum(dc_k.values())
omega_share = {iso: d / total_dc for iso, d in dc_k.items()}

# ── Compute new values for all 85 countries ──
print(f"\nComputing for {len(cal)} countries (RHO={RHO:.5f})...")
results = []
for iso, c in cal.items():
    gd = xi_data.get(iso)
    if gd is None:
        print(f"  WARNING: No G/R data for {iso}, skipping")
        continue

    G = gd["G"]
    R = gd["R"]
    cr_pe = SUBSIDY_ADJ.get(iso, c["p_E"])
    pue = c["pue"]

    # Cost-recovery cost (protocol formula: no construction)
    c_cr = RHO + cr_pe * pue * GAMMA + ETA

    # Old xi (with floor)
    xi_raw = (G ** OMEGA) * (R ** (1 - OMEGA))
    xi_old = XI_FLOOR_OLD + (1 - XI_FLOOR_OLD) * xi_raw

    # New xi (no floor)
    xi_new = xi_raw  # = G^0.50 * R^0.50

    # Adjusted costs
    c_adj_old = RHO + (c_cr - RHO) / xi_old if xi_old > 0 else 999
    c_adj_new = RHO + (c_cr - RHO) / xi_new if xi_new > 0 else 999

    results.append({
        "iso": iso,
        "country": c["country"],
        "G": G,
        "R": R,
        "cr_pe": cr_pe,
        "theta": c["theta"],
        "pue": pue,
        "constr_per_w": c["constr_per_w"],
        "mw": dc_k.get(iso, 5.0),
        "omega_share": omega_share.get(iso, 0),
        "xi_old": xi_old,
        "xi_new": xi_new,
        "c_cr": c_cr,
        "c_adj_old": c_adj_old,
        "c_adj_new": c_adj_new,
    })

# ── Rank ──
results.sort(key=lambda r: r["c_adj_new"])
for rank, r in enumerate(results, 1):
    r["rank_new"] = rank

# Old ranking
old_sorted = sorted(results, key=lambda r: r["c_adj_old"])
for rank, r in enumerate(old_sorted, 1):
    r["rank_old"] = rank

# CR ranking
cr_sorted = sorted(results, key=lambda r: r["c_cr"])
for rank, r in enumerate(cr_sorted, 1):
    r["rank_cr"] = rank

# ── Checkpoints ──
print("\n=== Checkpoints ===")
for name in ["Norway", "Canada", "Finland", "Kyrgyzstan", "Ethiopia"]:
    r = next((x for x in results if x["country"] == name), None)
    if r:
        print(f"  {name:15s}: xi_new={r['xi_new']:.4f}  c_adj_new=${r['c_adj_new']:.4f}"
              f"  rank_new={r['rank_new']}  (xi_old={r['xi_old']:.4f}  c_adj_old=${r['c_adj_old']:.4f})")

# ── Save country_results_v29.csv ──
out_path = DATA / "country_results_v29.csv"
fields = ["iso", "country", "G", "R", "cr_pe", "theta", "pue", "constr_per_w",
          "mw", "omega_share", "xi_old", "xi_new", "c_cr", "c_adj_old",
          "c_adj_new", "rank_old", "rank_new", "rank_cr"]
with open(out_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in sorted(results, key=lambda x: x["rank_new"]):
        w.writerow({k: r[k] for k in fields})
print(f"\nSaved {out_path}")

# ── Note xi values for P72 prose ──
print("\n=== P72 prose values ===")
for name in ["Kyrgyzstan", "Uzbekistan", "Ethiopia"]:
    r = next((x for x in results if x["country"] == name), None)
    if r:
        print(f"  {name}: xi_new = {r['xi_new']:.2f}")

# ── Sensitivity analysis (Table A3) ──
print("\n=== Table A3 Sensitivity Specs ===")

def compute_spec(label, param_change, omega_val, rho_val, form, results_data):
    """Compute one sensitivity spec."""
    spec_results = []
    for r in results_data:
        G, R = r["G"], r["R"]
        xi = (G ** omega_val) * (R ** (1 - omega_val))
        cr_pe = r["cr_pe"]
        pue = r["pue"]
        c_cr = rho_val + cr_pe * pue * GAMMA + ETA
        if form == "B":
            c_adj = rho_val + (c_cr - rho_val) / xi if xi > 0 else 999
        else:  # Form A
            c_adj = c_cr / xi if xi > 0 else 999
        spec_results.append({
            "country": r["country"],
            "iso": r["iso"],
            "c_adj": c_adj,
            "c_cr": c_cr,
            "xi": xi,
        })

    # Rank by c_adj
    spec_results.sort(key=lambda x: x["c_adj"])
    for rank, sr in enumerate(spec_results, 1):
        sr["rank_adj"] = rank

    # Rank by c_cr
    cr_sorted2 = sorted(spec_results, key=lambda x: x["c_cr"])
    for rank, sr in enumerate(cr_sorted2, 1):
        sr["rank_cr"] = rank

    # Top 15
    top15 = spec_results[:15]
    dev_top15 = sum(1 for sr in top15 if sr["country"] not in HIGH_INCOME)

    # Max markup in top 15
    costs_top15 = [sr["c_adj"] for sr in top15]
    max_markup = (max(costs_top15) - min(costs_top15)) / min(costs_top15) * 100

    # Spearman rho vs cr
    n = len(spec_results)
    d_sq = sum((sr["rank_adj"] - sr["rank_cr"]) ** 2 for sr in spec_results)
    spearman = 1 - 6 * d_sq / (n * (n ** 2 - 1))

    # Top 5 names
    top5 = ", ".join(sr["country"] for sr in spec_results[:5])

    print(f"  {label}: Dev={dev_top15}, Markup={max_markup:.1f}%, "
          f"Spearman={spearman:.2f}, Top5={top5}")

    return {
        "Scenario": label,
        "Parameter_change": param_change,
        "Dev_top15": str(dev_top15),
        "Max_markup": f"{max_markup:.1f}%",
        "Spearman_rho": f"{spearman:.2f}",
        "Top5": top5,
    }


specs = [
    ("Baseline (omega=0.50, rho=$1.36, Form B)",
     "omega=0.50, rho=$1.36", 0.50, RHO, "B"),
    ("High governance weight (omega=0.85)",
     "omega=0.85", 0.85, RHO, "B"),
    ("Low hardware share (rho=$1.30)",
     "rho=$1.30 (-4.4%)", 0.50, 1.30, "B"),
    ("High hardware share (rho=$1.42)",
     "rho=$1.42 (+4.4%)", 0.50, 1.42, "B"),
    ("Form A (v26 specification)",
     "c_adj = c_cr / xi_eff, omega=0.85", 0.85, RHO, "A"),
]

a3_rows = []
for label, param, omega_val, rho_val, form in specs:
    row = compute_spec(label, param, omega_val, rho_val, form, results)
    a3_rows.append(row)

# Save tableA3_v29.csv
a3_path = DATA / "tableA3_v29.csv"
a3_fields = ["Scenario", "Parameter_change", "Dev_top15", "Max_markup",
             "Spearman_rho", "Top5"]
with open(a3_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=a3_fields)
    w.writeheader()
    for row in a3_rows:
        w.writerow(row)
print(f"\nSaved {a3_path}")

# ── Omega sensitivity sweep (Phase 1.5) ──
print("\n=== Omega sensitivity sweep ===")
print("  (Using separate G, R — NOT degenerate)")
for omega_val_sweep in [x / 100 for x in range(30, 90, 5)]:
    spec_sweep = []
    for r in results:
        G, R = r["G"], r["R"]
        xi = (G ** omega_val_sweep) * (R ** (1 - omega_val_sweep))
        cr_pe = r["cr_pe"]
        pue = r["pue"]
        c_cr = RHO + cr_pe * pue * GAMMA + ETA
        c_adj = RHO + (c_cr - RHO) / xi if xi > 0 else 999
        spec_sweep.append({"country": r["country"], "c_adj": c_adj})
    spec_sweep.sort(key=lambda x: x["c_adj"])
    top15 = spec_sweep[:15]
    dev = sum(1 for s in top15 if s["country"] not in HIGH_INCOME)
    print(f"  omega={omega_val_sweep:.2f}: dev in top 15 = {dev}")

# ── Top 15 new ranking ──
print("\n=== New efficiency-adjusted top 15 ===")
for r in sorted(results, key=lambda x: x["rank_new"])[:15]:
    dev = "D" if r["country"] not in HIGH_INCOME else "A"
    print(f"  {r['rank_new']:2d}. {r['country']:30s} ${r['c_adj_new']:.4f}  "
          f"xi={r['xi_new']:.4f}  [{dev}]  (was #{r['rank_old']})")

print("\nPhase 1 complete.")
