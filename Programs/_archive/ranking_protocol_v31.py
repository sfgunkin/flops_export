"""
ranking_protocol_v31.py — FLOPs Export Model Rankings
Computes rankings for 3 specifications:
  (1) Raw       — raw electricity costs, no sovereignty
  (2) Cost-Recovery — subsidy-adjusted costs, no sovereignty
  (3) Bilateral — CR costs + bilateral sovereignty premia

Outputs:
  rankings_v31.csv       — country rankings for all 3 specs
  diagnostics_v31.txt    — parameter summary and diagnostics

Standalone: no pandas, requests, or python-docx.
"""

import csv
from pathlib import Path
from datetime import datetime

# ======================================================================
# Paths
# ======================================================================
BASE = Path(r"F:\onedrive\__documents\papers\FLOPsExport")
OUT_CSV  = BASE / "rankings_v31.csv"
OUT_DIAG = BASE / "diagnostics_v31.txt"
LATENCY_CSV = BASE / "Data" / "country_pair_latency.csv"

# ======================================================================
# Parameters
# ======================================================================
PHI         = 1.08
DELTA_PUE   = 0.015
THETA_REF   = 15.0
GAMMA       = 0.700          # kW per GPU
GPU_PRICE   = 25_000
GPU_LIFE    = 3
GPU_UTIL    = 0.70
H_YR        = 365.25 * 24    # 8766 hours
DC_LIFE     = 15
ETA         = 0.15           # network cost ($/GPU-hr)
ALPHA       = 0.50           # training share of demand
Q_TOTAL     = 60_000_000_000 # total GPU-hours demanded globally
TAU         = 0.0008         # latency sensitivity
L_BAR       = 200.0          # max acceptable latency (ms)
ALPHA_GEO   = 0.05           # geopolitical distance weight
ALPHA_REG   = 0.025          # regulatory incompatibility weight
LAMBDA_UNIFORM = 0.10        # kept for robustness reference only
RHO         = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL)  # ~$1.358/hr

GPU_EXPORT_CONTROLLED = {'CHN'}
GPU_CONTROL_ALPHA3    = 0.10  # partial GPU restriction for China

# ======================================================================
# Cost functions
# ======================================================================
def compute_pue(theta):
    return PHI + DELTA_PUE * max(0, theta - THETA_REF)

def compute_cost(p_E, theta, construction_per_watt):
    pue = compute_pue(theta)
    energy  = pue * GAMMA * p_E
    hardware = RHO
    network  = ETA
    constr   = construction_per_watt * GAMMA * 1000 / (DC_LIFE * H_YR)
    return energy + hardware + network + constr

# ======================================================================
# 85-country raw data
# (iso3, country, p_E_raw, theta, construction_per_watt, capacity_mw)
# ======================================================================
RAW_DATA = [
    ('IRN', 'Iran',                        0.005,  31.2,  8.50,    10),
    ('TKM', 'Turkmenistan',                0.01,   32.2,  9.24,     5),
    ('ETH', 'Ethiopia',                    0.03,   26.5,  8.08,    10),
    ('KGZ', 'Kyrgyzstan',                  0.038,  13.3,  7.83,     5),
    ('EGY', 'Egypt',                       0.038,  31.7,  7.63,   150),
    ('DZA', 'Algeria',                     0.033,  35.8,  8.48,    25),
    ('CAN', 'Canada',                      0.045,  14.6,  9.39,  3200),
    ('RUS', 'Russia',                      0.04,   16.9, 10.36,  2000),
    ('ZAF', 'South Africa',               0.04,   23.5, 10.20,   250),
    ('XKX', 'Kosovo',                      0.0468, 21.0,  9.48,     5),
    ('NGA', 'Nigeria',                     0.042,  31.4, 10.50,   100),
    ('TJK', 'Tajikistan',                  0.074,  16.8,  7.32,     5),
    ('MNE', 'Montenegro',                  0.0508, 21.7, 10.28,     5),
    ('CHN', 'China',                       0.079,  20.9,  6.12, 31900),
    ('QAT', 'Qatar',                       0.036,  36.1, 11.86,    80),
    ('UKR', 'Ukraine',                     0.0568, 22.5,  9.86,   175),
    ('ARG', 'Argentina',                   0.06,   22.3, 10.10,   150),
    ('COL', 'Colombia',                    0.075,  25.5,  7.49,   150),
    ('AZE', 'Azerbaijan',                  0.062,  24.4,  9.77,    10),
    ('NOR', 'Norway',                      0.0541, 14.5, 12.41,   400),
    ('KAZ', 'Kazakhstan',                  0.066,  24.9,  9.53,   100),
    ('UZB', 'Uzbekistan',                  0.071,  29.9,  8.37,    25),
    ('FIN', 'Finland',                     0.0571, 16.4, 12.29,   350),
    ('VNM', 'Vietnam',                     0.073,  28.0,  8.76,   250),
    ('SAU', 'Saudi Arabia',                0.053,  36.0, 11.34,   400),
    ('BRA', 'Brazil',                      0.063,  27.3, 10.75,  1200),
    ('ARE', 'United Arab Emirates',        0.065,  37.1,  9.24,   500),
    ('SWE', 'Sweden',                      0.0682, 15.2, 12.29,   500),
    ('IND', 'India',                       0.09,   30.2,  6.64,  3600),
    ('IDN', 'Indonesia',                   0.067,  26.4, 11.21,   500),
    ('GEO', 'Georgia',                     0.0911, 19.4,  9.58,    15),
    ('USA', 'United States',               0.0813, 22.9, 10.78, 53700),
    ('KEN', 'Kenya',                       0.088,  27.4,  9.74,    60),
    ('TUR', 'Turkey',                      0.086,  24.4, 10.57,   350),
    ('BIH', 'Bosnia and Herzegovina',      0.0985, 21.6,  9.17,    10),
    ('ISL', 'Iceland',                     0.0895,  8.7, 12.47,    60),
    ('GBR', 'United Kingdom',              0.0971, 15.9, 11.88,  2590),
    ('BLR', 'Belarus',                     0.099,  19.8, 10.91,    35),
    ('AUS', 'Australia',                   0.09,   28.8, 10.68,  2670),
    ('NZL', 'New Zealand',                 0.095,  15.9, 12.30,   250),
    ('MAR', 'Morocco',                     0.108,  28.5,  7.82,    50),
    ('MEX', 'Mexico',                      0.095,  26.6, 10.40,   900),
    ('FRA', 'France',                      0.1024, 21.0, 10.43,  1400),
    ('ARM', 'Armenia',                     0.111,  19.8,  9.76,    10),
    ('CHL', 'Chile',                       0.13,   13.4,  8.61,   200),
    ('POL', 'Poland',                      0.1188, 19.7,  9.16,   600),
    ('LVA', 'Latvia',                      0.1099, 18.4, 10.92,    80),
    ('PRT', 'Portugal',                    0.1089, 22.9, 10.25,   100),
    ('MLT', 'Malta',                       0.1105, 27.0,  9.40,    20),
    ('MYS', 'Malaysia',                    0.099,  26.9, 11.37,   500),
    ('PHL', 'Philippines',                 0.115,  27.8,  8.80,   200),
    ('ISR', 'Israel',                      0.108,  28.2, 10.09,   300),
    ('ESP', 'Spain',                       0.1131, 24.9, 10.04,   720),
    ('THA', 'Thailand',                    0.108,  29.3, 10.03,   300),
    ('BEL', 'Belgium',                     0.1252, 19.0,  9.97,   400),
    ('SRB', 'Serbia',                      0.1201, 23.2, 10.15,    40),
    ('PAK', 'Pakistan',                    0.134,  29.9,  6.57,    50),
    ('LUX', 'Luxembourg',                  0.1277, 18.0, 10.99,    70),
    ('NLD', 'Netherlands',                 0.1296, 18.9, 10.81,  1800),
    ('EST', 'Estonia',                     0.1288, 18.2, 11.19,    50),
    ('KOR', 'South Korea',                 0.125,  26.0, 10.07,   850),
    ('MDA', 'Moldova',                     0.1348, 24.2,  9.21,    20),
    ('DNK', 'Denmark',                     0.1293, 17.2, 12.02,   300),
    ('LTU', 'Lithuania',                   0.134,  18.8, 10.97,    55),
    ('MKD', 'North Macedonia',             0.1352, 24.0,  9.79,    18),
    ('GHA', 'Ghana',                       0.12,   30.7, 10.80,    15),
    ('SVN', 'Slovenia',                    0.147,  21.7, 10.17,    40),
    ('ALB', 'Albania',                     0.1474, 23.7,  9.55,     5),
    ('ROU', 'Romania',                     0.1564, 22.1,  9.24,   100),
    ('DEU', 'Germany',                     0.1552, 19.0, 11.54,  1955),
    ('GRC', 'Greece',                      0.1652, 26.1,  7.84,    50),
    ('BGR', 'Bulgaria',                    0.1546, 23.9, 10.31,    75),
    ('SVK', 'Slovakia',                    0.1644, 20.9, 10.02,    40),
    ('AUT', 'Austria',                     0.1595, 18.6, 11.81,   250),
    ('ITA', 'Italy',                       0.162,  24.0,  9.79,   850),
    ('JPN', 'Japan',                       0.135,  25.2, 14.64,  2400),
    ('CZE', 'Czechia',                     0.1723, 19.1, 10.93,   130),
    ('CHE', 'Switzerland',                 0.16,   15.7, 14.24,   500),
    ('HUN', 'Hungary',                     0.1759, 23.6, 10.73,    50),
    ('SGP', 'Singapore',                   0.145,  28.5, 14.53,  1130),
    ('CYP', 'Cyprus',                      0.185,  28.0, 10.29,    20),
    ('SEN', 'Senegal',                     0.18,   32.4, 10.50,    10),
    ('HRV', 'Croatia',                     0.2057, 23.7,  9.77,    30),
    ('IRL', 'Ireland',                     0.228,  15.3, 10.05,  1260),
    ('GRL', 'Greenland',                   0.263,  -3.1, 11.12,     5),
]

# ======================================================================
# Subsidy adjustments (cost-recovery electricity prices)
# ======================================================================
SUBSIDY_ADJ = {
    'IRN': 0.085,
    'TKM': 0.070,
    'DZA': 0.065,
    'EGY': 0.080,
    'UZB': 0.090,
    'QAT': 0.100,
    'SAU': 0.100,
    'ARE': 0.095,
    'RUS': 0.065,
    'KAZ': 0.085,
    'NGA': 0.080,
    'ZAF': 0.095,
    'ETH': 0.050,
}

# ======================================================================
# Country classifications
# ======================================================================
DEVELOPING = {
    'CHN', 'KGZ', 'XKX', 'MNE', 'ETH', 'VNM', 'IND', 'KEN', 'ARE',
    'EGY', 'DZA', 'UZB', 'TJK', 'TKM', 'ALB', 'MKD', 'GEO', 'ARM',
    'MDA', 'UKR', 'BIH', 'SRB', 'IDN', 'MYS', 'PHL', 'THA', 'COL',
    'MEX', 'BRA', 'ARG', 'CHL', 'NGA', 'ZAF', 'MAR', 'SEN', 'PAK',
}

SANCTIONED = {'IRN', 'RUS', 'BLR', 'TKM'}

# ======================================================================
# Bloc system for bilateral sovereignty
# ======================================================================
BLOC_WESTERN = {
    'USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'ESP', 'PRT', 'NLD', 'BEL',
    'LUX', 'AUT', 'CHE', 'IRL', 'DNK', 'NOR', 'SWE', 'FIN', 'ISL', 'GRC',
    'CZE', 'POL', 'HUN', 'SVK', 'SVN', 'EST', 'LVA', 'LTU', 'HRV', 'BGR',
    'ROU', 'CYP', 'MLT', 'JPN', 'KOR', 'AUS', 'NZL', 'ISR',
}
BLOC_CHINA = {'CHN', 'RUS', 'BLR', 'PRK', 'SYR', 'IRN', 'VEN', 'CUB', 'NIC', 'MMR'}

def get_bloc(iso):
    if iso in BLOC_WESTERN:
        return 'W'
    if iso in BLOC_CHINA:
        return 'C'
    return 'N'

BLOC_DISTANCE = {
    ('W','W'): 0.00, ('W','C'): 0.95, ('C','W'): 0.95,
    ('W','N'): 0.40, ('N','W'): 0.40, ('C','C'): 0.00,
    ('C','N'): 0.55, ('N','C'): 0.55, ('N','N'): 0.20,
}

# ======================================================================
# Regulatory compatibility groups
# ======================================================================
EU_MEMBERS = {
    'AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA',
    'DEU','GRC','HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD',
    'POL','PRT','ROU','SVK','SVN','ESP','SWE',
}
APEC_CBPR = {'AUS','CAN','JPN','KOR','MEX','PHL','SGP','USA'}
DEPA = {'SGP','CHL','NZL'}

def reg_compatible(iso_i, iso_j):
    """R_ij = 1 if both in same regulatory group, else 0."""
    if iso_i in EU_MEMBERS and iso_j in EU_MEMBERS:
        return 1
    if iso_i in APEC_CBPR and iso_j in APEC_CBPR:
        return 1
    if iso_i in DEPA and iso_j in DEPA:
        return 1
    return 0

def compute_lambda(iso_buyer, iso_seller):
    """Bilateral sovereignty premium lambda_ij."""
    # Sanctions check
    if iso_buyer in SANCTIONED or iso_seller in SANCTIONED:
        # Same-bloc sanctioned can trade with each other
        b_buyer = get_bloc(iso_buyer)
        b_seller = get_bloc(iso_seller)
        if iso_buyer in SANCTIONED and iso_seller in SANCTIONED and b_buyer == b_seller:
            pass  # allow
        else:
            return float('inf')
    # GPU export control: China faces partial restriction as seller
    gpu_penalty = 0.0
    if iso_seller in GPU_EXPORT_CONTROLLED:
        gpu_penalty = GPU_CONTROL_ALPHA3
    G_ij = BLOC_DISTANCE[(get_bloc(iso_buyer), get_bloc(iso_seller))]
    R_ij = reg_compatible(iso_buyer, iso_seller)
    lam = ALPHA_GEO * G_ij + ALPHA_REG * (1 - R_ij) + gpu_penalty
    return lam

# ======================================================================
# Load latency data
# ======================================================================
def load_latency():
    """Load country-pair latency from CSV. Returns dict[(from,to)] -> avg_ms."""
    latency = {}
    try:
        with open(LATENCY_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iso_from = row['iso3_from'].strip()
                iso_to   = row['iso3_to'].strip()
                avg_ms   = float(row['avg_ms'])
                latency[(iso_from, iso_to)] = avg_ms
    except FileNotFoundError:
        pass
    return latency

# ======================================================================
# Build country records
# ======================================================================
def build_countries():
    """Build list of country dicts with computed costs."""
    countries = []
    for iso, name, p_E_raw, theta, cpw, cap_mw in RAW_DATA:
        p_E_cr = SUBSIDY_ADJ.get(iso, p_E_raw)
        c_raw = compute_cost(p_E_raw, theta, cpw)
        c_cr  = compute_cost(p_E_cr, theta, cpw)
        # Capacity in GPU-hours per year
        cap_gpuhrs = cap_mw * (1000 / GAMMA) * H_YR * GPU_UTIL
        countries.append({
            'iso3': iso,
            'country': name,
            'p_E_raw': p_E_raw,
            'p_E_cr': p_E_cr,
            'theta': theta,
            'cpw': cpw,
            'capacity_mw': cap_mw,
            'cap_gpuhrs': cap_gpuhrs,
            'c_raw': c_raw,
            'c_cr': c_cr,
            'developing': iso in DEVELOPING,
        })
    return countries

# ======================================================================
# Equilibrium solver (capacity-constrained clearing-price)
# ======================================================================
def solve_equilibrium(countries, cost_key, use_bilateral=False):
    """
    Capacity-constrained clearing-price model.

    For non-bilateral specs (lambda=0):
      - Build supply stack sorted by cost
      - Find clearing price where cumulative capacity >= demanded imports
      - Countries with cost <= clearing price export; others import

    For bilateral spec:
      - Each buyer faces different delivered costs from each seller
      - A buyer imports from the cheapest seller j where (1+lambda_jk)*c_j < c_k
      - Exporters are those who supply to at least one buyer

    Returns: dict of {iso3: share} for training exporters,
             set of importing country ISOs,
             clearing price (or None for bilateral)
    """
    total_cap_mw = sum(c['capacity_mw'] for c in countries)
    iso2c = {c['iso3']: c for c in countries}
    isos = [c['iso3'] for c in countries]

    if not use_bilateral:
        # ---- Non-bilateral: uniform supply stack ----
        # Build supply stack sorted by cost
        stack = sorted(countries, key=lambda c: c[cost_key])

        # Iterative clearing: find p_T such that supply >= demand
        MAX_ITER = 50
        p_T = stack[0][cost_key]  # start from cheapest
        converged = False

        for iteration in range(MAX_ITER):
            # Determine importers: countries with cost > p_T
            importers = [c for c in countries if c[cost_key] > p_T]
            if not importers:
                # Everyone is cheaper than clearing price; minimal trade
                p_T = stack[0][cost_key]
                break

            # Total demand for imports
            Q_TX = sum(ALPHA * (c['capacity_mw'] / total_cap_mw) * Q_TOTAL
                       for c in importers)

            # Walk supply stack until cumulative capacity >= Q_TX
            cum_cap = 0.0
            marginal_idx = 0
            for i, s in enumerate(stack):
                if s[cost_key] >= p_T + 1e-12 and i > 0:
                    # Only suppliers with cost <= p_T are in the stack
                    pass
                cum_cap += s['cap_gpuhrs']
                marginal_idx = i
                if cum_cap >= Q_TX:
                    break

            new_p_T = stack[marginal_idx][cost_key]
            if abs(new_p_T - p_T) < 1e-8:
                converged = True
                break
            p_T = new_p_T

        # Final classification
        exporters = {}
        importer_set = set()
        cum_cap = 0.0
        total_export_cap = 0.0

        # Exporters: those on supply stack with cost <= p_T
        export_countries = [c for c in stack if c[cost_key] <= p_T + 1e-8]
        for c in export_countries:
            total_export_cap += c['cap_gpuhrs']

        for c in export_countries:
            share = c['cap_gpuhrs'] / total_export_cap if total_export_cap > 0 else 0
            exporters[c['iso3']] = share

        for c in countries:
            if c['iso3'] not in exporters:
                importer_set.add(c['iso3'])

        return exporters, importer_set, p_T

    else:
        # ---- Bilateral sovereignty ----
        # Each buyer k looks for cheapest seller j (excluding self) where
        # (1 + lambda_jk) * c_j < c_k
        exporters = {}
        importer_set = set()
        domestic_set = set()

        for k in countries:
            iso_k = k['iso3']
            c_k = k[cost_key]
            best_delivered = c_k  # domestic cost
            best_seller = None

            for j in countries:
                iso_j = j['iso3']
                if iso_j == iso_k:
                    continue
                lam = compute_lambda(iso_k, iso_j)
                if lam == float('inf'):
                    continue
                delivered = (1 + lam) * j[cost_key]
                if delivered < best_delivered:
                    best_delivered = delivered
                    best_seller = iso_j

            if best_seller is not None:
                # k imports from best_seller
                importer_set.add(iso_k)
                if best_seller not in exporters:
                    exporters[best_seller] = 0.0
                omega_k = k['capacity_mw'] / total_cap_mw
                exporters[best_seller] += ALPHA * omega_k * Q_TOTAL
            else:
                domestic_set.add(iso_k)

        # Normalize exporter shares
        total_export = sum(exporters.values()) if exporters else 1.0
        for iso in exporters:
            exporters[iso] = exporters[iso] / total_export

        return exporters, importer_set, None

# ======================================================================
# Inference regime classification
# ======================================================================
def classify_inference(countries, cost_key, training_exporters, latency,
                       use_bilateral=False):
    """
    Determine inference sourcing for each country.
    A country imports inference from j if:
      delivered_cost_j < delivered_cost_domestic
    where delivered includes latency penalty and (for bilateral) lambda.

    Returns dict: iso3 -> 'EE'|'IE'|'DD'|'II'
    """
    iso2c = {c['iso3']: c for c in countries}
    regimes = {}

    has_latency = len(latency) > 0

    for k in countries:
        iso_k = k['iso3']
        c_k = k[cost_key]

        is_training_exporter = iso_k in training_exporters

        if not has_latency:
            # Simplified: EE if training exporter, II if importer, DD otherwise
            if is_training_exporter:
                regimes[iso_k] = 'EE'
            elif iso_k in training_exporters:
                regimes[iso_k] = 'EE'
            else:
                regimes[iso_k] = 'DD'
            continue

        # Domestic inference cost (self-latency)
        lat_kk = latency.get((iso_k, iso_k), 0.0)
        domestic_inf = (1 + TAU * lat_kk) * c_k

        # Check if any supplier can beat domestic
        best_import_cost = domestic_inf
        can_import_inference = False

        for j in countries:
            iso_j = j['iso3']
            if iso_j == iso_k:
                continue
            lat_jk = latency.get((iso_j, iso_k), None)
            if lat_jk is None or lat_jk > L_BAR:
                continue
            c_j = j[cost_key]

            if use_bilateral:
                lam = compute_lambda(iso_k, iso_j)
                if lam == float('inf'):
                    continue
                delivered = (1 + lam) * (1 + TAU * lat_jk) * c_j
            else:
                delivered = (1 + TAU * lat_jk) * c_j

            if delivered < domestic_inf:
                can_import_inference = True
                break

        if is_training_exporter:
            # Training exporter
            if can_import_inference:
                # Exports training but could import inference — still EE
                # (exporter in both senses)
                regimes[iso_k] = 'EE'
            else:
                regimes[iso_k] = 'EE'
        else:
            # Not a training exporter
            # Check if this country can export inference to anyone
            can_export_inference = False
            for m in countries:
                iso_m = m['iso3']
                if iso_m == iso_k:
                    continue
                lat_km = latency.get((iso_k, iso_m), None)
                if lat_km is None or lat_km > L_BAR:
                    continue
                c_m = m[cost_key]
                lat_mm = latency.get((iso_m, iso_m), 0.0)
                domestic_m = (1 + TAU * lat_mm) * c_m

                if use_bilateral:
                    lam = compute_lambda(iso_m, iso_k)
                    if lam == float('inf'):
                        continue
                    delivered = (1 + lam) * (1 + TAU * lat_km) * c_k
                else:
                    delivered = (1 + TAU * lat_km) * c_k

                if delivered < domestic_m:
                    can_export_inference = True
                    break

            if can_export_inference:
                regimes[iso_k] = 'IE'
            elif can_import_inference:
                regimes[iso_k] = 'II'
            else:
                regimes[iso_k] = 'DD'

    return regimes

# ======================================================================
# Apply marks (* for sanctioned, dagger for developing exporters)
# ======================================================================
def apply_marks(iso, regime):
    marks = ''
    if iso in SANCTIONED:
        marks += '*'
    if iso in DEVELOPING and regime in ('EE', 'IE'):
        marks += '\u2020'  # dagger
    return regime + marks

# ======================================================================
# Main
# ======================================================================
def main():
    countries = build_countries()
    latency = load_latency()

    # ---- Spec 1: Raw ----
    exp_raw, imp_raw, pt_raw = solve_equilibrium(countries, 'c_raw', use_bilateral=False)
    regime_raw = classify_inference(countries, 'c_raw', exp_raw, latency,
                                    use_bilateral=False)

    # ---- Spec 2: Cost-Recovery ----
    exp_cr, imp_cr, pt_cr = solve_equilibrium(countries, 'c_cr', use_bilateral=False)
    regime_cr = classify_inference(countries, 'c_cr', exp_cr, latency,
                                   use_bilateral=False)

    # ---- Spec 3: Bilateral Sovereignty ----
    exp_bi, imp_bi, pt_bi = solve_equilibrium(countries, 'c_cr', use_bilateral=True)
    regime_bi = classify_inference(countries, 'c_cr', exp_bi, latency,
                                   use_bilateral=True)

    # Force sanctioned countries to DD under bilateral
    for iso in SANCTIONED:
        if iso in regime_bi:
            regime_bi[iso] = 'DD'

    # ---- Build rankings ----
    # Rank by cost (lower = better rank)
    sorted_raw = sorted(countries, key=lambda c: c['c_raw'])
    sorted_cr  = sorted(countries, key=lambda c: c['c_cr'])

    rank_raw = {c['iso3']: i+1 for i, c in enumerate(sorted_raw)}
    rank_cr  = {c['iso3']: i+1 for i, c in enumerate(sorted_cr)}

    # ---- Write CSV ----
    rows = []
    for c in countries:
        iso = c['iso3']
        r_raw = regime_raw.get(iso, 'DD')
        r_cr  = regime_cr.get(iso, 'DD')
        r_bi  = regime_bi.get(iso, 'DD')
        rows.append({
            'country': c['country'],
            'iso3': iso,
            'developing': 'Y' if c['developing'] else 'N',
            'c_raw': round(c['c_raw'], 4),
            'rank_raw': rank_raw[iso],
            'type_raw': apply_marks(iso, r_raw),
            'c_cr': round(c['c_cr'], 4),
            'rank_cr': rank_cr[iso],
            'type_cr': apply_marks(iso, r_cr),
            'type_bilateral': apply_marks(iso, r_bi),
        })

    # Sort output by rank_raw
    rows.sort(key=lambda r: r['rank_raw'])

    fieldnames = ['country','iso3','developing','c_raw','rank_raw','type_raw',
                  'c_cr','rank_cr','type_cr','type_bilateral']

    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUT_CSV}")

    # ---- Diagnostics ----
    diag_lines = []
    diag_lines.append(f"ranking_protocol_v31.py — Diagnostics")
    diag_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    diag_lines.append("")

    # Parameters
    diag_lines.append("=" * 60)
    diag_lines.append("PARAMETERS")
    diag_lines.append("=" * 60)
    diag_lines.append(f"  PHI           = {PHI}")
    diag_lines.append(f"  DELTA_PUE     = {DELTA_PUE}")
    diag_lines.append(f"  THETA_REF     = {THETA_REF}")
    diag_lines.append(f"  GAMMA         = {GAMMA} kW/GPU")
    diag_lines.append(f"  GPU_PRICE     = ${GPU_PRICE:,}")
    diag_lines.append(f"  GPU_LIFE      = {GPU_LIFE} yr")
    diag_lines.append(f"  GPU_UTIL      = {GPU_UTIL}")
    diag_lines.append(f"  H_YR          = {H_YR}")
    diag_lines.append(f"  RHO           = ${RHO:.4f}/hr")
    diag_lines.append(f"  DC_LIFE       = {DC_LIFE} yr")
    diag_lines.append(f"  ETA           = ${ETA}/hr")
    diag_lines.append(f"  ALPHA         = {ALPHA}")
    diag_lines.append(f"  Q_TOTAL       = {Q_TOTAL:.2e} GPU-hrs")
    diag_lines.append(f"  TAU           = {TAU}")
    diag_lines.append(f"  L_BAR         = {L_BAR} ms")
    diag_lines.append(f"  ALPHA_GEO     = {ALPHA_GEO}")
    diag_lines.append(f"  ALPHA_REG     = {ALPHA_REG}")
    diag_lines.append(f"  GPU_CONTROL   = {GPU_EXPORT_CONTROLLED}, penalty={GPU_CONTROL_ALPHA3}")
    diag_lines.append("")

    # Reference country cost breakdowns
    diag_lines.append("=" * 60)
    diag_lines.append("COST BREAKDOWNS (5 reference countries)")
    diag_lines.append("=" * 60)
    ref_isos = ['CAN', 'FIN', 'IRN', 'KGZ', 'USA']
    iso2c = {c['iso3']: c for c in countries}
    for iso in ref_isos:
        c = iso2c[iso]
        pue = compute_pue(c['theta'])
        energy_raw  = pue * GAMMA * c['p_E_raw']
        energy_cr   = pue * GAMMA * c['p_E_cr']
        constr      = c['cpw'] * GAMMA * 1000 / (DC_LIFE * H_YR)
        diag_lines.append(f"  {c['country']} ({iso}):")
        diag_lines.append(f"    PUE            = {pue:.4f}")
        diag_lines.append(f"    Energy (raw)   = ${energy_raw:.4f}/hr")
        diag_lines.append(f"    Energy (CR)    = ${energy_cr:.4f}/hr")
        diag_lines.append(f"    Hardware (RHO) = ${RHO:.4f}/hr")
        diag_lines.append(f"    Network (ETA)  = ${ETA:.4f}/hr")
        diag_lines.append(f"    Construction   = ${constr:.4f}/hr")
        diag_lines.append(f"    c_raw          = ${c['c_raw']:.4f}/hr")
        diag_lines.append(f"    c_cr           = ${c['c_cr']:.4f}/hr")
        diag_lines.append(f"    Rank (raw)     = {rank_raw[iso]}")
        diag_lines.append(f"    Rank (CR)      = {rank_cr[iso]}")
        diag_lines.append("")

    # Subsidized countries
    diag_lines.append("=" * 60)
    diag_lines.append("SUBSIDY ADJUSTMENTS")
    diag_lines.append("=" * 60)
    for iso, p_cr in sorted(SUBSIDY_ADJ.items()):
        c = iso2c.get(iso)
        if c:
            diag_lines.append(
                f"  {iso} ({c['country']}): p_E {c['p_E_raw']:.3f} -> {p_cr:.3f} "
                f"(cost {c['c_raw']:.4f} -> {c['c_cr']:.4f})")
    diag_lines.append("")

    # Exporter counts
    diag_lines.append("=" * 60)
    diag_lines.append("EXPORTER COUNTS")
    diag_lines.append("=" * 60)
    for spec_name, regimes in [('Raw', regime_raw), ('Cost-Recovery', regime_cr),
                                ('Bilateral', regime_bi)]:
        ee = sum(1 for v in regimes.values() if v == 'EE')
        ie = sum(1 for v in regimes.values() if v == 'IE')
        dd = sum(1 for v in regimes.values() if v == 'DD')
        ii = sum(1 for v in regimes.values() if v == 'II')
        diag_lines.append(f"  {spec_name}: EE={ee}, IE={ie}, DD={dd}, II={ii}")
    diag_lines.append("")

    # Regime changes
    diag_lines.append("=" * 60)
    diag_lines.append("REGIME CHANGES: Raw -> CR -> Bilateral")
    diag_lines.append("=" * 60)
    for c in sorted(countries, key=lambda x: x['iso3']):
        iso = c['iso3']
        r1 = regime_raw.get(iso, '??')
        r2 = regime_cr.get(iso, '??')
        r3 = regime_bi.get(iso, '??')
        if r1 != r2 or r2 != r3:
            diag_lines.append(f"  {iso} ({c['country']}): {r1} -> {r2} -> {r3}")
    diag_lines.append("")

    # Sanctions check
    diag_lines.append("=" * 60)
    diag_lines.append("SANCTIONS CHECK (bilateral spec)")
    diag_lines.append("=" * 60)
    for iso in sorted(SANCTIONED):
        r = regime_bi.get(iso, '??')
        diag_lines.append(f"  {iso}: {r} {'[OK]' if r == 'DD' else '[WARN]'}")
    diag_lines.append("")

    # Capacity utilization
    diag_lines.append("=" * 60)
    diag_lines.append("CAPACITY UTILIZATION")
    diag_lines.append("=" * 60)
    total_cap = sum(c['capacity_mw'] for c in countries)
    for spec_name, exporters in [('Raw', exp_raw), ('Cost-Recovery', exp_cr),
                                  ('Bilateral', exp_bi)]:
        exp_cap = sum(iso2c[iso]['capacity_mw'] for iso in exporters if iso in iso2c)
        diag_lines.append(
            f"  {spec_name}: {len(exporters)} exporters, "
            f"{exp_cap:,.0f} MW / {total_cap:,.0f} MW total "
            f"({100*exp_cap/total_cap:.1f}%)")
    diag_lines.append("")

    # Clearing prices
    diag_lines.append("=" * 60)
    diag_lines.append("CLEARING PRICES")
    diag_lines.append("=" * 60)
    diag_lines.append(f"  Raw:           ${pt_raw:.4f}/hr" if pt_raw else "  Raw:           N/A")
    diag_lines.append(f"  Cost-Recovery: ${pt_cr:.4f}/hr" if pt_cr else "  Cost-Recovery: N/A")
    diag_lines.append(f"  Bilateral:     (bilateral model, no single clearing price)")
    diag_lines.append("")

    # Latency stats
    diag_lines.append("=" * 60)
    diag_lines.append("LATENCY DATA")
    diag_lines.append("=" * 60)
    diag_lines.append(f"  Pairs loaded: {len(latency)}")
    panel_isos = {c['iso3'] for c in countries}
    covered = sum(1 for (a, b) in latency if a in panel_isos and b in panel_isos)
    diag_lines.append(f"  Pairs in panel: {covered}")
    diag_lines.append("")

    diag_text = '\n'.join(diag_lines)
    with open(OUT_DIAG, 'w', encoding='utf-8') as f:
        f.write(diag_text)

    print(f"Wrote {OUT_DIAG}")
    print()
    print(diag_text)

if __name__ == '__main__':
    main()
