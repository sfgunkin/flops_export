"""
Process WonderNetwork ping data into country-pair average latencies.

Inputs:
  - wondernetwork_servers.csv: server locations with country
  - wondernetwork_pings.csv.gz: ~3M bilateral ping measurements

Output: country_pair_latency.csv with columns:
  country_from, country_to, iso3_from, iso3_to, avg_ms, min_ms, max_ms, n_pings
"""

import csv
import gzip
import pathlib
from collections import defaultdict
import numpy as np

DATA = pathlib.Path(r"F:\onedrive\__documents\papers\FLOPsExport\Data")

# ── 1. Country name to ISO3 mapping ────────────────────────────────────────
# WonderNetwork uses full country names; map to ISO3

COUNTRY_TO_ISO3 = {
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "Angola": "AGO",
    "Argentina": "ARG", "Armenia": "ARM", "Australia": "AUS", "Austria": "AUT",
    "Azerbaijan": "AZE", "Bahrain": "BHR", "Bangladesh": "BGD", "Belarus": "BLR",
    "Belgium": "BEL", "Bolivia": "BOL", "Bosnia and Herzegovina": "BIH",
    "Brazil": "BRA", "Brunei": "BRN", "Bulgaria": "BGR", "Cambodia": "KHM",
    "Cameroon": "CMR", "Canada": "CAN", "Chile": "CHL", "China": "CHN",
    "Colombia": "COL", "Costa Rica": "CRI", "Croatia": "HRV", "Cuba": "CUB",
    "Cyprus": "CYP", "Czech Republic": "CZE", "Czechia": "CZE",
    "Denmark": "DNK", "Dominican Republic": "DOM",
    "Ecuador": "ECU", "Egypt": "EGY", "El Salvador": "SLV", "Estonia": "EST",
    "Ethiopia": "ETH", "Finland": "FIN", "France": "FRA", "Georgia": "GEO",
    "Germany": "DEU", "Ghana": "GHA", "Greece": "GRC", "Guatemala": "GTM",
    "Honduras": "HND", "Hong Kong": "HKG", "Hungary": "HUN", "Iceland": "ISL",
    "India": "IND", "Indonesia": "IDN", "Iran": "IRN", "Iraq": "IRQ",
    "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA", "Jamaica": "JAM",
    "Japan": "JPN", "Jordan": "JOR", "Kazakhstan": "KAZ", "Kenya": "KEN",
    "Kosovo": "XKX", "Kuwait": "KWT", "Kyrgyzstan": "KGZ", "Laos": "LAO",
    "Latvia": "LVA", "Lebanon": "LBN", "Libya": "LBY", "Lithuania": "LTU",
    "Luxembourg": "LUX", "Macau": "MAC", "Madagascar": "MDG",
    "Malaysia": "MYS", "Malta": "MLT", "Mexico": "MEX", "Moldova": "MDA",
    "Mongolia": "MNG", "Montenegro": "MNE", "Morocco": "MAR", "Mozambique": "MOZ",
    "Myanmar": "MMR", "Nepal": "NPL", "Netherlands": "NLD", "New Zealand": "NZL",
    "Nicaragua": "NIC", "Nigeria": "NGA", "North Macedonia": "MKD",
    "Norway": "NOR", "Oman": "OMN", "Pakistan": "PAK", "Palestine": "PSE",
    "Panama": "PAN", "Paraguay": "PRY", "Peru": "PER", "Philippines": "PHL",
    "Poland": "POL", "Portugal": "PRT", "Puerto Rico": "PRI", "Qatar": "QAT",
    "Romania": "ROU", "Russia": "RUS", "Rwanda": "RWA", "Saudi Arabia": "SAU",
    "Senegal": "SEN", "Serbia": "SRB", "Singapore": "SGP", "Slovakia": "SVK",
    "Slovenia": "SVN", "South Africa": "ZAF", "South Korea": "KOR",
    "Spain": "ESP", "Sri Lanka": "LKA", "Sudan": "SDN", "Sweden": "SWE",
    "Switzerland": "CHE", "Taiwan": "TWN", "Tanzania": "TZA",
    "Thailand": "THA", "Tunisia": "TUN", "Turkey": "TUR",
    "Turkiye": "TUR", "Uganda": "UGA", "Ukraine": "UKR",
    "United Arab Emirates": "ARE", "United Kingdom": "GBR",
    "United States": "USA", "Uruguay": "URY", "Uzbekistan": "UZB",
    "Venezuela": "VEN", "Vietnam": "VNM", "Zambia": "ZMB", "Zimbabwe": "ZWE",
}

# ── 2. Load servers ────────────────────────────────────────────────────────

print("Loading servers...")
servers = {}
unmapped_countries = set()

with open(DATA / "wondernetwork_servers.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sid = row["id"]
        country = row["country"]
        iso3 = COUNTRY_TO_ISO3.get(country)
        if iso3 is None:
            unmapped_countries.add(country)
        servers[sid] = {
            "name": row["name"],
            "city": row["title"],
            "country": country,
            "iso3": iso3,
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"]),
        }

print(f"  {len(servers)} servers in {len(set(s['country'] for s in servers.values()))} countries")
if unmapped_countries:
    print(f"  WARNING: unmapped countries: {unmapped_countries}")

# ── 3. Process pings ──────────────────────────────────────────────────────

print("Processing pings (this may take a minute)...")

# Accumulate: (iso3_from, iso3_to) -> list of avg latencies
pair_data = defaultdict(list)
skipped = 0
processed = 0

with gzip.open(DATA / "wondernetwork_pings.csv.gz", "rt") as f:
    reader = csv.DictReader(f)
    for row in reader:
        src = row["source"]
        dst = row["destination"]
        avg_ms = row["avg"]

        # Skip if server not found or no ISO3
        if src not in servers or dst not in servers:
            skipped += 1
            continue
        iso_from = servers[src]["iso3"]
        iso_to = servers[dst]["iso3"]
        if iso_from is None or iso_to is None:
            skipped += 1
            continue

        try:
            lat = float(avg_ms)
        except (ValueError, TypeError):
            skipped += 1
            continue

        if lat <= 0 or lat > 2000:  # sanity filter
            skipped += 1
            continue

        pair_data[(iso_from, iso_to)].append(lat)
        processed += 1

        if processed % 500000 == 0:
            print(f"  ... {processed:,} pings processed")

print(f"  {processed:,} valid pings, {skipped:,} skipped")
print(f"  {len(pair_data):,} unique country pairs")

# ── 4. Aggregate to country-pair averages ──────────────────────────────────

print("Aggregating to country-pair averages...")

# Build ISO3 -> country name lookup
iso3_to_name = {}
for s in servers.values():
    if s["iso3"]:
        iso3_to_name[s["iso3"]] = s["country"]

results = []
for (iso_from, iso_to), latencies in pair_data.items():
    arr = np.array(latencies)
    results.append({
        "iso3_from": iso_from,
        "iso3_to": iso_to,
        "country_from": iso3_to_name.get(iso_from, iso_from),
        "country_to": iso3_to_name.get(iso_to, iso_to),
        "avg_ms": round(np.mean(arr), 2),
        "median_ms": round(np.median(arr), 2),
        "min_ms": round(np.min(arr), 2),
        "p95_ms": round(np.percentile(arr, 95), 2),
        "max_ms": round(np.max(arr), 2),
        "n_pings": len(arr),
    })

results.sort(key=lambda r: (r["iso3_from"], r["avg_ms"]))

# ── 5. Save full pair data ─────────────────────────────────────────────────

outpath = DATA / "country_pair_latency.csv"
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys())
    w.writeheader()
    w.writerows(results)

print(f"\nSaved {len(results)} country pairs to {outpath}")

# ── 6. Summary statistics ─────────────────────────────────────────────────

# Domestic latency (same country)
domestic = [r for r in results if r["iso3_from"] == r["iso3_to"]]
cross_border = [r for r in results if r["iso3_from"] != r["iso3_to"]]

print(f"\nDomestic pairs: {len(domestic)}")
if domestic:
    avg_domestic = np.mean([r["avg_ms"] for r in domestic])
    print(f"  Mean domestic latency: {avg_domestic:.1f} ms")

print(f"Cross-border pairs: {len(cross_border)}")
if cross_border:
    avg_cross = np.mean([r["avg_ms"] for r in cross_border])
    print(f"  Mean cross-border latency: {avg_cross:.1f} ms")

# Pairs above/below the 40ms threshold (from the model)
THRESHOLD = 40
below = sum(1 for r in cross_border if r["avg_ms"] <= THRESHOLD)
above = sum(1 for r in cross_border if r["avg_ms"] > THRESHOLD)
print(f"\nCross-border pairs below {THRESHOLD}ms threshold: {below} ({100 * below / len(cross_border):.0f}%)")
print(f"Cross-border pairs above {THRESHOLD}ms threshold: {above} ({100 * above / len(cross_border):.0f}%)")

# Show some examples near the threshold
near = sorted([r for r in cross_border if 30 <= r["avg_ms"] <= 50],
              key=lambda r: r["avg_ms"])
print(f"\nPairs near the {THRESHOLD}ms threshold:")
for r in near[:10]:
    print(f"  {r['iso3_from']}->{r['iso3_to']}  {r['avg_ms']:>6.1f} ms  ({r['country_from']} -> {r['country_to']})")
