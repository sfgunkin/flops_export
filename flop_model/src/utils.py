"""Shared helpers: country name standardization, formatting, ranking."""

import os

# Project root (flop_model/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# T&T market name → ISO3 mapping
TT_MARKET_TO_ISO3 = {
    "Tokyo": "JPN", "Osaka": "JPN",
    "Singapore": "SGP",
    "Zurich": "CHE",
    "Silicon Valley": "USA", "New Jersey": "USA", "Chicago": "USA",
    "North Virginia": "USA", "Portland": "USA", "Atlanta": "USA",
    "Phoenix": "USA", "Columbus": "USA", "Dallas": "USA", "Charlotte": "USA",
    "Oslo": "NOR",
    "Auckland": "NZL",
    "Stockholm": "SWE",
    "Helsinki": "FIN",
    "Copenhagen": "DNK",
    "London": "GBR", "Cardiff": "GBR",
    "Vienna": "AUT",
    "Frankfurt": "DEU", "Berlin": "DEU",
    "Kuala Lumpur": "MYS",
    "Kingdom of Saudi Arabia": "SAU",
    "Jakarta": "IDN",
    "Paris": "FRA", "Bordeaux": "FRA",
    "Amsterdam": "NLD",
    "São Paulo": "BRA",
    "Sydney": "AUS", "Melbourne": "AUS",
    "Lagos": "NGA",
    "Querétaro": "MEX",
    "Cape Town": "ZAF", "Johannesburg": "ZAF",
    "Lisbon": "PRT",
    "Seoul": "KOR",
    "Dublin": "IRL",
    "Madrid": "ESP",
    "Montevideo": "URY",
    "Milan": "ITA",
    "Nairobi": "KEN",
    "Toronto": "CAN",
    "UAE": "ARE",
    "Warsaw": "POL",
    "Santiago": "CHL",
    "Athens": "GRC",
    "Bogotá": "COL",
    "Mumbai": "IND",
    "Shanghai": "CHN",
}

# World Bank developing country classification (non-High income)
DEVELOPING_COUNTRIES = {
    "IRN", "TKM", "ETH", "KGZ", "EGY", "DZA", "NGA", "TJK", "CHN", "UKR",
    "ARG", "COL", "AZE", "KAZ", "UZB", "VNM", "BRA", "IND", "IDN", "GEO",
    "TUR", "BIH", "MAR", "MEX", "ARM", "PHL", "THA", "SRB", "PAK", "MDA",
    "MKD", "GHA", "ALB", "ROU", "BGR", "ZAF", "KEN", "SEN",
    # XKX and MNE might be upper-middle
    "XKX", "MNE",
}


def fmt_cost(x):
    """Format cost as '$X.XX'."""
    return f"${x:.2f}"


def fmt_xi(x):
    """Format ξ as 'X.XX'."""
    return f"{x:.2f}"


def fmt_pct(x):
    """Format as signed percentage: '+X.X%' or '−X.X%'."""
    if x >= 0:
        return f"+{x*100:.1f}%"
    return f"\u2212{abs(x)*100:.1f}%"


def fmt_mu(x):
    """Format shadow value: '$X.XXX' or '—' if zero."""
    if abs(x) < 1e-6:
        return "\u2014"
    return f"${x:.3f}"


def rank_series(s, method="min", ascending=True):
    """Rank a pandas Series. Lower value = rank 1 if ascending."""
    return s.rank(method=method, ascending=ascending).astype(int)
