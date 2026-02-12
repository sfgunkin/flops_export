"""
Process Eurostat + EIA electricity price data into country-level averages.

For data center calibration we want:
  - Large industrial consumers (closest to DC consumption)
  - Excluding taxes (DCs often get tax exemptions)
  - EUR prices (common unit)
  - Most recent available data

Eurostat: band MWH20000-69999 (~20-70 GWh/yr, typical large DC), X_TAX, EUR
EIA: US national + state-level industrial prices (cents/kWh -> EUR/kWh)

Output: country_electricity_prices.csv
"""

import csv
import pathlib
from collections import defaultdict
import numpy as np

DATA = pathlib.Path(r"F:\onedrive\__documents\papers\FLOPsExport\Data")

# Eurostat 2-letter geo codes to ISO3
EUROSTAT_TO_ISO3 = {
    "AL": "ALB", "AT": "AUT", "BA": "BIH", "BE": "BEL", "BG": "BGR",
    "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST",
    "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA", "GE": "GEO",
    "HR": "HRV", "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA",
    "LI": "LIE", "LT": "LTU", "LU": "LUX", "LV": "LVA", "MD": "MDA",
    "ME": "MNE", "MK": "MKD", "MT": "MLT", "NL": "NLD", "NO": "NOR",
    "PL": "POL", "PT": "PRT", "RO": "ROU", "RS": "SRB", "SE": "SWE",
    "SI": "SVN", "SK": "SVK", "TR": "TUR", "UA": "UKR", "UK": "GBR",
    "XK": "XKX",
}
# Skip aggregates
SKIP_GEOS = {"EA", "EU27_2020"}

# EUR/USD approximate rate for converting EIA data (2024 average)
EUR_USD = 0.92

# ── 1. Process Eurostat data ──────────────────────────────────────────────

print("Processing Eurostat electricity prices...")

# Preferred filters (in order of preference for consumption band)
PREFERRED_BANDS = [
    "MWH20000-69999",   # 20-70 GWh — large data center
    "MWH70000-149999",  # 70-150 GWh — very large DC
    "MWH_GE150000",     # 150+ GWh — hyperscale
    "MWH2000-19999",    # 2-20 GWh — medium DC
    "TOT_KWH",          # all bands average (fallback)
]

# Collect: geo -> band -> [(period, price)]
eurostat_raw = defaultdict(lambda: defaultdict(list))

with open(DATA / "eurostat_electricity_prices.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        geo = row["geo"]
        if geo in SKIP_GEOS:
            continue
        if row["tax"] != "X_TAX":  # excluding all taxes
            continue
        if row["currency"] != "EUR":
            continue
        band = row["nrg_cons"]
        period = row["TIME_PERIOD"]
        try:
            price = float(row["OBS_VALUE"])
        except (ValueError, TypeError):
            continue
        if price <= 0:
            continue

        eurostat_raw[geo][band].append((period, price))

# For each country, pick best band and most recent 2 semesters
eurostat = {}
for geo, bands in eurostat_raw.items():
    iso3 = EUROSTAT_TO_ISO3.get(geo)
    if not iso3:
        continue

    # Try bands in preference order
    chosen_band = None
    chosen_prices = []
    for band in PREFERRED_BANDS:
        if band in bands:
            # Sort by period descending, take most recent 2
            entries = sorted(bands[band], key=lambda x: x[0], reverse=True)
            chosen_prices = [p for _, p in entries[:2]]
            chosen_band = band
            break

    if not chosen_prices:
        # Fallback: any band, most recent
        all_entries = []
        for band, entries in bands.items():
            all_entries.extend(entries)
        if all_entries:
            all_entries.sort(key=lambda x: x[0], reverse=True)
            chosen_prices = [all_entries[0][1]]
            chosen_band = "fallback"

    if chosen_prices:
        avg_eur_kwh = np.mean(chosen_prices)
        eurostat[iso3] = {
            "price_eur_kwh": avg_eur_kwh,
            "price_usd_kwh": avg_eur_kwh / EUR_USD,
            "band": chosen_band,
            "source": "Eurostat",
        }

print(f"  {len(eurostat)} countries from Eurostat")

# ── 2. Process EIA data (US) ──────────────────────────────────────────────

print("Processing EIA electricity prices...")

# Get US national average and state-level for most recent year
us_prices = []
state_prices = {}
with open(DATA / "eia_electricity_prices.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["period"] != "2024":
            continue
        price_cents = float(row["price"])
        price_usd_kwh = price_cents / 100.0
        state = row["stateid"]

        if state == "US":
            us_national = price_usd_kwh
        else:
            state_prices[state] = price_usd_kwh
            us_prices.append(price_usd_kwh)

# Add US as single country entry
eurostat["USA"] = {
    "price_eur_kwh": us_national * EUR_USD,
    "price_usd_kwh": us_national,
    "band": "national_industrial",
    "source": "EIA",
}

# Also compute percentiles for reference
us_arr = np.array(list(state_prices.values()))
print(f"  US national: ${us_national:.4f}/kWh")
print(f"  US states: min=${us_arr.min():.4f} median=${np.median(us_arr):.4f} max=${us_arr.max():.4f}")

# Key DC states
DC_STATES = {"VA": "Virginia", "TX": "Texas", "OR": "Oregon", "WA": "Washington",
             "GA": "Georgia", "OH": "Ohio", "AZ": "Arizona", "NV": "Nevada"}
print("  Key DC states:")
for st, name in DC_STATES.items():
    if st in state_prices:
        print(f"    {st} ({name}): ${state_prices[st]:.4f}/kWh")

# ── 3. Merge and save ─────────────────────────────────────────────────────

print("\nMerging datasets...")

results = []
for iso3, d in eurostat.items():
    results.append({
        "iso3": iso3,
        "price_eur_kwh": round(d["price_eur_kwh"], 4),
        "price_usd_kwh": round(d["price_usd_kwh"], 4),
        "consumption_band": d["band"],
        "source": d["source"],
    })

results.sort(key=lambda r: r["price_usd_kwh"])

outpath = DATA / "country_electricity_prices.csv"
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys())
    w.writeheader()
    w.writerows(results)

print(f"Saved {len(results)} countries to {outpath}")

# ── 4. Summary ─────────────────────────────────────────────────────────────

print("\nCheapest 10 (USD/kWh, excl. tax, large industrial):")
for r in results[:10]:
    print(f"  {r['iso3']}  ${r['price_usd_kwh']:.4f}  ({r['source']}, {r['consumption_band']})")

print("\nMost expensive 10:")
for r in results[-10:]:
    print(f"  {r['iso3']}  ${r['price_usd_kwh']:.4f}  ({r['source']}, {r['consumption_band']})")

# ── 5. Save US state-level data separately ─────────────────────────────────

state_results = []
with open(DATA / "eia_electricity_prices.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["period"] != "2024":
            continue
        if row["stateid"] == "US":
            continue
        price_usd = float(row["price"]) / 100.0
        state_results.append({
            "state": row["stateid"],
            "state_name": row["stateDescription"],
            "price_usd_kwh": round(price_usd, 4),
            "price_eur_kwh": round(price_usd * EUR_USD, 4),
        })

state_results.sort(key=lambda r: r["price_usd_kwh"])

state_outpath = DATA / "us_state_electricity_prices.csv"
with open(state_outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=state_results[0].keys())
    w.writeheader()
    w.writerows(state_results)

print(f"\nSaved {len(state_results)} US states to {state_outpath}")
