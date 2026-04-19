"""
Step D: Bilateral sovereignty λ matrices and latency matrix.

Input: sovereignty raw files, latency raw file, panel
Output: lambda_bilateral, lambda_uniform, lambda_fdi (all as dicts),
        latency matrix (dict of (from, to) → ms)
"""

import os
import csv
import math

import config
from .utils import DATA_RAW


# ── Bloc assignments ──

def _load_blocs():
    """Load geopolitical bloc assignments.
    Returns dict: iso3 → bloc code ('W', 'C', 'N').
    Countries not listed default to 'N' (non-aligned).
    """
    path = os.path.join(DATA_RAW, "sovereignty", "blocs.csv")
    blocs = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            blocs[row["iso3"].strip()] = row["bloc"].strip()
    return blocs


def _load_sanctions():
    """Load sanctioned countries.
    Returns set of ISO3 codes.
    """
    path = os.path.join(DATA_RAW, "sovereignty", "sanctions.csv")
    sanctioned = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["sanctioned"].strip() == "1":
                sanctioned.add(row["iso3"].strip())
    return sanctioned


def _load_data_adequacy():
    """Load regulatory compatibility frameworks.
    Returns list of sets, each set being a group of mutually adequate countries.
    """
    path = os.path.join(DATA_RAW, "sovereignty", "data_adequacy.csv")
    frameworks = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            members = {m.strip() for m in row["members"].split(",")}
            frameworks.append(members)
    return frameworks


# ── Inter-bloc distance ──

BLOC_DISTANCE = {
    ("W", "W"): 0.00,
    ("W", "C"): 0.95,
    ("W", "N"): 0.40,
    ("C", "W"): 0.95,
    ("C", "C"): 0.00,
    ("C", "N"): 0.55,
    ("N", "W"): 0.40,
    ("N", "C"): 0.55,
    ("N", "N"): 0.20,
}


def _get_bloc(iso, blocs):
    return blocs.get(iso, "N")


def compute_geo_distance(iso_i, iso_j, blocs):
    """Geopolitical distance G_{ij} ∈ [0, 1]."""
    if iso_i == iso_j:
        return 0.0
    bi = _get_bloc(iso_i, blocs)
    bj = _get_bloc(iso_j, blocs)
    return BLOC_DISTANCE.get((bi, bj), 0.40)


def compute_reg_compat(iso_i, iso_j, frameworks):
    """Regulatory compatibility R_{ij} ∈ {0, 1}.
    Returns 1 if both countries share a mutual adequacy framework.
    """
    if iso_i == iso_j:
        return 1
    for group in frameworks:
        if iso_i in group and iso_j in group:
            return 1
    return 0


def compute_lambda_bilateral(iso_i, iso_j, blocs, frameworks, sanctioned):
    """
    Eq. (2): λ_ij = α₁·G(i,j) + α₂·(1−R(i,j))
    Returns inf if either country is sanctioned (vis-à-vis non-sanctioned partner).
    λ_ii = 0 by definition.
    """
    if iso_i == iso_j:
        return 0.0
    # Sanctions
    if iso_i in sanctioned or iso_j in sanctioned:
        # Same-bloc sanctioned countries can still trade
        if iso_i in sanctioned and iso_j in sanctioned:
            bi = _get_bloc(iso_i, blocs)
            bj = _get_bloc(iso_j, blocs)
            if bi == bj:
                return config.ALPHA1 * 0.0 + config.ALPHA2 * 1.0
        return math.inf
    G_ij = compute_geo_distance(iso_i, iso_j, blocs)
    R_ij = compute_reg_compat(iso_i, iso_j, frameworks)
    return config.ALPHA1 * G_ij + config.ALPHA2 * (1 - R_ij)


def compute_lambda_fdi(host_j, buyer_k, blocs, frameworks, sanctioned, h="USA"):
    """
    Eq. (2'): λ^FDI_jk = α₁·G(h,k) + α₂·(1−R(h,k)) + α₃·S(j,k)
    Trust shifts from host j to hyperscaler home h.
    Sanctions on host j still bind.
    """
    if host_j == buyer_k:
        return 0.0
    # Sanctions on the host still apply
    if host_j in sanctioned:
        return math.inf
    # Buyer-side: use hyperscaler home (h=USA) relationship
    G_hk = compute_geo_distance(h, buyer_k, blocs)
    R_hk = compute_reg_compat(h, buyer_k, frameworks)
    # Sanctions component: S(j,k) — if buyer is sanctioned vis-à-vis host
    if buyer_k in sanctioned:
        return math.inf
    return config.ALPHA1 * G_hk + config.ALPHA2 * (1 - R_hk)


def compute_lambda_uniform(iso_i, iso_j, sanctioned):
    """Column (6): flat λ = 0.10 for all non-sanctioned pairs."""
    if iso_i == iso_j:
        return 0.0
    if iso_i in sanctioned or iso_j in sanctioned:
        return math.inf
    return config.LAMBDA_UNIFORM


# ── Latency ──

def _load_latency():
    """Load bilateral RTT latency from WonderNetwork.
    Returns dict: (iso3_from, iso3_to) → avg_ms.
    """
    path = os.path.join(DATA_RAW, "latency", "wondernetwork_rtt.csv")
    latency = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src = row["iso3_from"].strip()
            dst = row["iso3_to"].strip()
            avg = float(row["avg_ms"])
            latency[(src, dst)] = avg
    return latency


# ── Main entry point ──

def compute_all_sovereignty(panel):
    """Compute all sovereignty matrices and load latency.

    Returns:
        lambdas: dict with keys 'bilateral', 'uniform', 'fdi',
                 each mapping (iso_i, iso_j) → λ value
        latency: dict mapping (iso_from, iso_to) → avg_ms
    """
    countries = list(panel["country_iso3"])

    blocs = _load_blocs()
    sanctioned = _load_sanctions()
    frameworks = _load_data_adequacy()
    latency = _load_latency()

    print(f"    {len(sanctioned)} sanctioned countries: {sorted(sanctioned)}")
    print(f"    {len(latency)} latency pairs loaded")
    print(f"    {len(frameworks)} adequacy frameworks loaded")

    # Build lambda matrices as flat dicts
    lam_bilateral = {}
    lam_uniform = {}
    lam_fdi = {}

    for i in countries:
        for j in countries:
            lam_bilateral[(i, j)] = compute_lambda_bilateral(i, j, blocs, frameworks, sanctioned)
            lam_uniform[(i, j)] = compute_lambda_uniform(i, j, sanctioned)
            lam_fdi[(i, j)] = compute_lambda_fdi(i, j, blocs, frameworks, sanctioned)

    # Count summary stats
    n_inf_bilateral = sum(1 for v in lam_bilateral.values() if v == math.inf)
    n_inf_uniform = sum(1 for v in lam_uniform.values() if v == math.inf)
    print(f"    Bilateral: {n_inf_bilateral} prohibited pairs")
    print(f"    Uniform:   {n_inf_uniform} prohibited pairs")

    lambdas = {
        "bilateral": lam_bilateral,
        "uniform": lam_uniform,
        "fdi": lam_fdi,
        "sanctioned": sanctioned,
        "blocs": blocs,
        "frameworks": frameworks,
    }

    return lambdas, latency
