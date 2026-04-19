"""
Run the full FLOP trade model pipeline.
Usage: python run_pipeline.py
"""
import sys
import os
import io

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add project root to path so config and src modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.a_ingest import ingest_all
from src.b_costs import estimate_construction_regression, compute_all_costs
from src.c_efficiency import compute_all_efficiency
from src.d_sovereignty import compute_all_sovereignty
from src.e_equilibrium import run_all_specifications
from src.f_tables import assemble_all_tables


def main():
    print("=" * 60)
    print("FLOP Trade Model — Fresh Calculation Pipeline")
    print("=" * 60)

    # Step A: Ingest raw data
    print("\n[A] Ingesting raw data...")
    panel = ingest_all()
    print(f"    {len(panel)} countries loaded")

    # Step B: Estimate construction regression + compute costs
    print("\n[B] Estimating construction regression (Appendix E)...")
    panel, reg_diagnostics = estimate_construction_regression(panel)
    print(f"    Predicted construction range: "
          f"${panel['construction_per_watt'].min():.1f}"
          f"–${panel['construction_per_watt'].max():.1f}/W")

    print("\n[B] Computing unit costs...")
    panel = compute_all_costs(panel)
    print(f"    c_raw range: ${panel['c_raw'].min():.3f} – ${panel['c_raw'].max():.3f}")
    print(f"    c_cr  range: ${panel['c_cr'].min():.3f} – ${panel['c_cr'].max():.3f}")

    min_bound = config.RHO + config.ETA
    if panel["c_raw"].min() < min_bound - 0.001:
        print(f"    WARNING: min c_raw = ${panel['c_raw'].min():.4f} < "
              f"rho+eta = ${min_bound:.4f}")
    else:
        print(f"    OK: all c_raw >= rho+eta = ${min_bound:.4f}")

    # Step C: Efficiency
    print("\n[C] Computing efficiency indices...")
    panel = compute_all_efficiency(panel)
    print(f"    xi range: {panel['xi'].min():.3f} – {panel['xi'].max():.3f}")
    print(f"    c_adj range: ${panel['c_adj'].min():.3f} – ${panel['c_adj'].max():.3f}")

    # Step D: Sovereignty
    print("\n[D] Computing sovereignty matrices...")
    lambdas, latency = compute_all_sovereignty(panel)

    # Step E: Equilibrium
    print("\n[E] Solving equilibria...")
    results = run_all_specifications(panel, lambdas, latency)
    for spec, res in results.items():
        n_exp = sum(1 for r in res["regime"].values() if "E" in r)
        n_bound = sum(1 for v in res["shadow_value"].values() if v > 0)
        print(f"    {spec}: {n_exp} exporters, p_T=${res['p_T']:.3f}, "
              f"{n_bound} capacity-bound, HHI={res['hhi_training']:.3f}")

    # Step F: Tables
    print("\n[F] Assembling tables...")
    tables = assemble_all_tables(panel, results, lambdas, latency)

    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    # Show Table 3a top 10
    t3a = tables["3a"]
    print("\nTable 3a (top 10):")
    print(f"{'Country':<20} {'c_raw':>8} {'Rk1':>4} {'T1':>3} "
          f"{'c_cr':>8} {'Rk2':>4} {'T2':>3} "
          f"{'c_adj':>8} {'xi':>5} {'Rk3':>4} {'T3':>3} {'T4':>3} {'D':>3}")
    for _, row in t3a.head(10).iterrows():
        print(f"{row['Country']:<20} ${row['c_raw']:>6.2f} {row['Rank_1']:>4d} "
              f"{row['Type_1']:>3} ${row['c_cr']:>6.2f} {row['Rank_2']:>4d} "
              f"{row['Type_2']:>3} ${row['c_adj']:>6.2f} {row['xi']:>5.2f} "
              f"{row['Rank_3']:>4d} {row['Type_3']:>3} {row['Type_4']:>3} "
              f"{row['Delta']:>3d}")

    return panel, results, tables


if __name__ == "__main__":
    main()
