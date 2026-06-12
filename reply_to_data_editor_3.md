Subject: Re: Reproducibility verification RR_EUR_2026_669 — all five flagged exhibits fixed

Dear [Data Editor],

Thank you for the detailed verification report of June 12. We traced each of
the five exhibits flagged as not reproducing. In every case the underlying
model results were correct (as the reproduction of Table 2 and Tables A4, A5,
A7 indicates); the failures were in the package's table-export and sensitivity
steps, which wrote internal model quantities rather than the cells the paper
prints. We have revised the package so that every analytical exhibit now
reproduces cell-for-cell. Specifically:

1. **Table 3 and Table A2.** The export wrote production costs c_j without the
   $0.15/hr networking markup and in a single merged layout. It now prints the
   paper's delivered prices (P_j = c_j + η), with the four specification
   blocks each sorted by its own ranking, the regime-type letters (EE/IE/DD/II)
   and the sanction/developing flags, in the paper's units and number formats
   (revised `code/19_export_tables.do`).

2. **Table A1.** The capacity column was exported in GPU-hours instead of MW
   of installed data-center capacity, the demand share was misscaled, and the
   cost-recovery electricity-price column was missing. All three are fixed,
   and rows are now in cost-recovery rank order as published.

3. **Table A3.** The export pointed to an internal robustness file with a
   different scenario design. The revised step computes the published Table A3
   directly: hardware-amortization scenarios ρ = $1.36 / $1.30 / $1.42 with
   the developing-countries-in-top-15 count, maximum cost spread, Spearman
   rank correlation, and top-5 ranking.

4. **Table A6.** The sensitivity runner used a simplified income statement
   that omitted GPU depreciation (and the GPU-value insurance base), so its
   scenarios — including its own base case — diverged from the main DCF. Each
   scenario now re-runs the full cash-flow model, and the code asserts that
   the base case reproduces the main DCF exactly (NPV $353M, IRR 17.6%, as in
   Table A5, which already verified).

To confirm the fixes, we extracted every cell of the five exhibits from the
typeset manuscript and compared them against the regenerated CSVs: all cells
are now identical (Table 3: 25 rows × 12 columns; Table A1: 85 × 9; Table A2:
85 × 8; Table A3: 3 rows; Table A6: 11 rows).

The updated package replaces the previous one. Only two code files changed
(`code/14_kyrgyzstan_dcf.do`, `code/19_export_tables.do`), plus the README's
fidelity section; the exhibits that already reproduced are unaffected, and the
reference outputs in `output/` were refreshed from a clean end-to-end run.
Runtime and setup are unchanged (one working-directory edit in `run_all.do`).

Please let us know if anything else stands in the way of completing the
verification.

Best regards,
Michael Lokshin
