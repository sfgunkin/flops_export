"""
Step F: Assemble Tables 3a, 3b, A1, A2, A3.

Writes CSV files and a combined XLSX workbook.
"""

import os

import pandas as pd

import config
from .utils import OUTPUT_DIR, fmt_cost, fmt_xi, fmt_pct, fmt_mu
from .c_efficiency import compute_all_efficiency
from .e_equilibrium import run_all_specifications


def assemble_table_3a(panel, results):
    """
    Table 3a: Top 25 countries by column (4) rank.

    Columns: Country | c_raw | Rank₁ | Type₁ | c_cr | Rank₂ | Type₂ |
             c_adj | ξ | Rank₃ | Type₃ | c_adj | Rank₄ | Type₄ | Δ
    """
    countries = list(panel["country_iso3"])

    # Build data for all 85 countries
    rows = []
    for iso in countries:
        name = panel.loc[iso, "country_name"]
        c_raw = panel.loc[iso, "c_raw"]
        c_cr = panel.loc[iso, "c_cr"]
        c_adj = panel.loc[iso, "c_adj"]
        xi = panel.loc[iso, "xi"]
        rank_raw = int(panel.loc[iso, "rank_raw"])
        rank_cr = int(panel.loc[iso, "rank_cr"])
        rank_adj = int(panel.loc[iso, "rank_adj"])

        type_1 = results["col1"]["regime"].get(iso, "II")
        type_2 = results["col2"]["regime"].get(iso, "II")
        type_3 = results["col3"]["regime"].get(iso, "II")
        type_4 = results["col4"]["regime"].get(iso, "II")

        delta = rank_raw - rank_adj

        rows.append({
            "Country": name,
            "iso3": iso,
            "c_raw": c_raw,
            "Rank_1": rank_raw,
            "Type_1": type_1,
            "c_cr": c_cr,
            "Rank_2": rank_cr,
            "Type_2": type_2,
            "c_adj": c_adj,
            "xi": xi,
            "Rank_3": rank_adj,
            "Type_3": type_3,
            "c_adj_4": c_adj,  # same cost, different regime
            "Rank_4": rank_adj,  # same rank
            "Type_4": type_4,
            "Delta": delta,
        })

    df = pd.DataFrame(rows)
    # Sort by Rank_4 and take top 25
    df = df.sort_values("Rank_4").head(25).reset_index(drop=True)
    return df


def assemble_table_3b(panel, results, table_3a_countries):
    """
    Table 3b: Same 25 countries as 3a.

    Columns: Country | c_adj | Type₄ | Type₆ | Rank₆ | Type₇ | λ* | μ
    """
    rows = []
    for iso in table_3a_countries:
        name = panel.loc[iso, "country_name"]
        c_adj = panel.loc[iso, "c_adj"]
        rank_adj = int(panel.loc[iso, "rank_adj"])

        type_4 = results["col4"]["regime"].get(iso, "II")
        type_6 = results["col6"]["regime"].get(iso, "II")
        type_7 = results["col7"]["regime"].get(iso, "II")

        # Rank in col6 (uniform) by cost
        # We need to compute rank_6 from the uniform results
        all_costs = {i: panel.loc[i, "c_adj"] for i in panel["country_iso3"]}
        sorted_costs = sorted(all_costs.items(), key=lambda x: x[1])
        rank_6 = next(i + 1 for i, (iso_c, _) in enumerate(sorted_costs) if iso_c == iso)

        lambda_star = results["col4"]["lambda_star"].get(iso, 0)
        mu = results["col4"]["shadow_value"].get(iso, 0)

        rows.append({
            "Country": name,
            "iso3": iso,
            "c_adj": c_adj,
            "Type_4": type_4,
            "Type_6": type_6,
            "Rank_6": rank_6,
            "Type_7": type_7,
            "lambda_star": lambda_star,
            "mu": mu,
        })

    return pd.DataFrame(rows)


def assemble_table_a1(panel, results):
    """
    Table A1: All 85 countries sorted by c_adj.

    Columns: Country | p_E | θ | PUE | Constr. | k̄(MW) | ω(%) | ξ | c_adj | μ | Cost-Rec.p_E
    """
    rows = []
    for iso in panel["country_iso3"]:
        name = panel.loc[iso, "country_name"]
        rows.append({
            "Country": name,
            "iso3": iso,
            "p_E": panel.loc[iso, "p_E_raw"],
            "theta": panel.loc[iso, "theta"],
            "PUE": panel.loc[iso, "pue"],
            "Constr_per_W": panel.loc[iso, "construction_per_watt"],
            "k_bar_MW": panel.loc[iso, "capacity_mw"],
            "omega_pct": panel.loc[iso, "demand_share"] * 100,
            "xi": panel.loc[iso, "xi"],
            "c_adj": panel.loc[iso, "c_adj"],
            "mu": results["col4"]["shadow_value"].get(iso, 0),
            "Cost_Rec_pE": panel.loc[iso, "p_E_cr"],
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("c_adj").reset_index(drop=True)
    return df


def assemble_table_a2(panel, results):
    """Table A2: All 85 countries, same structure as Table 3a."""
    countries = list(panel["country_iso3"])
    rows = []
    for iso in countries:
        name = panel.loc[iso, "country_name"]
        rows.append({
            "Country": name,
            "iso3": iso,
            "c_raw": panel.loc[iso, "c_raw"],
            "Rank_1": int(panel.loc[iso, "rank_raw"]),
            "Type_1": results["col1"]["regime"].get(iso, "II"),
            "c_cr": panel.loc[iso, "c_cr"],
            "Rank_2": int(panel.loc[iso, "rank_cr"]),
            "Type_2": results["col2"]["regime"].get(iso, "II"),
            "c_adj": panel.loc[iso, "c_adj"],
            "xi": panel.loc[iso, "xi"],
            "Rank_3": int(panel.loc[iso, "rank_adj"]),
            "Type_3": results["col3"]["regime"].get(iso, "II"),
            "c_adj_4": panel.loc[iso, "c_adj"],
            "Rank_4": int(panel.loc[iso, "rank_adj"]),
            "Type_4": results["col4"]["regime"].get(iso, "II"),
            "Delta": int(panel.loc[iso, "rank_raw"]) - int(panel.loc[iso, "rank_adj"]),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("Rank_4").reset_index(drop=True)
    return df


def assemble_table_a3(panel, lambdas_dict, latency):
    """
    Table A3: Sensitivity analysis.

    Reruns equilibrium for each scenario in config.SENSITIVITY.
    """
    from .utils import DEVELOPING_COUNTRIES

    rows = []
    for scenario_name, params in config.SENSITIVITY.items():
        # Re-compute efficiency with scenario parameters
        panel_s = compute_all_efficiency(
            panel, omega=params["omega"], rho=params["rho"], form=params["form"]
        )

        # Run equilibrium
        results_s = run_all_specifications(panel_s, lambdas_dict, latency)
        col3 = results_s["col3"]

        # Top 15 by c_adj
        costs_sorted = sorted(
            [(iso, panel_s.loc[iso, "c_adj"]) for iso in panel_s["country_iso3"]],
            key=lambda x: x[1]
        )
        top15 = [iso for iso, _ in costs_sorted[:15]]
        top5 = [panel_s.loc[iso, "country_name"] for iso in top15[:5]]

        # Count developing in top 15
        n_dev = sum(1 for iso in top15 if iso in DEVELOPING_COUNTRIES)

        # Max markup in top 15
        min_cost = costs_sorted[0][1]
        max_markup = max((c - min_cost) / min_cost for _, c in costs_sorted[:15])

        # Spearman ρ vs baseline cost-recovery ranking
        from scipy.stats import spearmanr
        adj_ranks = [panel_s.loc[iso, "rank_adj"] for iso in panel_s["country_iso3"]]
        cr_ranks = [panel_s.loc[iso, "rank_cr"] for iso in panel_s["country_iso3"]]
        rho_val, _ = spearmanr(adj_ranks, cr_ranks)

        rows.append({
            "Scenario": scenario_name,
            "omega": params["omega"],
            "rho": params["rho"],
            "form": params["form"],
            "Dev_top_15": n_dev,
            "Max_markup": max_markup,
            "Spearman_rho": rho_val,
            "Top_5": ", ".join(top5),
        })

    return pd.DataFrame(rows)


def assemble_all_tables(panel, results, lambdas_dict=None, latency=None):
    """Write all tables to CSV and XLSX."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Table 3a
    t3a = assemble_table_3a(panel, results)
    t3a_path = os.path.join(OUTPUT_DIR, "table_3a.csv")
    t3a.to_csv(t3a_path, index=False)
    print(f"    Saved Table 3a ({len(t3a)} rows) -> {t3a_path}")

    # Table 3b (same 25 countries)
    t3a_isos = list(t3a["iso3"])
    t3b = assemble_table_3b(panel, results, t3a_isos)
    t3b_path = os.path.join(OUTPUT_DIR, "table_3b.csv")
    t3b.to_csv(t3b_path, index=False)
    print(f"    Saved Table 3b ({len(t3b)} rows) -> {t3b_path}")

    # Table A1
    ta1 = assemble_table_a1(panel, results)
    ta1_path = os.path.join(OUTPUT_DIR, "table_a1.csv")
    ta1.to_csv(ta1_path, index=False)
    print(f"    Saved Table A1 ({len(ta1)} rows) -> {ta1_path}")

    # Table A2
    ta2 = assemble_table_a2(panel, results)
    ta2_path = os.path.join(OUTPUT_DIR, "table_a2.csv")
    ta2.to_csv(ta2_path, index=False)
    print(f"    Saved Table A2 ({len(ta2)} rows) -> {ta2_path}")

    # Table A3 (only if sovereignty data available)
    if lambdas_dict is not None and latency is not None:
        print("    Computing sensitivity analysis (Table A3)...")
        ta3 = assemble_table_a3(panel, lambdas_dict, latency)
        ta3_path = os.path.join(OUTPUT_DIR, "table_a3.csv")
        ta3.to_csv(ta3_path, index=False)
        print(f"    Saved Table A3 ({len(ta3)} rows) -> {ta3_path}")
    else:
        ta3 = None

    # Combined XLSX
    xlsx_path = os.path.join(OUTPUT_DIR, "all_tables.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        t3a.to_excel(writer, sheet_name="Table_3a", index=False)
        t3b.to_excel(writer, sheet_name="Table_3b", index=False)
        ta1.to_excel(writer, sheet_name="Table_A1", index=False)
        ta2.to_excel(writer, sheet_name="Table_A2", index=False)
        if ta3 is not None:
            ta3.to_excel(writer, sheet_name="Table_A3", index=False)
    print(f"    Saved combined workbook -> {xlsx_path}")

    return {"3a": t3a, "3b": t3b, "A1": ta1, "A2": ta2, "A3": ta3}
