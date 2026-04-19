"""
Step B: PUE, raw cost, cost-recovery cost, construction regression.

Input: country_panel DataFrame from a_ingest
Output: panel with added columns: pue, c_raw, c_cr, rank_raw, rank_cr
"""

import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

import config
from .utils import OUTPUT_DIR, rank_series


def compute_pue(theta):
    """PUE(θ) = φ + δ · max(0, θ − θ̄)"""
    return config.PHI + config.DELTA * max(0.0, theta - config.THETA_BAR)


def compute_raw_cost(pue, p_E_raw, construction_per_watt):
    """
    Eq. (1): c_j = PUE · γ · p_E + ρ + η + p_L · γ · 1000 / (D · H)

    Construction term: p_L ($/W) × γ×1000 (W/GPU) / (D×H hours).
    """
    energy = pue * config.GAMMA_KW * p_E_raw
    construction = (construction_per_watt * config.GAMMA_KW * 1000
                    / (config.D_YEARS * config.H_HOURS))
    return energy + config.RHO + config.ETA + construction


def compute_cr_cost(pue, p_E_cr, construction_per_watt):
    """Same formula, using cost-recovery electricity price."""
    energy = pue * config.GAMMA_KW * p_E_cr
    construction = (construction_per_watt * config.GAMMA_KW * 1000
                    / (config.D_YEARS * config.H_HOURS))
    return energy + config.RHO + config.ETA + construction


def estimate_construction_regression(panel):
    """
    Appendix E: Estimate OLS regression for construction cost prediction.

    Dependent: ln(construction_$/W) for T&T-observed countries.
    Regressors: ln(GDP_pc), ln(pop), urban_share, seismic, region dummies.

    Returns:
        panel: updated with filled construction_per_watt
        diagnostics: dict with R2, adj_R2, F_stat, n_obs, coefficients
    """
    # Identify T&T observed countries
    observed = panel[panel["construction_source"] == "T&T"].copy()
    predicted_mask = panel["construction_source"] == "predicted"

    # Filter to countries with all regressors available
    reg_cols = ["gdp_pc", "population", "urban_share", "seismic", "wb_region"]
    observed = observed.dropna(subset=["construction_per_watt", "gdp_pc", "population", "urban_share"])

    print(f"    T&T observed countries for regression: {len(observed)}")

    # Build regression data
    observed = observed.copy()
    observed["ln_constr"] = np.log(observed["construction_per_watt"])
    observed["ln_gdp_pc"] = np.log(observed["gdp_pc"])
    observed["ln_pop"] = np.log(observed["population"])

    # Region dummies (reference: Europe & Central Asia)
    region_dummies = pd.get_dummies(observed["wb_region"], prefix="reg", drop_first=False)
    # Drop the reference category
    ref_region = "Europe & Central Asia"
    ref_cols = [c for c in region_dummies.columns if ref_region.replace(" ", "") in c.replace(" ", "")]
    if not ref_cols:
        # Try fuzzy match
        for c in region_dummies.columns:
            if "Europe" in c:
                ref_cols = [c]
                break
    if ref_cols:
        region_dummies = region_dummies.drop(columns=ref_cols)

    X = pd.concat([
        observed[["ln_gdp_pc", "ln_pop", "urban_share", "seismic"]].astype(float),
        region_dummies.astype(float)
    ], axis=1)
    X = sm.add_constant(X)
    y = observed["ln_constr"].astype(float)

    model = sm.OLS(y, X).fit()

    print(f"    Regression R² = {model.rsquared:.3f}, Adj R² = {model.rsquared_adj:.3f}")
    print(f"    F-statistic = {model.fvalue:.2f}, n = {model.nobs:.0f}")
    print(f"    Coefficients:")
    for name, coef, se in zip(model.params.index, model.params.values, model.bse.values):
        print(f"      {name}: {coef:.4f} (se={se:.4f})")

    # Predict for all countries (including observed, for validation)
    all_data = panel.copy()
    # Fill NaN regressors with median values from observed countries
    for col in ["gdp_pc", "population", "urban_share", "seismic"]:
        median_val = observed[col].median() if col in observed.columns else 0
        all_data[col] = all_data[col].fillna(median_val)
    all_data["ln_gdp_pc"] = np.log(all_data["gdp_pc"].clip(lower=100))
    all_data["ln_pop"] = np.log(all_data["population"].clip(lower=100))

    # Fill empty region with reference category
    all_data["wb_region"] = all_data["wb_region"].replace("", ref_region).fillna(ref_region)
    all_regions = pd.get_dummies(all_data["wb_region"], prefix="reg", drop_first=False)
    if ref_cols:
        for c in ref_cols:
            if c in all_regions.columns:
                all_regions = all_regions.drop(columns=[c])
    # Ensure same columns as training
    for c in region_dummies.columns:
        if c not in all_regions.columns:
            all_regions[c] = 0
    all_regions = all_regions[region_dummies.columns]

    X_all = pd.concat([
        all_data[["ln_gdp_pc", "ln_pop", "urban_share", "seismic"]].astype(float),
        all_regions.astype(float)
    ], axis=1)
    X_all = sm.add_constant(X_all)

    # Align columns
    for c in X.columns:
        if c not in X_all.columns:
            X_all[c] = 0
    X_all = X_all[X.columns]

    predicted_ln = model.predict(X_all)
    predicted_vals = np.exp(predicted_ln)

    # Fill predicted construction costs for non-T&T countries
    panel = panel.copy()
    for idx in panel.index:
        if panel.loc[idx, "construction_source"] == "predicted":
            panel.loc[idx, "construction_per_watt"] = predicted_vals.loc[idx]

    # Save diagnostics
    coefficients = dict(zip(model.params.index, model.params.values))
    # Rename 'const' to 'intercept' for clarity
    if "const" in coefficients:
        coefficients["intercept"] = coefficients.pop("const")
    diagnostics = {
        "R2": model.rsquared,
        "adj_R2": model.rsquared_adj,
        "F_stat": model.fvalue,
        "n_obs": int(model.nobs),
        "coefficients": coefficients,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    reg_path = os.path.join(OUTPUT_DIR, "construction_regression.json")
    with open(reg_path, "w") as f:
        json.dump(diagnostics, f, indent=2, default=float)
    print(f"    Saved regression to {reg_path}")

    return panel, diagnostics


def compute_all_costs(panel):
    """Add pue, c_raw, c_cr, rank_raw, rank_cr to the panel."""
    panel = panel.copy()

    panel["pue"] = panel["theta"].apply(compute_pue)
    panel["c_raw"] = panel.apply(
        lambda r: compute_raw_cost(r["pue"], r["p_E_raw"], r["construction_per_watt"]),
        axis=1
    )
    panel["c_cr"] = panel.apply(
        lambda r: compute_cr_cost(r["pue"], r["p_E_cr"], r["construction_per_watt"]),
        axis=1
    )

    panel["rank_raw"] = rank_series(panel["c_raw"])
    panel["rank_cr"] = rank_series(panel["c_cr"])

    return panel
