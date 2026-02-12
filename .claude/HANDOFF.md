# Project Handoff: FLOP Trade Model Paper

## Current State

The deliverable is `flop_trade_model_v8.docx` — a 5-page academic economics paper modeling international trade in computational capacity (FLOPs). It is a `.docx` file generated entirely via `python-docx` with OMML equations.

## Version History

| Version | Pages | Description |
|---------|-------|-------------|
| v2 | 17 | Initial model (Sections 1–2) with production technology, trade costs, 4 propositions |
| v3 | 22 | Added calibration section (Section 5) |
| v4 | 28 | Full paper: added make-or-buy (Section 4), extensions (Section 6), conclusion (Section 7), footnote on agentic compute |
| v5 | 14 | First condensation pass (Sections 3–7 compressed) |
| v6 | 9 | Further condensation (parameter list inlined, proof sketches dropped) |
| v7 | 4 | Aggressive condensation: merged sections, dropped Props 3–4, folded into Props 1–2; fixed sSubSup OMML; added fixed costs to Prop 2 |
| v8 | 5 | **Current.** All equations in borderless 2-column tables (equation left, number right); expanded explanation of equation (2); equations renumbered (1)–(4) |

## Paper Structure (v8)

```
Title: Comparative Advantage in Compute Exports: A Two-Segment Model with Heterogeneous Trade Costs
Abstract
1. Model Setup
   1.1 Production Technology — equation (1): c_j = (α + δγ(θ_j))p_j^E + βr + ηp_j^L
   1.2 Trade Costs — equation (2): piecewise τ^I(l_jk) with threshold l̄ ≈ 40ms
2. Comparative Advantage Results
   Proposition 1: Geographic Separation (training concentrates, inference disperses)
   Proposition 2: Entry with Fixed Costs — equation (3): c_j + F/Q_j < c_{j*}
3. The Make-or-Buy Decision — equation (4): c_k + F^s/Q_k^s ≤ p_k^{s*} + λ
   Four regimes: full import / import training+build inference / full domestic / build training+import inference
4. Calibration and Discussion
5. Conclusion
References (9 entries)
```

## Key Technical Details

### OMML Equations in python-docx

Equations are built using raw OMML XML via `OxmlElement`. Key helpers:

- `make_run(text, italic, bold)` — creates `m:r` with Cambria Math font
- `make_sub(base, sub)` — creates `m:sSub`
- `make_sup(base, sup)` — creates `m:sSup`
- `make_sub_sup(base, sub, sup)` — creates `m:sSubSup` (CRITICAL: use this for combined sub+sup like p_k^{T*}, Q_k^s, NOT sequential sSub + sSup which renders broken)
- `make_frac(num_els, den_els)` — creates `m:f`
- `inline_math(paragraph, elements)` — appends `m:oMath` to paragraph
- `display_math(paragraph, elements)` — appends `m:oMathPara` (centered display)

### Equation Tables

All display equations use a borderless 1-row × 2-column table:
- Left cell (8460 twips / ~5.875"): centered equation via `m:oMathPara`
- Right cell (900 twips / ~0.625"): right-aligned equation number e.g. "(1)"
- No borders on table or cells
- Vertical alignment: center

The `make_eq_table(doc, body, insert_after_el, math_para_els, eq_number)` function handles this. For piecewise equations (eq 2), pass multiple `oMathPara` elements; each gets its own paragraph in the left cell.

### Style Conventions

- First line indent: 0.5 inches on all body paragraphs
- Headings: Level 1 for sections, Level 2 for subsections and propositions
- Proposition names in bold: `p.add_run('Proposition 1').bold = True`
- Regime names in italic: `p.add_run('full import').italic = True`
- References: hanging indent (left indent 0.5", first line -0.5"), 11pt, 6pt space after
- Author citation format: first name initials included (e.g., "Helpman, E., Melitz, M. J., and S. R. Yeaple.")

### Known LibreOffice Rendering Limitation

OMML equations do not render in LibreOffice PDF conversion — they appear as blank space with surrounding text visible. The equations are structurally correct and render properly in Microsoft Word. The PDF previews in this project show blank equation areas; this is expected.

## Model Summary

**Core insight:** FLOPs are traded goods, but training compute (batch, latency-insensitive) and inference compute (real-time, latency-sensitive) have fundamentally different trade costs.

**Production:** All countries produce FLOPs using the same technology. Costs vary by electricity price, climate (cooling), and land. Hardware costs (GPU rental) are globally common because NVIDIA dominates supply.

**Trade costs:** Training has zero iceberg costs (τ^T = 1). Inference has a piecewise iceberg cost: zero below a ~40ms latency threshold, linearly increasing above it.

**Results:**
1. Training concentrates in cheapest-energy countries globally; inference disperses toward demand centers
2. Entry requires both low variable costs AND sufficient scale (Melitz-style fixed cost threshold)
3. Demand centers face a make-or-buy decision across four regimes, with a sovereignty premium λ shifting toward domestic production
4. Observable data (electricity prices, latency, cloud spending) can calibrate the model

## Files

- `flop_trade_model_v8.docx` — **current deliverable**
- `flop_trade_model_v4.docx` — full 28-page version with all sections, extensions, calibration detail
- `eq_tables.py` — the build script for v8 (complete, self-contained)
- `fix_subsup.py` — the sSubSup fix script
- `generate_model.py`, `generate_model_v2.py` — original build scripts for v2
- `add_calibration.py`, `add_extensions.py` — scripts that built v3 and v4

## Potential Next Steps (from the paper itself)

- Empirical calibration using real data
- Add figures/tables with country assignments to regimes
- Formal proofs for propositions
- Expand the footnote on agentic compute (present in v4, dropped in condensation)
- Restore extensions on export controls, distributed training, resource curse (detailed in v4)
- Add a welfare analysis section

## User Preferences

- Academic economics style; prose with first-line indents, no bullets
- OMML equations generated via Python (not LaTeX)
- References with first-name initials (Helpman, E., not just Helpman)
- When generating Word documents with equations, always use Python to generate OMML
- Follow academic-research skill for writing tasks
- Follow reference-format skill for citations
