"""
FLOP Trade Model — All parameters.
Source: Table 2 of the paper. Change values ONLY here.
"""

# === Hardware ===
GAMMA_KW        = 0.700        # GPU thermal design power (kW)
P_GPU           = 25_000       # GPU purchase price ($)
L_YEARS         = 3            # GPU useful life (years)
H_HOURS         = 8_766        # Hours per year (365.25 × 24)
BETA            = 0.70         # GPU utilization rate
# Derived
RHO = P_GPU / (L_YEARS * H_HOURS * BETA)  # Amortized hardware cost ($/hr)

# === Networking ===
ETA             = 0.15         # Amortized networking cost ($/hr)

# === Cooling ===
PHI             = 1.08         # PUE baseline (best-practice free-air)
DELTA           = 0.015        # PUE temperature sensitivity (per °C)
THETA_BAR       = 15.0         # Free-cooling threshold (°C)

# === Construction ===
D_YEARS         = 15           # Data center facility lifetime (years)

# === Efficiency ===
OMEGA           = 0.50         # Governance weight in ξ
XI_MIN          = 0.01         # Floor to prevent division by zero

# === Trade ===
TAU             = 0.0008       # Latency degradation per ms of RTT
L_BAR_MS        = 200          # Maximum usable latency (ms)
ALPHA_TRAIN     = 0.50         # Training share of compute demand

# === Sovereignty ===
ALPHA1          = 0.08         # Geopolitical distance weight
ALPHA2          = 0.04         # Regulatory incompatibility weight
ALPHA3          = 0.10         # Sanctions weight
LAMBDA_UNIFORM  = 0.10         # Uniform premium for column (6)

# === Demand ===
Q_TOTAL         = 6e10         # Total global compute demand (GPU-hr/yr)

# === Sensitivity scenarios (Table A3) ===
SENSITIVITY = {
    "baseline":        {"omega": 0.50, "rho": RHO,  "form": "B"},
    "form_a":          {"omega": 0.85, "rho": RHO,  "form": "A"},
    "high_governance":  {"omega": 0.85, "rho": RHO,  "form": "B"},
    "low_hardware":     {"omega": 0.50, "rho": 1.30, "form": "B"},
    "high_hardware":    {"omega": 0.50, "rho": 1.42, "form": "B"},
}

# === Country count ===
N_COUNTRIES     = 85

# === Construction cost prediction (Appendix E) ===
# The regression is ESTIMATED from raw data, not hardcoded.
# Populated at runtime by b_costs.estimate_construction_regression()
CONSTRUCTION_REGRESSION = None
