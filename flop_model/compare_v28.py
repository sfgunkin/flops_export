"""Compare fresh pipeline output with v28 recalculated Table 3."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import pandas as pd

PAPER_ROOT = r"F:\onedrive\__documents\papers\FLOPsExport"
FRESH_DIR = os.path.join(PAPER_ROOT, "flop_model", "output")
V28_FILE = os.path.join(PAPER_ROOT, "Data", "output", "table3_recalculated.xlsx")

# Load fresh
fresh_3a = pd.read_csv(os.path.join(FRESH_DIR, "table_3a.csv"))
fresh_3b = pd.read_csv(os.path.join(FRESH_DIR, "table_3b.csv"))

# Load v28
v28_3a = pd.read_excel(V28_FILE, sheet_name="Table_3a", header=[0, 1])
v28_3b = pd.read_excel(V28_FILE, sheet_name="Table_3b", header=[0, 1])

# Flatten v28 headers
v28_3a.columns = [
    "Country", "c_raw", "Rank_1", "Type_1",
    "c_cr", "Rank_2", "Type_2",
    "c_adj", "xi", "Rank_3", "Type_3",
    "c_adj_4", "Rank_4", "Type_4", "Delta",
]
v28_3b.columns = [
    "Country", "c_adj", "Type_4", "Type_6", "Rank_6", "Type_7", "lambda_star",
]

# Parse v28 dollar-formatted costs
for col in ["c_raw", "c_cr", "c_adj", "c_adj_4"]:
    v28_3a[col] = v28_3a[col].astype(str).str.replace("$", "", regex=False).astype(float)
v28_3b["c_adj"] = v28_3b["c_adj"].astype(str).str.replace("$", "", regex=False).astype(float)
v28_3a["Delta"] = v28_3a["Delta"].astype(str).str.replace("+", "", regex=False).astype(int)

# Standardize country names
name_map = {
    "United States of America": "United States",
    "United Arab Emirates": "UAE",
}
v28_3a["Country"] = v28_3a["Country"].replace(name_map)
v28_3b["Country"] = v28_3b["Country"].replace(name_map)

# ---- Comparison ----
print("=" * 110)
print("COMPARISON: Fresh Pipeline vs v28 Recalculated -- Table 3a (Top 25 by Col 4 Rank)")
print("=" * 110)
print()

fresh_countries = set(fresh_3a["Country"])
v28_countries = set(v28_3a["Country"])
only_fresh = sorted(fresh_countries - v28_countries)
only_v28 = sorted(v28_countries - fresh_countries)
both = sorted(fresh_countries & v28_countries)

print(f"Countries in FRESH top 25 only: {only_fresh}")
print(f"Countries in V28 top 25 only:   {only_v28}")
print(f"Countries in BOTH:              {len(both)}")
print()

# ---- c_adj (efficiency-adjusted cost) comparison ----
print("--- EFFICIENCY-ADJUSTED COST (c_adj) & RANK COMPARISON ---")
header = f"{'Country':<22} {'Fresh':>8} {'v28':>8} {'Diff':>8}  {'F_Rk':>5} {'V_Rk':>5} {'dRk':>5}  {'F_xi':>6} {'V_xi':>5}  {'F_Ty':>5} {'V_Ty':>5}"
print(header)
print("-" * len(header))

for c in both:
    fr = fresh_3a[fresh_3a["Country"] == c].iloc[0]
    v2 = v28_3a[v28_3a["Country"] == c].iloc[0]
    diff_c = fr["c_adj"] - v2["c_adj"]
    diff_r = int(fr["Rank_4"]) - int(v2["Rank_4"])
    ty_match = "" if fr["Type_4"] == v2["Type_4"] else " <--"
    print(
        f"{c:<22} ${fr['c_adj']:.4f} ${v2['c_adj']:.2f}  {diff_c:>+.4f}  "
        f"{int(fr['Rank_4']):>5} {int(v2['Rank_4']):>5} {diff_r:>+5}  "
        f"{fr['xi']:.4f} {v2['xi']:.2f}  "
        f"{fr['Type_4']:>5} {v2['Type_4']:>5}{ty_match}"
    )
print()

# ---- Raw cost comparison ----
print("--- RAW COST (c_raw, Col 1) COMPARISON ---")
header2 = f"{'Country':<22} {'Fresh':>9} {'v28':>8} {'Diff':>8}  {'F_Rk':>5} {'V_Rk':>5}"
print(header2)
print("-" * len(header2))
for c in both:
    fr = fresh_3a[fresh_3a["Country"] == c].iloc[0]
    v2 = v28_3a[v28_3a["Country"] == c].iloc[0]
    diff = fr["c_raw"] - v2["c_raw"]
    print(f"{c:<22} ${fr['c_raw']:.4f}  ${v2['c_raw']:.2f}  {diff:>+.4f}  {int(fr['Rank_1']):>5} {int(v2['Rank_1']):>5}")
print()

# ---- Type (regime) comparison across all columns ----
print("--- REGIME TYPE COMPARISON ---")
header3 = f"{'Country':<22} {'F_T1':>5} {'V_T1':>5}  {'F_T2':>5} {'V_T2':>5}  {'F_T4':>5} {'V_T4':>5}  Mismatches"
print(header3)
print("-" * len(header3))
total_mm = 0
for c in both:
    fr = fresh_3a[fresh_3a["Country"] == c].iloc[0]
    v2 = v28_3a[v28_3a["Country"] == c].iloc[0]
    mm = []
    for col_name in ["Type_1", "Type_2", "Type_4"]:
        if fr[col_name] != v2[col_name]:
            mm.append(col_name)
    total_mm += len(mm)
    mm_str = ", ".join(mm) if mm else ""
    print(
        f"{c:<22} {fr['Type_1']:>5} {v2['Type_1']:>5}  "
        f"{fr['Type_2']:>5} {v2['Type_2']:>5}  "
        f"{fr['Type_4']:>5} {v2['Type_4']:>5}  {mm_str}"
    )
print(f"\nTotal cell mismatches: {total_mm}")
print()

# ---- Table 3b comparison ----
print("=" * 110)
print("TABLE 3b COMPARISON (Col 6 uniform, Col 7 FDI)")
print("=" * 110)
print()

header4 = f"{'Country':<22} {'F_T6':>5} {'V_T6':>5}  {'F_Rk6':>5} {'V_Rk6':>5}  {'F_T7':>5} {'V_T7':>5}  Mismatches"
print(header4)
print("-" * len(header4))
both_3b = sorted(set(fresh_3b["Country"]) & set(v28_3b["Country"]))
mm_3b = 0
for c in both_3b:
    fr = fresh_3b[fresh_3b["Country"] == c].iloc[0]
    v2 = v28_3b[v28_3b["Country"] == c].iloc[0]
    mm = []
    if fr["Type_6"] != v2["Type_6"]:
        mm.append("Type_6")
    if int(fr["Rank_6"]) != int(v2["Rank_6"]):
        mm.append("Rank_6")
    if fr["Type_7"] != v2["Type_7"]:
        mm.append("Type_7")
    mm_3b += len(mm)
    mm_str = ", ".join(mm) if mm else ""
    print(
        f"{c:<22} {fr['Type_6']:>5} {v2['Type_6']:>5}  "
        f"{int(fr['Rank_6']):>5} {int(v2['Rank_6']):>5}  "
        f"{fr['Type_7']:>5} {v2['Type_7']:>5}  {mm_str}"
    )
print(f"\nTotal cell mismatches: {mm_3b}")
print()

# ---- Summary statistics ----
print("=" * 110)
print("SUMMARY")
print("=" * 110)
# Average cost difference for countries in both
diffs = []
for c in both:
    fr = fresh_3a[fresh_3a["Country"] == c].iloc[0]
    v2 = v28_3a[v28_3a["Country"] == c].iloc[0]
    diffs.append(fr["c_adj"] - v2["c_adj"])

print(f"Average c_adj difference (fresh - v28):  +${sum(diffs)/len(diffs):.4f}")
print(f"Min c_adj difference:                    +${min(diffs):.4f}")
print(f"Max c_adj difference:                    +${max(diffs):.4f}")
print()

# Fresh: all costs above theoretical minimum?
rho_eta = 1.358 + 0.15  # = 1.508
all_above = (fresh_3a["c_raw"] >= rho_eta - 0.001).all()
fresh_min = fresh_3a["c_raw"].min()
v28_min = v28_3a["c_raw"].min()
print(f"Theoretical minimum (rho+eta):           ${rho_eta:.3f}")
print(f"Fresh min c_raw:                         ${fresh_min:.4f}  {'PASS' if all_above else 'FAIL'}")
print(f"v28 min c_raw:                           ${v28_min:.2f}  {'PASS' if v28_min >= rho_eta - 0.001 else 'FAIL -- below rho+eta!'}")
print()

# xi comparison
print("xi comparison for countries in both:")
xi_diffs = []
for c in both:
    fr = fresh_3a[fresh_3a["Country"] == c].iloc[0]
    v2 = v28_3a[v28_3a["Country"] == c].iloc[0]
    xi_diffs.append(abs(fr["xi"] - v2["xi"]))
print(f"Average |xi difference|: {sum(xi_diffs)/len(xi_diffs):.4f}")
print(f"Max |xi difference|:     {max(xi_diffs):.4f}")
print()

# Rank correlation
from scipy.stats import spearmanr
fr_ranks = []
v2_ranks = []
for c in both:
    fr = fresh_3a[fresh_3a["Country"] == c].iloc[0]
    v2 = v28_3a[v28_3a["Country"] == c].iloc[0]
    fr_ranks.append(int(fr["Rank_4"]))
    v2_ranks.append(int(v2["Rank_4"]))
rho_corr, _ = spearmanr(fr_ranks, v2_ranks)
print(f"Spearman rank correlation (Col 4): {rho_corr:.4f}")

# ---- Full 85-country comparison ----
print()
print("=" * 110)
print("FULL 85-COUNTRY COMPARISON (Table A1 vs v28 Full)")
print("=" * 110)

fresh_a1 = pd.read_csv(os.path.join(FRESH_DIR, "table_a1.csv"))
# Also load fresh full 3a for rank/type info (has all 85 rows with c_raw)
fresh_full_3a = pd.read_csv(os.path.join(FRESH_DIR, "table_3a.csv").replace("table_3a", "table_a1"))
# Actually use the main 3a but load from the full pipeline panel for all 85
# The table_3a.csv only has top 25. Use table_a1 which has all 85.
# table_a1 has: Country, iso3, p_E, theta, PUE, Constr_per_W, k_bar_MW, omega_pct, xi, c_adj, mu, Cost_Rec_pE
# We need c_adj and xi from fresh_a1, and rank by c_adj

fresh_a1 = fresh_a1.sort_values("c_adj").reset_index(drop=True)
fresh_a1["Rank_4_fr"] = range(1, len(fresh_a1) + 1)

v28_full = pd.read_excel(V28_FILE, sheet_name="Table_3a_full", header=[0, 1])
v28_full.columns = [
    "Country", "c_raw", "Rank_1", "Type_1",
    "c_cr", "Rank_2", "Type_2",
    "c_adj", "xi", "Rank_3", "Type_3",
    "c_adj_4", "Rank_4", "Type_4", "Delta",
]
for col in ["c_raw", "c_cr", "c_adj", "c_adj_4"]:
    v28_full[col] = v28_full[col].astype(str).str.replace("$", "", regex=False).astype(float)
v28_full["Country"] = v28_full["Country"].replace(name_map)

print(f"Fresh A1 rows: {len(fresh_a1)}, v28 full rows: {len(v28_full)}")

m = fresh_a1[["Country", "c_adj", "xi", "Rank_4_fr"]].merge(
    v28_full[["Country", "c_adj", "xi", "Rank_4", "Type_4"]].rename(
        columns={"c_adj": "c_adj_v28", "xi": "xi_v28", "Rank_4": "Rank_4_v28", "Type_4": "Type_4_v28"}
    ),
    on="Country", how="outer",
).rename(columns={"c_adj": "c_adj_fr", "xi": "xi_fr"})

only_fr = m[m["c_adj_v28"].isna()]["Country"].tolist()
only_v28m = m[m["c_adj_fr"].isna()]["Country"].tolist()
if only_fr:
    print(f"Only in fresh: {only_fr}")
if only_v28m:
    print(f"Only in v28: {only_v28m}")

matched = m.dropna(subset=["Rank_4_fr", "Rank_4_v28"])
rho2, _ = spearmanr(matched["Rank_4_fr"], matched["Rank_4_v28"])
print(f"Spearman rank correlation (full {len(matched)} countries, Col 4): {rho2:.4f}")
print()

# Top 15 by fresh rank
print("TOP 15 by fresh pipeline rank:")
fmt = "{:>3} {:<22} {:>8} {:>8} {:>5} {:>5} {:>7} {:>5}"
print(fmt.format("#", "Country", "F_cadj", "V_cadj", "F_Rk", "V_Rk", "F_xi", "V_xi"))
print("-" * 85)
top15 = matched.nsmallest(15, "Rank_4_fr")
for _, r in top15.iterrows():
    print(fmt.format(
        int(r["Rank_4_fr"]),
        r["Country"],
        f"${r['c_adj_fr']:.4f}",
        f"${r['c_adj_v28']:.2f}",
        int(r["Rank_4_fr"]),
        int(r["Rank_4_v28"]),
        f"{r['xi_fr']:.4f}",
        f"{r['xi_v28']:.2f}",
    ))
print()

# Cost difference statistics
avg_d = (matched["c_adj_fr"] - matched["c_adj_v28"]).mean()
std_d = (matched["c_adj_fr"] - matched["c_adj_v28"]).std()
print(f"Average c_adj difference (full {len(matched)} countries): +${avg_d:.4f} (std ${std_d:.4f})")

# Countries where rank changed most
matched["rank_change"] = abs(matched["Rank_4_fr"] - matched["Rank_4_v28"])
big_movers = matched.nlargest(10, "rank_change")
print()
print("Biggest rank changes (Col 4):")
for _, r in big_movers.iterrows():
    d = int(r["Rank_4_fr"]) - int(r["Rank_4_v28"])
    print(f"  {r['Country']:<22} Fresh Rk={int(r['Rank_4_fr']):>3}  v28 Rk={int(r['Rank_4_v28']):>3}  Change={d:>+3}")

# Bottom 10 by fresh rank
print()
print("BOTTOM 10 by fresh pipeline rank:")
bottom10 = matched.nlargest(10, "Rank_4_fr")
for _, r in bottom10.iterrows():
    print(fmt.format(
        int(r["Rank_4_fr"]),
        r["Country"],
        f"${r['c_adj_fr']:.4f}",
        f"${r['c_adj_v28']:.2f}",
        int(r["Rank_4_fr"]),
        int(r["Rank_4_v28"]),
        f"{r['xi_fr']:.4f}",
        f"{r['xi_v28']:.2f}",
    ))
