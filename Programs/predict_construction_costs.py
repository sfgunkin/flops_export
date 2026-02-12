"""
Predict data center construction costs (US$/watt) for all countries.

Regression: ln($/W) = a + b1*ln(GDP_pcap) + b2*ln(pop) + region dummies
Trained on Turner & Townsend DCCI 2025 (52 markets, 37 unique countries).
"""

from collections import Counter
import csv
import math
import pathlib
import numpy as np

DATA = pathlib.Path(r"F:\onedrive\__documents\papers\FLOPsExport\Data")

# ── 1. Map DCCI markets to ISO3 codes ──────────────────────────────────────

MARKET_TO_ISO3 = {
    "Tokyo": "JPN", "Singapore": "SGP", "Zurich": "CHE", "Osaka": "JPN",
    "Silicon Valley": "USA", "New Jersey": "USA", "Oslo": "NOR",
    "Auckland": "NZL", "Stockholm": "SWE", "Helsinki": "FIN",
    "Copenhagen": "DNK", "London": "GBR", "Vienna": "AUT",
    "Cardiff": "GBR", "Frankfurt": "DEU", "Berlin": "DEU",
    "Kuala Lumpur": "MYS", "Kingdom of Saudi Arabia": "SAU",
    "Chicago": "USA", "Jakarta": "IDN", "North Virginia": "USA",
    "Portland": "USA", "Paris": "FRA", "Amsterdam": "NLD",
    "São Paulo": "BRA", "Sydney": "AUS", "Lagos": "NGA",
    "Melbourne": "AUS", "Querétaro": "MEX", "Cape Town": "ZAF",
    "Lisbon": "PRT", "Seoul": "KOR", "Johannesburg": "ZAF",
    "Bordeaux": "FRA", "Dublin": "IRL", "Madrid": "ESP",
    "Atlanta": "USA", "Montevideo": "URY", "Phoenix": "USA",
    "Columbus": "USA", "Milan": "ITA", "Nairobi": "KEN",
    "Dallas": "USA", "Charlotte": "USA", "Toronto": "CAN",
    "UAE": "ARE", "Warsaw": "POL", "Santiago": "CHL",
    "Athens": "GRC", "Bogotá": "COL", "Mumbai": "IND",
    "Shanghai": "CHN",
}

# ── 2. Load DCCI data ─────────────────────────────────────────────────────

dcci = {}
with open(DATA / "dcci_2025_construction_costs.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        market = row["market"]
        iso3 = MARKET_TO_ISO3[market]
        cost = float(row["usd_per_watt"])
        if iso3 in dcci:
            dcci[iso3]["costs"].append(cost)
        else:
            dcci[iso3] = {"costs": [cost], "market": market}

for iso3 in dcci:
    dcci[iso3]["avg_cost"] = np.mean(dcci[iso3]["costs"])

print(f"DCCI: {len(dcci)} unique countries from 52 markets")
print("  Multi-city: ", end="")
for iso3, d in dcci.items():
    if len(d["costs"]) > 1:
        print(f"{iso3}({len(d['costs'])})", end=" ")
print()

# ── 3. Load World Bank data ────────────────────────────────────────────────

gdp = {}
with open(DATA / "wb_gdp_per_capita_ppp_2023.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        gdp[row["iso3"]] = {
            "country": row["country"],
            "gdp_pcap": float(row["gdp_pcap_ppp_2023"]),
        }

pop = {}
with open(DATA / "wb_population_2023.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        pop[row["iso3"]] = int(row["population_2023"])

regions = {}
with open(DATA / "wb_country_regions.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        regions[row["iso3"]] = row["region"]

print(f"World Bank: {len(gdp)} GDP, {len(pop)} pop, {len(regions)} regions")

# Region list (omit one as reference category)
REGION_NAMES = sorted(set(regions.values()))
print(f"Regions ({len(REGION_NAMES)}): {REGION_NAMES}")
# Reference category = the most common region in DCCI sample
REF_REGION = "Europe & Central Asia"
DUMMY_REGIONS = [r for r in REGION_NAMES if r != REF_REGION]
print(f"Reference region: {REF_REGION}")
print(f"Dummy regions ({len(DUMMY_REGIONS)}): {DUMMY_REGIONS}")

# ── 4. Match and prepare regression data ───────────────────────────────────

matched = []
unmatched = []
for iso3, d in dcci.items():
    if iso3 in gdp and iso3 in pop and iso3 in regions:
        matched.append({
            "iso3": iso3,
            "cost": d["avg_cost"],
            "gdp_pcap": gdp[iso3]["gdp_pcap"],
            "pop": pop[iso3],
            "region": regions[iso3],
        })
    else:
        missing = []
        if iso3 not in gdp:
            missing.append("gdp")
        if iso3 not in pop:
            missing.append("pop")
        if iso3 not in regions:
            missing.append("region")
        unmatched.append(f"{iso3}({','.join(missing)})")

if unmatched:
    print(f"WARNING: no match for: {unmatched}")

print(f"Matched: {len(matched)} countries for regression")

# Show region distribution in sample
reg_counts = Counter(m["region"] for m in matched)
for r, c in reg_counts.most_common():
    print(f"  {r}: {c}")

# ── 5. OLS regression ─────────────────────────────────────────────────────
# ln($/W) = a + b1*ln(gdp_pcap) + b2*ln(pop) + sum(g_r * D_r)

n = len(matched)
k = 3 + len(DUMMY_REGIONS)  # intercept + ln_gdp + ln_pop + dummies

y = np.array([math.log(m["cost"]) for m in matched])

# Build X matrix
X = np.zeros((n, k))
col_names = ["intercept", "ln_gdp_pcap", "ln_pop"] + [f"D_{r[:8]}" for r in DUMMY_REGIONS]

for i, m in enumerate(matched):
    X[i, 0] = 1.0  # intercept
    X[i, 1] = math.log(m["gdp_pcap"])  # ln GDP per capita
    X[i, 2] = math.log(m["pop"])  # ln population
    for j, reg in enumerate(DUMMY_REGIONS):
        X[i, 3 + j] = 1.0 if m["region"] == reg else 0.0

# OLS
beta = np.linalg.lstsq(X, y, rcond=None)[0]
y_hat = X @ beta
resid = y - y_hat
ss_res = np.sum(resid**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - ss_res / ss_tot
adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k)
rmse = math.sqrt(ss_res / (n - k))

# Standard errors
try:
    var_beta = ss_res / (n - k) * np.diag(np.linalg.inv(X.T @ X))
    se = np.sqrt(np.maximum(var_beta, 0))
    t_stats = beta / np.where(se > 0, se, 1)
except np.linalg.LinAlgError:
    se = np.full(k, np.nan)
    t_stats = np.full(k, np.nan)

print(f"\n{'=' * 70}")
print("OLS: ln($/W) = a + b1*ln(GDP/cap) + b2*ln(Pop) + region dummies")
print(f"{'=' * 70}")
print(f"  N = {n},  k = {k},  R2 = {r_squared:.4f},  adj-R2 = {adj_r_squared:.4f},  RMSE = {rmse:.4f}")
print(f"\n  {'Variable':<20} {'Coeff':>8} {'SE':>8} {'t':>8}")
print(f"  {'-' * 48}")
for j in range(k):
    sig = ""
    if abs(t_stats[j]) > 2.576:
        sig = "***"
    elif abs(t_stats[j]) > 1.96:
        sig = "**"
    elif abs(t_stats[j]) > 1.645:
        sig = "*"
    print(f"  {col_names[j]:<20} {beta[j]:>8.4f} {se[j]:>8.4f} {t_stats[j]:>8.2f} {sig}")

# ── 6. Residuals for DCCI countries ───────────────────────────────────────

print(f"\n{'=' * 70}")
print(f"{'Country':<6} {'Region':<16} {'Actual':>8} {'Predicted':>10} {'Resid':>8}")
print(f"{'=' * 70}")
for i, m in enumerate(sorted(matched, key=lambda x: x["cost"], reverse=True)):
    idx = next(j for j, mm in enumerate(matched) if mm["iso3"] == m["iso3"])
    pred = math.exp(y_hat[idx])
    r = m["cost"] - pred
    print(f"{m['iso3']:<6} {m['region'][:15]:<16} {m['cost']:>8.2f} {pred:>10.2f} {r:>+8.2f}")

# ── 7. Predict for all countries ──────────────────────────────────────────

output = []
for iso3, gdata in gdp.items():
    if iso3 not in pop or iso3 not in regions:
        continue
    g = gdata["gdp_pcap"]
    p = pop[iso3]
    reg = regions[iso3]

    x_pred = np.zeros(k)
    x_pred[0] = 1.0
    x_pred[1] = math.log(g)
    x_pred[2] = math.log(p)
    for j, dr in enumerate(DUMMY_REGIONS):
        x_pred[3 + j] = 1.0 if reg == dr else 0.0

    ln_pred = x_pred @ beta
    # Smearing adjustment for log retransformation: E[y] = exp(ln_pred) * exp(s2/2)
    pred_cost = math.exp(ln_pred + ss_res / (2 * (n - k)))

    source = "DCCI" if iso3 in dcci else "predicted"
    actual = dcci[iso3]["avg_cost"] if iso3 in dcci else None

    output.append({
        "iso3": iso3,
        "country": gdata["country"],
        "region": reg,
        "gdp_pcap_ppp": round(g, 2),
        "population": p,
        "predicted_usd_per_watt": round(pred_cost, 2),
        "actual_usd_per_watt": round(actual, 2) if actual else "",
        "source": source,
    })

output.sort(key=lambda r: r["predicted_usd_per_watt"], reverse=True)

outpath = DATA / "predicted_construction_costs.csv"
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=output[0].keys())
    w.writeheader()
    w.writerows(output)

n_pred = sum(1 for r in output if r["source"] == "predicted")
print(f"\nSaved {len(output)} countries ({n_pred} predicted, {len(output) - n_pred} DCCI) to:")
print(f"  {outpath}")
