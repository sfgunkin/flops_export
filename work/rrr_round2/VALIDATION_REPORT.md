# Replication-package validation report

**Paper:** "Cheap Energy Might Not Be Enough: A Trade Model of AI Compute
Services" (current manuscript: `Documents/flop_trade_model_v34.docx`)
**Package:** `Replication/` (Stata, 19 steps, `run_all.do`)
**Matched against:** RRR reproducibility review **RR_EUR_2026_669**
(second submission, June 12, 2026)
**Validation date:** June 13, 2026

## Method

1. Ground truth: every table exhibit was extracted cell-by-cell from the
   typeset manuscript (`extract_paper_tables_v34.py` → `v34/paper_*.csv`).
2. The full pipeline (`run_all.do`) was executed twice on the same machine;
   outputs were compared across runs (stability) and against the paper cells
   (`compare_tables_v34.py`).
3. Comparison standard: **strict cell-string equality** for Tables 1, 2, 3,
   A1, A2, A3, A4, A6, A8 (the package exports these as the paper's exact
   cell strings, including regime-type letters, flags, units, and number
   formats; whitespace runs are folded). **Numeric equality at the paper's
   printed precision** for Table A5 (paper: $ millions, 1 decimal; package:
   full-precision model dataset) and Table A7 (paper: 3-decimal coefficients
   and standard errors; package: full-precision regression output).

## Result: every exhibit matches, zero differences

| Exhibit | RRR round-2 verdict | This validation |
|---|---|---|
| Figure 1 | Does not apply (non-analytical) | n/a (drawing) |
| Table 1 | Does not apply (non-analytical) | ✅ exact, 5 rows |
| Table 2 | Reproduced | ✅ exact, 16 rows |
| **Table 3** | **Does not reproduce** | ✅ **exact, 25 rows × 12 cols** |
| **Table A1** | **Does not reproduce** | ✅ **exact, 85 rows × 9 cols** |
| **Table A2** | **Does not reproduce** | ✅ **exact, 85 rows × 8 cols** |
| **Table A3** | **Does not reproduce** | ✅ **exact, 3 scenario rows** |
| Table A4 | Reproduced | ✅ exact, 10 rows |
| Table A5 | Reproduced | ✅ exact at printed precision, 16 years + Total |
| **Table A6** | **Does not reproduce** | ✅ **exact, 11 scenario rows** |
| Table A7 | Reproduced | ✅ exact at printed precision, 11 coefficients |
| Table A8 | Does not apply (non-analytical) | ✅ exact, 6 rows |

Total cell differences across all 11 table exhibits: **0**.

The five exhibits that failed in round 2 were fixed in
`code/14_kyrgyzstan_dcf.do` (Table A6: scenarios now re-run the full
cash-flow model; the base case is asserted equal to the main DCF) and
`code/19_export_tables.do` (Tables 3/A1/A2/A3: paper-exact recomputation —
delivered prices including the η markup, MW units, the cost-recovery price
column, the published A3 scenario design, the paper's sorting/formats/types).
The two static exhibits the review classified as non-analytical (Tables 1 and
A8) and the two it judged reproduced (2 and A4) are now also emitted
cell-for-cell to remove any judgment calls.

## Stability across runs

Two consecutive executions of `run_all.do` produced **byte-identical CSVs for
all 11 exhibits** (the only files that differ between runs are the Stata
`.dta` files, whose headers embed a write timestamp, and the run log). Key
headline numbers, identical in both runs and matching the paper:

- Kyrgyzstan DCF: NPV **$353,362,628**, IRR **17.6%**, payback year 6
  (Tables A4–A6, Appendix D)
- Equilibrium prices: p_T raw **$1.5921**, cost-recovery **$1.5978**,
  bilateral CR **$1.5978**
- Table A3: dev-in-top-15 = 11; spreads 11.9% / 12.3% / 11.4%; top-5
  Kyrgyzstan, Ethiopia, Kosovo, Canada, Tajikistan in all scenarios

## Version note (v33 vs v34)

The review examined the paper shared June 3 (v33). The current manuscript
(v34) contains prose-only revisions; extraction confirms the five flagged
exhibits are **byte-identical between v33 and v34**, so this validation holds
for both versions.

## In-text (prose) numbers

Beyond the exhibits, every quantitative claim in the body text is covered by
the paper's test suite (`Programs/test_paper_values.py`, 314 tests recomputing
values from the raw calibration data, including the docx text itself):
**314/314 pass** against v34.

## How to re-verify

```
# 1. run the package (Stata, ~9 min):  do run_all.do   (from Replication/)
# 2. extract paper cells:    python -X utf8 extract_paper_tables_v34.py
# 3. compare:                python -X utf8 compare_tables_v34.py
#    -> expect "Total differences across all 11 exhibits: 0"
```
