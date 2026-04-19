"""
Step A: Read raw files → data/processed/country_panel.csv

Ingests all raw data files and produces a single flat CSV with one row
per country (85 rows) containing all variables needed for cost computation.
"""

import os
import csv
import pandas as pd
import numpy as np

from .utils import DATA_RAW, DATA_PROCESSED, TT_MARKET_TO_ISO3


# Master list of 85 countries (from calibration_results_v3.csv ordering)
MASTER_85 = [
    "IRN", "TKM", "ETH", "KGZ", "EGY", "DZA", "CAN", "RUS", "ZAF", "XKX",
    "NGA", "TJK", "MNE", "CHN", "QAT", "UKR", "ARG", "COL", "AZE", "NOR",
    "KAZ", "UZB", "FIN", "VNM", "SAU", "BRA", "ARE", "SWE", "IND", "IDN",
    "GEO", "USA", "KEN", "TUR", "BIH", "ISL", "GBR", "BLR", "AUS", "NZL",
    "MAR", "MEX", "FRA", "ARM", "CHL", "POL", "LVA", "PRT", "MLT", "MYS",
    "PHL", "ISR", "ESP", "THA", "BEL", "SRB", "PAK", "LUX", "NLD", "EST",
    "KOR", "MDA", "DNK", "LTU", "MKD", "GHA", "SVN", "ALB", "ROU", "DEU",
    "GRC", "BGR", "SVK", "AUT", "ITA", "JPN", "CZE", "CHE", "HUN", "SGP",
    "CYP", "SEN", "HRV", "IRL", "GRL",
]

# Standardized country names keyed by ISO3
COUNTRY_NAMES = {
    "IRN": "Iran", "TKM": "Turkmenistan", "ETH": "Ethiopia",
    "KGZ": "Kyrgyzstan", "EGY": "Egypt", "DZA": "Algeria",
    "CAN": "Canada", "RUS": "Russia", "ZAF": "South Africa",
    "XKX": "Kosovo", "NGA": "Nigeria", "TJK": "Tajikistan",
    "MNE": "Montenegro", "CHN": "China", "QAT": "Qatar",
    "UKR": "Ukraine", "ARG": "Argentina", "COL": "Colombia",
    "AZE": "Azerbaijan", "NOR": "Norway", "KAZ": "Kazakhstan",
    "UZB": "Uzbekistan", "FIN": "Finland", "VNM": "Vietnam",
    "SAU": "Saudi Arabia", "BRA": "Brazil", "ARE": "UAE",
    "SWE": "Sweden", "IND": "India", "IDN": "Indonesia",
    "GEO": "Georgia", "USA": "United States", "KEN": "Kenya",
    "TUR": "Turkey", "BIH": "Bosnia and Herz.", "ISL": "Iceland",
    "GBR": "United Kingdom", "BLR": "Belarus", "AUS": "Australia",
    "NZL": "New Zealand", "MAR": "Morocco", "MEX": "Mexico",
    "FRA": "France", "ARM": "Armenia", "CHL": "Chile",
    "POL": "Poland", "LVA": "Latvia", "PRT": "Portugal",
    "MLT": "Malta", "MYS": "Malaysia", "PHL": "Philippines",
    "ISR": "Israel", "ESP": "Spain", "THA": "Thailand",
    "BEL": "Belgium", "SRB": "Serbia", "PAK": "Pakistan",
    "LUX": "Luxembourg", "NLD": "Netherlands", "EST": "Estonia",
    "KOR": "South Korea", "MDA": "Moldova", "DNK": "Denmark",
    "LTU": "Lithuania", "MKD": "North Macedonia", "GHA": "Ghana",
    "SVN": "Slovenia", "ALB": "Albania", "ROU": "Romania",
    "DEU": "Germany", "GRC": "Greece", "BGR": "Bulgaria",
    "SVK": "Slovakia", "AUT": "Austria", "ITA": "Italy",
    "JPN": "Japan", "CZE": "Czechia", "CHE": "Switzerland",
    "HUN": "Hungary", "SGP": "Singapore", "CYP": "Cyprus",
    "SEN": "Senegal", "HRV": "Croatia", "IRL": "Ireland",
    "GRL": "Greenland",
}


def _load_electricity_prices():
    """Load electricity prices from non_european_prices.csv (master file).

    This file contains the complete price list for all 85 countries,
    compiled from Eurostat, EIA, and manual research.
    Returns dict: iso3 → price in $/kWh.
    """
    path = os.path.join(DATA_RAW, "electricity", "non_european_prices.csv")
    prices = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iso = row["iso3"].strip()
            p = float(row["price_usd_kwh"])
            prices[iso] = p
    return prices


def _load_cost_recovery_prices():
    """Load cost-recovery electricity prices for 13 subsidized countries.
    Returns dict: iso3 → price in $/kWh.
    """
    path = os.path.join(DATA_RAW, "electricity", "cost_recovery_prices.csv")
    cr = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iso = row["iso3"].strip()
            cr[iso] = float(row["p_E_cr_usd_kwh"])
    return cr


def _load_temperatures():
    """Load peak summer temperatures.
    Returns dict: iso3 → temperature in °C.
    """
    path = os.path.join(DATA_RAW, "climate", "temperatures.csv")
    temps = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iso = row["iso3"].strip()
            temps[iso] = float(row["temp_summer_peak_C"])
    return temps


def _load_tt_construction():
    """Load Turner & Townsend DCCI 2025 construction costs.
    Aggregates multiple cities per country (average).
    Returns dict: iso3 → $/W.
    """
    path = os.path.join(DATA_RAW, "construction", "tt_construction_2025.csv")
    city_data = {}  # iso3 → list of $/W values
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            market = row["market"].strip()
            iso = TT_MARKET_TO_ISO3.get(market)
            if iso is None:
                continue  # skip markets not in our 85 (e.g., Montevideo→URY)
            usd = float(row["usd_per_watt"])
            city_data.setdefault(iso, []).append(usd)
    # Average across cities for each country
    return {iso: sum(vals) / len(vals) for iso, vals in city_data.items()}


def _load_construction_regressors():
    """Load GDP per capita, population, urban share, seismic zones, WB regions.
    Returns dict: iso3 → dict of regressor values.
    """
    regressors = {}

    # GDP per capita
    path = os.path.join(DATA_RAW, "construction_regressors", "wdi_gdp_pc.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            val = row.get("gdp_pcap_ppp_2023", "").strip()
            if val:
                regressors.setdefault(iso, {})["gdp_pc"] = float(val)

    # Population
    path = os.path.join(DATA_RAW, "construction_regressors", "wdi_population.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            val = row.get("population_2023", "").strip()
            if val:
                regressors.setdefault(iso, {})["population"] = float(val)

    # Urban share
    path = os.path.join(DATA_RAW, "construction_regressors", "wdi_urban_share.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            val = row.get("urban_share_pct", "").strip()
            if val:
                regressors.setdefault(iso, {})["urban_share"] = float(val)

    # Seismic zones
    path = os.path.join(DATA_RAW, "construction_regressors", "seismic_zones.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            regressors.setdefault(iso, {})["seismic"] = int(row["seismic_high"])

    # WB regions
    path = os.path.join(DATA_RAW, "construction_regressors", "wb_regions.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            regressors.setdefault(iso, {})["wb_region"] = row["region"].strip()

    return regressors


def _load_governance():
    """Load WGI Rule of Law percentile (G).
    Returns dict: iso3 → G ∈ [0, 1].
    """
    path = os.path.join(DATA_RAW, "governance", "wgi_rule_of_law.csv")
    gov = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            gov[iso] = float(row["G_RoL"])
    return gov


def _load_grid_reliability():
    """Load grid reliability index (R).
    Returns dict: iso3 → R ∈ [0, 1].
    """
    path = os.path.join(DATA_RAW, "governance", "enterprise_surveys_grid.csv")
    grid = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            grid[iso] = float(row["R_grid"])
    return grid


def _load_capacity():
    """Load DC capacity (MW).
    Returns dict: iso3 → capacity_mw.
    """
    path = os.path.join(DATA_RAW, "capacity", "dc_capacity_mw.csv")
    cap = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            cap[iso] = float(row["capacity_mw"])
    return cap


def _load_demand_shares():
    """Load demand shares.
    Returns dict: iso3 → ω_k.
    """
    path = os.path.join(DATA_RAW, "demand", "demand_shares.csv")
    shares = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso = row["iso3"].strip()
            shares[iso] = float(row["demand_share"])
    return shares


def ingest_all():
    """Load all raw data and produce the country panel DataFrame.

    Returns:
        pd.DataFrame with 85 rows, indexed by ISO3, with all required columns.
    """
    print("    Loading electricity prices...")
    prices = _load_electricity_prices()
    cr_prices = _load_cost_recovery_prices()

    print("    Loading temperatures...")
    temps = _load_temperatures()

    print("    Loading T&T construction costs...")
    tt_costs = _load_tt_construction()

    print("    Loading construction regressors...")
    regressors = _load_construction_regressors()

    print("    Loading governance (G)...")
    governance = _load_governance()

    print("    Loading grid reliability (R)...")
    grid_rel = _load_grid_reliability()

    print("    Loading DC capacity...")
    capacity = _load_capacity()

    print("    Loading demand shares...")
    demand = _load_demand_shares()

    # Build panel
    rows = []
    for iso in MASTER_85:
        name = COUNTRY_NAMES.get(iso, iso)
        p_E_raw = prices.get(iso)
        if p_E_raw is None:
            raise ValueError(f"Missing electricity price for {iso}")

        theta = temps.get(iso)
        if theta is None:
            raise ValueError(f"Missing temperature for {iso}")

        # Cost-recovery price
        is_subsidized = iso in cr_prices
        p_E_cr = cr_prices[iso] if is_subsidized else p_E_raw

        # Construction: T&T if available, otherwise leave NaN for regression
        constr = tt_costs.get(iso, np.nan)
        constr_source = "T&T" if iso in tt_costs else "predicted"

        # Governance
        G = governance.get(iso)
        if G is None:
            raise ValueError(f"Missing governance G for {iso}")

        R = grid_rel.get(iso)
        if R is None:
            raise ValueError(f"Missing grid reliability R for {iso}")

        # Capacity (default 5.0 MW if missing)
        cap = capacity.get(iso, 5.0)

        # Demand share
        omega = demand.get(iso, 0.0)

        # Construction regressors
        reg = regressors.get(iso, {})

        rows.append({
            "country_iso3": iso,
            "country_name": name,
            "p_E_raw": p_E_raw,
            "p_E_cr": p_E_cr,
            "is_subsidized": is_subsidized,
            "theta": theta,
            "construction_per_watt": constr,
            "construction_source": constr_source,
            "G_governance": G,
            "R_grid": R,
            "capacity_mw": cap,
            "demand_share": omega,
            "gdp_pc": reg.get("gdp_pc", np.nan),
            "population": reg.get("population", np.nan),
            "urban_share": reg.get("urban_share", np.nan),
            "seismic": reg.get("seismic", 0),
            "wb_region": reg.get("wb_region", ""),
        })

    panel = pd.DataFrame(rows)
    panel = panel.set_index("country_iso3", drop=False)

    # Normalize demand shares to sum to 1
    total = panel["demand_share"].sum()
    if total > 0:
        panel["demand_share"] = panel["demand_share"] / total

    # Save to processed
    os.makedirs(DATA_PROCESSED, exist_ok=True)
    out_path = os.path.join(DATA_PROCESSED, "country_panel.csv")
    panel.to_csv(out_path, index=False)
    print(f"    Saved {len(panel)} countries to {out_path}")

    return panel
