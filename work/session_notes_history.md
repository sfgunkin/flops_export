# FLOPs Export Paper

## Status
**MIGRATED TO DOCXKIT (2026-08-14, commit 7f5e79c; docxkit 4df3b09+3548ad7).** Paper was submitted to JITED, then the reader/checker layer moved onto the shared toolkit. The GENERATOR stays the paper's own (docxkit v1 leaves content builders per paper) — everything that READS/CHECKS/DERIVES from the manuscript is docxkit now. Gate: `work/docxkit_migration/gate.py` — rebuild must still BE `golden_v34.docx` (frozen at f5cbff9, the submitted text) on every compare layer bar the version stamp; passed at every step, so **no word of the paper changed**. What moved and what it found:
- `add_calibration_v34.py`: `preserve_space` over all text parts as the LAST build step (reports 0 — python-docx protects its own runs); new `_set_once()` fixes **32 schema violations in the SUBMITTED manuscript** (20 duplicate `w:spacing`, 12 duplicate `w:tcBorders`) — cause: a merged cell is ONE `<w:tc>` and python-docx returns it once per grid position, so `for row in tbl.rows: for cell in row.cells:` appended a duplicate child each visit. Word rendered it anyway; only `docxkit lint` saw it. Now 0.
- **NEW `Programs/verify_paper.py`** — what the document IS (citations / crossrefs / lint / abstract parity across all 3 manuscripts), as `test_paper_values.py` is what it SAYS. `--quick` skips the advisory refstyle/prose-math/footnote-size/wordcount audits. **Abstract parity was previously unchecked by anything** (sync only covers body from the `1. Introduction` anchor down; the abstract is front matter — and the July author edit was in the abstract).
- `sync_jited_submission.py`: body parity 220 → **2,375 paragraphs** (python-docx `Document.paragraphs` never yielded table cells); staleness now via `package.changed_parts`, NOT text — a structural repair changes no words, so the old text test left the journal's copies stale (it did, until this).
- `test_paper_values.py`: `docxkit.testing` fixtures — lock-safe reads (suite survives the paper being open in Word), `latest_version()` instead of hardcoded v34, tables via `read_all`. 324/324.
- `work/rrr_round2/extract_paper_tables_v34.py`: `tables.read_all` + new `Table.grid_rows`. 10/11 exhibits byte-identical; **Table 2 gains θ and λij — OMML cells python-docx read as EMPTY**, so the replication package's Table 2 has 2 blank symbol cells (`compare_tables_v34.py` now reports exactly those 2). LEFT FOR THE AUTHOR: package is under RRR review; fix = regenerate the Table 2 static block (`gen_static_blocks.py` → `static_blocks.do` → `splice_static_blocks.py`) + rerun Stata step 19.
- Upstreamed to docxkit rather than written into the paper: **`Table.grid_rows`** (the rectangle — horizontal span repeated, vertical continuation carrying its origin's text) and public `package.text_parts` / `testing.DOCUMENT|FOOTNOTES`.

**Round-5 author Word edits INTEGRATED + JITED manuscripts resynced (2026-08-14, commit f5cbff9, NOT yet pushed — 2 commits ahead of origin/master).** The author hand-edited `flop_trade_model_v34.docx` in Word on 2026-07-17 (rev 18) *after* the last JITED sync; those 7 edits sat uncommitted for a month and are now in `add_calibration_v34.py`: abstract rewording (turn→convert, We develop→This paper develops, Because hardware…, "prices, including"), "not the places"→"not the ones", "Cheap electricity alone", sovereignty premium "that raises delivered costs", "translate into export competitiveness", "four regime combinations", Prop 3 "because they raise world prices, making imports more expensive", cost-ranking "+indicating that low production cost alone is not sufficient…", "extends the logic of sovereignty", welfare "modest relative to". Also FIXED a phantom-diff source: the §-lead-in rule (~line 6542) wrote an explicit `Pt(12)`/TNR on the 22 italic run-ins although Normal is already 12pt TNR — Word strips redundant run props on save, so every round-trip produced 22 bogus FORMAT entries. Gate `docxkit compare --expect-clean` = 0; residuals are only the dynamic version stamp, U+2032 prime, and Word-stripped `m:sty="i"`. 324/324 tests (1 assertion updated: welfare "small"→"modest"), citations 0 broken/0 orphan, flake8 unchanged vs baseline. Backup kept: `Documents/_backup_20260814_useredits5.docx`. **STILL-OPEN BLOCKERS (unchanged):** `[TODO – insert ORCiD iD]` and `[TODO – insert RRR DOI/URL]` in `JITED_manuscript_with_author_details.docx` + `JITED_title_page.docx`; cover letter has an optional suggested-reviewers TODO. Re-upload to the Routledge portal is a manual author action.

**JITED UN-SUBMITTED → both editorial issues RESOLVED & verified; ready to re-upload (2026-07-16).** Manuscript "Cheap Energy Might Not Be Enough: A Trade Model of AI Compute Services" was un-submitted by JITED (notice saved as `Documents/JITED_submission/Submission_incomplete.docx`) for TWO reasons: (1) **missing in-text citations to Appendices A, C & G**; (2) **not anonymized** for double-blind. BOTH fixed in committed anon manuscript (commit ffd5b69, 2026-07-14, "Cite appendices A, C, E, G in text"): verified all of A–G now cited in body (A→"Table A1 (Appendix A)", C→"Table A3 (Appendix C)", G→"Appendix G develops a symmetric specification"; B/D/E/F likewise). `JITED_manuscript_anonymous.docx` verified fully clean for double-blind: no Lokshin/Torre/McDaniel/Artuc anywhere (body/footnotes/metadata/track-changes), blank core author, empty Manager/Company, no acks, no headers/footers → **ready to re-upload as-is**. **Still-open BLOCKERS (only in the NON-anon `JITED_title_page.docx` + `JITED_manuscript_with_author_details.docx`, both JITED-required):** `[TODO – insert ORCiD iD]` (need value from user) and `[TODO – insert RRR DOI/URL once assigned]` (likely not yet assigned — WB-RRR verification still open). Loose ends: `reply_to_data_editor_3.md` uncommitted (adds line "v34 attached"; separate WB-RRR track, not yet sent); untracked clutter (backups, Data_Source.docx, Letter_Ivailo.docx). Re-submission itself is a manual Routledge-portal action for the user.

**RETARGETED to JITED — submission package built + pushed (2026-07-08, through e57b2a3 on origin/master).** Journal decision made: **JITED** (Journal of International Trade & Economic Development, T&F, rjte20) over The World Economy — best fit for a formal trade+development model w/ calibration; IF ~2.56; no word limit; **format-free** initial submission (keep author-date refs as-is; T&F style applied post-acceptance); **double-anonymous**; $150 submission fee; submits via **Routledge Submission Portal**. Package in `Documents/JITED_submission/`: **both required manuscripts** — `JITED_manuscript_anonymous.docx` (from `--anon`) + `JITED_manuscript_with_author_details.docx` (from new `--author-details` flag: keeps author+ack footnote, drops version stamp, adds affiliation + Statements-and-Declarations block after keywords) — plus `JITED_cover_letter.docx`. `JITED_title_page.docx` now OPTIONAL/superseded (its content is embedded in the with-author-details manuscript). Front-matter built by `Programs/build_jited_frontmatter.py`; manuscripts by `add_calibration_v34.py --anon` / `--author-details`. Author decisions baked in: AI-declaration = text-editing assistance only; funding = none; data availability = WB RRR; keywords trimmed 7→6 (dropped "electricity costs"). Anonymized manuscript via new `add_calibration_v34.py --anon` flag (omits author/ack-footnote/version-stamp, blank metadata, writes `_anon.docx`, skips commit; also `--no-commit`). **Open TODOs before upload:** insert ORCiD + RRR DOI/URL on title page; optional suggested reviewers in cover letter; confirm submission date; pay $150 fee. **REJECTED at WBER → v34 revision APPLIED (2026-06-13, pushed b9df2ad).** All 7 targeted edits from `Downloads\v33_targeted_revision_edits_1.md` are in `add_calibration_v34.py` → `flop_trade_model_v34.docx`.

**v34 manual copy-edits integrated (2026-07-08, committed 915cd16).** User hand-edited `flop_trade_model_v34.docx`; 23 changed paragraph-blocks folded into the generator via `/integrate-edits` (compare_docx `--expect-clean` residuals were only the live version stamp + 2 generator-correct glyphs U+2032 prime / en-dash). Incl. a paragraph SPLIT: the SecNumCloud/World Bank(2025) tail of the §6.2 welfare-discussion ¶ became its own paragraph; `link_citations` auto-restored the WorldBank2025 hyperlink Word stripped. Fixed a Word artifact: stopped setting redundant run-level bold on Heading 1 runs (style carries it) — line ~6437 `run.bold = None`. Updated 3 relationship tests to the reworded prose. Grammar fixed (e57b2a3): "would likely to be larger" → "would likely be larger". 324/324 pass. Backups: `Documents/_backup_20260708_useredits4.docx` + `_useredited.docx` (keep until user confirms).

**Reference/notation cleanup — findings A3/A4/A5 (2026-07-08, committed 44989d4).** A3: added Borenstein (2012) + Davis and Hausman (2016) as linked ref entries; footnoted the 4 data sources (EMBER/Agora Energiewende/BDEW/OECD Energy Policy Review) fn25-style (make_footnote id=90 — Word renumbers by position). A4: regime (iii) ID → λjk. A5: applied user's stated "six-then-et-al" house convention LIST-WIDE (Sastry 19, Calcaterra 14, Straub 9) — **this reverses the prior documented "spell out all authors" style**; if user only wanted Sastry, restore Calcaterra/Straub. Stojkoski C.A.→C. Hidalgo; subtitle italics extended past colon (World Bank 2025, Barroso); fixed ref sort so single-author precedes same-name multi-author (`key=x.lower().replace(' ','￿')` — Deloitte before Deloitte and Google). Citations 65→67, 0 orphans. GOTCHA: generator MIXES literal-unicode and `\uXXXX`-escape source text for the same glyphs (λ/quotes = escapes at some lines, literal í/– at others) — use `python -c "print(repr(line))"` to disambiguate before exact-match edits; Read escapes non-ASCII in its DISPLAY so it can't distinguish the two.

**RRR verification round 2 RESOLVED (2026-06-12, pushed 02e24e2).** Round-2 report `Documents/reproducibility_report_RR_EUR_2026_669.pdf` failed 5 exhibits (Tables 3, A1, A2, A3, A6). All five fixed and now reproduce **cell-for-cell** vs the typeset v33 docx (verification gate: `work/rrr_round2/compare_tables.py` = 0 diffs; ground truth extracted by `extract_paper_tables.py`). Reply drafted: `reply_to_data_editor_3.md` (not yet sent). Zip rebuilt via `git archive HEAD Replication` (94 files, 1.93 MB). Project folder `F:\onedrive\__documents\papers\_Submitted\FLOPsExport\`. Remote: `github.com/sfgunkin/flops_export` (master).

## Overview
Academic paper on international trade in compute services (FLOPs). Models how countries with cheap electricity can export computational services.

## Key Files
Project root: `F:\onedrive\__documents\papers\_Submitted\FLOPsExport\` (paths below relative to root)

**Active code (`Programs/`)**
- `add_calibration_v34.py` — **Current generator** (v33 + WBER-revision edits)
- `add_calibration_v33.py` — Previous version kept for diffing (v32 also retained)
- `test_paper_values.py` — Paper values test suite (324 tests, 43 classes, ~4600 LoC). Last 4 classes (TestArithmeticReconciliation/CrossSectionConsistency/SemanticFrame/SurfaceLint) implement Layers 0/2/3/4 of [[paper-verification-protocol]] — the error classes the WBER review caught that data↔prose tests miss (CANONICAL registry + $1.44B reconciliation, cross-section quantifier/adjective agreement, denominator/scope frame, balanced-paren + %-in-body lint). All 7 v33 errors are in the mutation corpus and confirmed caught.
- `generate_figures.py` — SVG+PNG for Figures 1 and 1b
- `calibrate_model_v3.py` — Core calibration (81 countries, construction fix)
- `Stata/` — 16-file pipeline (00_master.do, 01_prep_*.do, ...)

**Active outputs (`Documents/`)**
- `flop_trade_model_v33.docx` — **Current paper version**
- `flop_trade_model_v33_clean.docx`, `_title.docx`, `declarationStatement.docx` — Submission-package artifacts (May 20)
- `flop_trade_model_v32.docx` — Previous published version
- `flop_trade_model_v8.docx` — Base template (all generators modify this)
- `flop_trade_presentation.pptx` — Active slide deck
- `_archive/` — All older docx versions (v18-v31, _tc, _base), edit-integration sidecars, backups

**Data (`Data/`)**
- `calibration_results_v3.csv` — 85 countries ranked by c_j
- `calibration_regimes_v3.csv` — Regime assignments
- `dc_capacity_estimates.csv` — MW capacity for 86 countries (demand shares)
- `country_results_v29.csv`, `tableA3_v29.csv` — v29 floor-removal snapshots (now baked into v33)
- `xi_scenarios.xlsx`, `xi_calibration_test.xlsx`, `form_b_simulations.xlsx` — Inputs read by v33 generator
- README.md documents the rest

**Pipeline outputs (`work/`)**
- `lrmc_symmetric/` — Symmetric LRMC pipeline outputs (build script, 8 CSVs, diff report, Appendix E.1 text)

**Deleted in 2026-05-21 prune** (recoverable via `git show <sha>:Programs/_archive/<name>`)
- `add_calibration_v20.py`…`v31.py`, `compute_v29.py`, `phase2_xml_edits.py`, `phase3_table_updates.py`, `recalculate_tables_3ab.py`, `verify_v28_numbers.py`, `make_figure1_v31.py`, `ranking_protocol_v31.py`, `xi_scenarios.py`, `xi_calibration_test.py`, `form_b_simulations.py`, `extracted_v32.txt`

**External**
- `C:\Users\Ezhik\tools\integrate_word_edits.py` — Compare user-edited .docx against script baseline (use with `/integrate-edits` skill)
- `C:\Users\Ezhik\Downloads\PROTOCOL_symmetric_lrmc.md` — Protocol executed to produce v33 spec (2)
- `C:\Users\Ezhik\Downloads\referee_report_v32.md` — Working referee report being responded to in v33

## Document Structure (v24)
1. Title page (Abstract, JEL: F14/F18/L86/O14/O33/Q40, Keywords) — no page number
2. Introduction
3. Related Literature — 3 paras (trade/dev econ, DC location, compute governance + IO of cloud)
4. Model Setup
   - 3.1 Production Technology and Cost Structure (Eq 1, K̄_j capacity ceiling)
   - 3.2 Trade Costs (Eq 2: bilateral λ_{ij})
   - 3.3 Global Compute Demand (Eq 4: q_k = ω_k · Q, training/inference split with α)
   - 3.4 Sourcing and Market Equilibrium (Eqs 5-6: sourcing rule, p_T, inference price)
5. Equilibrium Properties (Props 1-5: taxonomy, concentration, λ*, shadow value, nesting)
6. Data (calibration approach paragraph after Demand)
7. Calibration and Results (was "Calibration and Discussion")
   - 6.1 Parameter calibration
   - 6.2 Cost Rankings and Trade Patterns (trade flows, demand centers, sovereignty, welfare)
8. Robustness, Caveats, and Extensions
   - 7.1 Robustness to parameter variation (sensitivity, hardware share, uniform λ, tiers)
   - 7.2 Caveats and omitted frictions (GPU controls, water, fiscal, endogenous prices, GPU upgrades, cost of capital)
   - 7.3 Extensions (edge computing)
9. Conclusion (split into 3 paragraphs: model summary, results, developing countries)
References (~48 citations)
Figure 1 (model structure diagram), Table 1, Appendix heading
Table A2 (85 countries, landscape)
Appendix B: Model Derivation (B.1-B.6, Eqs B.1-B.5)
Appendix C: Sensitivity Analysis (Table A3)
Appendix D: Kyrgyzstan DCF (Tables A4-A6, Risks)
Appendix E: Construction Cost Regression (Table A7)

## Equations (v32: 6 main + PUE display + HHI display + 5 appendix)
- (1): Cost c_j = PUE(θ_j) · γ · p_{E,j} + ρ + η + p_{L,j} / (D · H), where p_{L,j} = per-GPU construction cost ($/W × 700 W)
- PUE display (unnumbered, §3.1): PUE(θ_j) = φ + δ · max(0, θ_j − θ̄)
- HHI display (unnumbered, Prop 2): HHI_T = Σ_j (K_{T,j}/Q_{T,X})² via omath_para()
- (2): Bilateral sovereignty λ_{ij} = α₁·G_{ij} + α₂·(1-R_{ij}) + α₃·S_{ij}
- (3): ξ_j^{eff} = G^ω × R^{1−ω} (ω=0.50, no floor — floor removed in v29)
- (4): Demand q_k = ω_k · Q
- (5): Sourcing j*_s(k) = argmin
- (6): Inference price p_I^f(k)
- (B.1)-(B.5): Marginal exporter, inference MC, capacity allocation, DWL components

## Word Generation Preferences
- **Equation punctuation**: Display equations are part of the sentence. End with comma if followed by "where" clause, period if ending the sentence.
- **No first-line indent**, **full justification**, spacing 0pt before/8pt after
- **OMML** for all math — helpers: _mr, _v, _t, _msub, _msup, _msubsup, _nary, _limlow
- Display equations in borderless 2-col table (centered eq + right-aligned number)
- References: hanging indent (0.5"/-0.5"), single space, 0pt before/4pt after
- Journal/book titles in italic (ITALIC_IN_REFS dict + find_italic_portion)
- Citations: blue underline, cross-linked (bookmark + hyperlink, CITE_MAP/REF_KEY_MAP)
- Headings: H1 = blue (#2F5496), H2 = blue italic
- **PAGE NUMBERS RULE**: Always add page numbers — right-aligned footer, 10pt Times New Roman, `different_first_page_header_footer=True`, no number on title page, Introduction starts on page 2 (page break before Heading 1). Use PAGE field code in footer.
- Page breaks before Appendix and References
- Table A1: autofit window (pct/5000), 8 cols (no ISO3), meaningful headers
- Footnotes: lxml etree manipulation of footnotes.xml (init_footnotes/make_footnote/flush_footnotes)
- **Abstract/JEL/Keywords block**: 0.5" left+right indent, single line spacing (1.0), full justification. JEL separated from abstract by ~20pt (space_after=8 on abstract + space_before=12 on JEL). Keywords space_before=2.

## Technical Notes
- v8.docx has sections 1-5; scripts renumber and insert new sections
- v3 calibration FIXED construction cost bug: multiply GPU_TDP_KW × 1000 (kW→W for $/W data)
- PermissionError if Word has file open — save to new filename
- Footnotes use lxml to parse/modify footnotes.xml part, write back via _blob before save
- **BACKUP-BEFORE-REGENERATE RULE**: Before EVERY script run that overwrites the .docx:
  1. Copy the current .docx to `_backup_<timestamp>.docx` in the same folder
  2. Run the script (generates new .docx)
  3. After generation, diff the new .docx against the backup to verify no user edits were lost
  4. Keep the backup until the user confirms the new version is correct
  5. If user asks to "integrate changes" first, ALWAYS do that BEFORE any other edits to the script — never run the script until integration is complete
- **INTEGRATION-FIRST RULE**: When the user says "integrate my changes", this is the HIGHEST PRIORITY task. Do NOT make other script edits (hyperlinks, formatting, refactoring) until integration is complete and verified. The user's manual Word edits are at risk of being overwritten by any script run.
- **METADATA RULE**: Always set `doc.core_properties.author = 'Michael Lokshin'` before saving.
- **FIGURE PLACEMENT RULE**: Always place figures after the References section, never inline in the body text. Number sequentially (Figure 1, Figure 2, ...) in order of first textual reference.
- **TABLE/FIGURE NOTES RULE**: All notes paragraphs under tables and figures must have `alignment = WD_ALIGN_PARAGRAPH.LEFT` to prevent Word from stretching the last line (justified text stretches short final lines).
- **TABLE PAGE BREAK RULE**: Every table must start on a new page. Set `paragraph_format.page_break_before = True` on the table title paragraph.

## Calibration Results (v3, 85 countries)
- Cheapest globally (observed): Iran ($1.41/hr), Turkmenistan ($1.42), Kyrgyzstan ($1.43)
- Cost-recovery top 5: KGZ ($1.58), CAN ($1.59), ETH ($1.60), XKX ($1.60), TJK ($1.60)
- Pure cost: 39 full import, 42 hybrid, 1 domestic (total 82 in regimes CSV; 85 in calibration)
- With sovereignty (λ=10%): shifts most to domestic

## Evolution
- v13: Initial iceberg with δ_T and δ_I
- v14: Single δ, equations 2a/2b
- v15/v17: New Intro, Literature, OMML, τ notation, 26 refs
- v16/v18: Sovereignty, Props 1-2, taxonomy, Data, 82 countries, 32 refs, footnotes, formatting
- v16 text tightening (Referee #2): ~30% word-count reduction, 32→30 refs, 10 footnotes
  - Intro: consolidated demand stats (2→1 para), shortened training/inference, Kyrgyzstan arithmetic→footnote, tightened labor/option-value
  - Lit review: 5→3 paras (deleted IEA/GS/EPRI repeat, dropped Melitz sentence, merged value-chain para)
  - Section 3 opening: cut GPT-3/4 examples, amortization arithmetic→footnote, trimmed redundancy
  - Calibration: governance 7→2 paras (merged caveats+institutional+regulatory+infrastructure), model extensions 4→1 para
  - Conclusion: removed training/inference re-explanation, shortened developing-countries para
  - Removed orphaned refs: MarketsandMarkets (2025), Melitz (2003)
  - Round 2: Applied track changes (rephrase intro, simplify Section 3.1, remove Flucker sentence, simplify F_j/Data)
  - Round 2: τ per ms notation, PUE dimensionless, ρ decomposition, ad valorem→proportional, Table 1→Table A1
  - Round 2: Added training duration, latency threshold l̄, China chip stack footnote (fn 8)
  - Round 3: Removed ALL em dashes (→ commas, colons, parentheses), added DC investment footnote (fn 3)
  - Round 3: Lambda calibration para (bilateral, Iran/sanctions example), merged short paragraphs
  - Round 3: 2pt spacing before equations, "This paper makes" instead of "We make"
  - Footnote sequence (v21, 16 total): 1(disclaimer) 2(DC investments) 3(Kyrgyz arithmetic) 4(FLOPs definition) 5(PUE simplification) 6(H100 amortization) 7(China chips) 8(DC capacity proxy) 9(agentic inference) 10(HHI range) 11(HHI definition) 12(DCCI markets) 13(latency/Deloitte) 14(sovereignty conservative) 15(PUE cap sensitivity) 16(IMF subsidies) — note: Kyrgyz seasonal power footnote may have shifted
  - R2 Major Issue 2: Added demand calibration q_k = ω_k·Q via GDP PPP shares, Eq (5), trade flow results
  - R2 Major Issue 3: Added Corollaries 1 (λ*), 2 (train⊆inf exporters), 3 (HHI_T≥HHI_I)
  - AI language cleanup: removed "unprecedented", "Crucially", "pathway", "The key insight", "on paper"
  - Data files added: wb_gdp_per_capita_ppp_2023.csv, wb_population_2023.csv

## Demand Calibration Results
- **MW-capacity-based ω** (v20+): USA (43.1%), CHN (25.6%), IND (2.9%), CAN (2.6%), AUS (2.1%)
  - Uses `dc_capacity_estimates.csv` (86 countries, MW from Synergy Research/IEA/Cushman & Wakefield)
  - China corrected from 3.9% (DC count) to 25.6% (MW capacity) — 6.5x correction
  - Total 124.5 GW ≈ Synergy Research 122.2 GW global figure
- Old DC-count-based: USA (47%), DEU (4.6%), GBR (4.5%), CHN (3.9%), CAN (2.9%)
- Training unconstrained: Iran captures 99.8% (HHI_T = 0.9979)
- Inference top: Kyrgyzstan, Canada, Algeria
- Welfare cost of full sovereignty: 9.5% of weighted avg spending
- Counterfactual 20%: +27 countries domestic, training exports → 0%

## Capacity-Constrained Results (v20, cost-recovery baseline)
- Parameters: Q_TOTAL = 60B GPU-hrs, ALPHA = 0.50, K_BAR_SCALE = 1000 (5% grid)
- **Cost-recovery preferred baseline**: pure-cost run first, then adj_costs re-run
- **Cost-recovery (λ=0)**: p_T = $1.578, 2 exporters (KGZ+CAN), HHI_T = 0.93
- **Cost-recovery (λ=10%)**: p_T = $1.58, 1 exporter (KGZ), HHI_T = 1.00
- **Inference (cost-recovery)**: CAN 46%, KGZ 26%, XKX 6%, GBR 3%, IND 3%
- Efficiency-adjusted top 5: NOR, CAN, FIN, SWE, ISL
- Kyrgyzstan DCF: NPV $353M, IRR 17.6%, payback year 6

## v24 Changes (bilateral λ_{ij} + ξ decomposition)
- **ξ decomposition**: ξ_j^{eff} = geometric mean of governance × grid quality; sanctions removed from ξ
- **Bilateral λ_{ij}**: α₁·G_{ij} (geo=0.08) + α₂·(1-R_{ij}) (reg=0.04) + α₃·S_{ij} (sanctions=0.10)
- **Demand tiering**: Tier 1 sovereign 10%, Tier 2 regulated 20%, Tier 3 commercial 70%
- **Geopolitical blocs**: Western/Allied, China-Aligned, Non-Aligned (inter-bloc distance matrix)
- **Regulatory compatibility**: EU adequacy, APEC CBPR, DEPA membership
- **Table 3**: single 13-col landscape table (merged from old 3a+3b); specs (1) Raw, (2) CR, (3) Bilateral, (4) Uniform, (5) FDI
- **Equation renumbering**: New eqs (2) λ_{ij} and (3) ξ^{eff}; old 2→implicit, 3→4, 4→5, 5→6
- **Key results**: bilateral welfare 4.7% (vs uniform 17.0%); bilateral HHI_T = 0.46 (vs uniform 1.00)
- **Regime types (bilateral)**: 2 T+I exporters, 5 inference hubs, 7 hybrid, 7 domestic, 64 full importers

## Recent Edits

### Full-package validation vs paper + RRR review (June 13, 2026, pushed b6e069d)
ALL 11 table exhibits now verified against the v34 manuscript with **0 cell
differences** (`work/rrr_round2/compare_tables_v34.py`; report in
`work/rrr_round2/VALIDATION_REPORT.md`, mapped to review RR_EUR_2026_669).
Strict cell equality for 9 exhibits; numeric-at-printed-precision for A5
(years ×1e6, 1dp) and A7 (3dp coefs/SEs, region-dummy row map, base region
2b omitted in paper). Static Tables 1/2/A4/A8 in step 19 are now GENERATED
from the docx cells (`gen_static_blocks.py` → `static_blocks.do` →
`splice_static_blocks.py`); old A8 had a stale workload taxonomy, A4/T2
different row sets. GOTCHA: Stata `export delimited` writes embedded LFs
unquoted (splits CSV records) — emit typographic in-cell line breaks as
spaces; comparison folds whitespace runs (\s+ also catches U+2009/U+00A0).
Stability: two consecutive full runs → byte-identical CSVs for all 11
exhibits (only .dta embedded timestamps + log differ). 5 flagged exhibits
byte-identical v33↔v34 (prose-only edits). 314/314 prose tests pass.

### v34 — WBER-rejection targeted revisions applied (June 13, 2026, pushed b9df2ad)
Forked `add_calibration_v34.py` from v33 (stamp/output/auto-commit → v34) and
applied all 7 edits from `Downloads\v33_targeted_revision_edits_1.md`:
- **Edit 0** (user opted IN): abstract +2 sentences ("Credibility is priced
  twice…levers are financial and regulatory").
- **A1**: new intro ¶ after megaprojects ¶ — Kyrgyzstan paradox hook
  ("We ask why, and what would have to change").
- **A2**: replaced "necessary but not sufficient" ¶ — verdict-first, two
  channels, "eliminate nearly all their exports", "Section 8 sets out the
  policy levers".
- **D**: (i) paren-close + (iii) $1.3→$1.4 were ALREADY in from June 3
  integration; applied (ii) average→total and bumped $1.4→**$1.44** billion
  (kept the U+2009 thin space before "billion" — house style; plain-space
  string searches MISS it).
- **C1**: conclusion opener leads with the finding (no "In this paper").
- **C2**: welfare framing locked ("high in aggregate dollars but modest as a
  share (about {welfare_pct:.1f} percent)" — kept DYNAMIC via demand_data,
  which IS in write_conclusion's signature).
- **B**: new conclusion ¶ (financing levers / regulatory credibility /
  rent capture, SecNumCloud+IRAP, Kyrgyzstan Appendix D rent point).
Tests: NO assertions touched the edited prose (relationship-test design);
only 4 docx-filename fixture refs v33→v34 + test_version_stamp_v34.
314/314 pass. flake8 baseline-clean (4 E501s pre-exist in v33 too).
v33 docx left untouched; v34 is a new file. Verified all new sentences
present & all replaced phrasings absent in the docx.

### RRR round-2 fail fixed — 5 exhibits now cell-exact (June 12, 2026, pushed 02e24e2)
Report RR_EUR_2026_669 failed Tables 3/A1/A2/A3/A6. Root causes were all in the
EXPORT/sensitivity layer, not the model: (3/A2) exported c_j without η=$0.15 and
in merged layout vs paper's per-spec-sorted blocks with Type+flags; (A1) k̄ in
GPU-hours not MW, ω misscaled, Cost-Rec p^E column missing; (A3) old v28-style
scenario file vs paper's ρ∈{1.36,1.30,1.42} design; (A6) scenario loop omitted
GPU depreciation (~$240M NPV of tax shield) + GPU-value insurance.
Fixes (mirrored in Replication/code/ AND Programs/Stata/):
- **14_kyrgyzstan_dcf.do**: scenarios re-run the FULL model via shared `dcf_run`
  program; base case asserted == main NPV ($353,362,628). Labels use U+2212.
- **19_export_tables.do**: full paper-exact recomputation transcribed from
  add_calibration_v33.py — 56-entry SUBSIDY_ADJ, WACC bands+income groups,
  SANCTIONED6 (IRN RUS BLR PRK SYR TKM), blocs/EU27/APEC9(TWN!)/DEPA3,
  DEVELOPING43, dc-capacity k̄ = MW×(1000/γ)×8766×0.7 (NOT grid×1000!), the
  3 equilibria (raw/CR/bilateral-CR λ_min), simple (L̄=200) + bilateral (no
  latency cone!) inference, EE/IE/DD/II classification, exact formats/sorting.
  Key gotchas: Python equilibrium uses CSV c_j_total+η (not recomputed comps);
  table values recomputed from comps in Python term order; stable sort with CSV
  row order as tiebreak; paper's A2 name-map lacks "United States of America"
  (prints "United States of A.") while Table 3 maps it to USA — mirrored via
  `_shortname mapped3|mappeda2|plain`.
Validation: extracted all 5 exhibits' cells from v33 docx → compare_tables.py
0 diffs; full 19-step run_all.do clean (Stata 19, ~9 min); all previously-
passing headline numbers unchanged. README §2 fidelity rewritten (steps 15–17
re-scoped as mechanism implementations; step 19 owns all exhibits).
Replication/temp/ now gitignored. 4 commits, zip rebuilt, pushed.
**Next: send reply_to_data_editor_3.md; then apply v34 revision edits.**

### WB RRR reproducibility verification — DAS, preprocessing scripts, % edits, intermediates bundled (June 2–5, 2026, pushed to cd9ccfc)
Long session responding to the WB Reproducible Research Repository data editors.
First committed the uncommitted May 29 work (Stata steps 15–19, solve_tagged
refactor, `Replication/` package, submission artifacts, final Wave 5 docx) as 3
logical commits; `FLOPsExport_Replication.zip` is **gitignored** (regenerable
build artifact, rebuilt with `zip -r`, ~2.0 MB).

**Data-editor request #1 — DAS + share preprocessing scripts.** Added
`Replication/preprocessing/` with **portable** copies (paths via
`pathlib.Path(__file__).resolve().parents[1]`) of `process_temperature.py`
(ERA5→`country_temperatures.csv`), `process_latency.py` (WonderNetwork pings→
`country_pair_latency.csv`), and `predict_construction_costs.py` (DCCI+WDI→
`predicted_construction_costs.csv`, reproduces shipped file byte-for-byte).
**Deliberately did NOT ship `process_electricity.py`**: `country_electricity_prices.csv`
= the master `non_european_prices.csv` = Eurostat + EIA **+ ~20 manually-compiled
non-European "research" rows** (GlobalPetrolPrices/regulators, incl. KGZ); the
script alone produces a truncated file, so electricity provenance is documented
in the DAS instead. Wrote a full **Data Availability Statement** (README §6),
filled from project git history (data assembled **Feb 2026**; aux ξ-caches Apr
2026). Honestly labeled authors'-compilation/estimate inputs: `dc_capacity_estimates.csv`
(~41/86 rows = "DC count × regional avg", ~20 anchored to Synergy/CBRE/Cushman/
Arizton/Mordor/IEA per its `source` col), `seismic_zones.csv` (authors' binary
GSHAP/USGS-informed coding, not a download), `reliability_index.csv` (authors'
index). Found **RIPE Atlas NOT used** — latency is WonderNetwork only (old README
was wrong). Drafted `reply_to_data_editor.md`.

**June 3 Word edits integrated** (via integrate-edits skill / `integrate_word_edits.py`):
28 substantive changes. Dominant pattern = **spell out "%" → "percent" in MAIN
BODY prose (§1–8 only)**; tables, table notes (¶178 keeps `HIC 8%`…), footnotes,
and appendices KEEP "%". Also wording fixes (economies of scale, Weighting, merged
Germany/France/UK inference clause [made conditional on shared hub], straight-line
amortization sentence, welfare-paren fix, $1.3→$1.4 B, "compresses"→"diminishes",
etc.). ¶12 "exceed 3%"→"3 percent" applied after a follow-up confirm. **Skipped**:
version stamp; ¶74 `0.04–0.07` en-dash→hyphen (Word autocorrect); 26 citation
hyperlink-styling run_format diffs; 3 equation token DIFFs = script-correct Unicode
(− U+2212, ′ U+2032) vs degraded ASCII. Updated 5 static-text tests that asserted
old "%" strings (77%/8%/18%/20%/premium-to-20%). **314/314 pass.** Note: a
**pre-commit hook runs the full test suite**; the generator also **auto-commits**
the docx+script on each run ("Auto-save v33").

**Data-editor request #2 — verify from raw data.** Raw is large/proprietary
(ERA5 .nc 110 MB, WonderNetwork pings 49 MB **proprietary**, ripe_atlas 38 MB).
Initially prepped a DDH deposit (`DDH_archive/` + DDH metadata + form-ready
upload metadata), then user decided **NOT to use DDH**. Final approach: bundle the
4 small intermediates into `Replication/intermediate_datasets/` (byte-identical to
`data/`) with `metadata.md` (provenance + variable data dictionaries) + folder
README; de-DDH'd all in-package docs. Rewrote `reply_to_data_editor_2.md`:
intermediates redistributed in the package (archived in RRR = stable repository),
no separate deposit. `DDH_archive/` kept at repo root (obsolete, retained for
reference). New skill memory added: [[feedback_integrate_edits_robust]].

### Stata reimplementation to reproduce ALL paper tables (May 29, 2026)
User wanted the Stata-only package to reproduce every published table. The
published tables are actually built by the Python generator (symmetric-LRMC +
bilateral + WACC), so the Stata pipeline (v32/13-country) didn't match. User
chose **reimplement in Stata** + **qualitative match** standard. Added 5 steps
(all transcribing the Python constants/logic; validated via stata-runner):
- **15_symmetric_lrmc.do** — v32 (13) + EMBER grid-CI×2024-carbon-price (43) +
  cross-subsidy add-backs → symmetric p_E, recompute c_j. Top-5 KGZ/ETH/XKX/CAN/
  TJK ✓, p_T=$1.598 (≈paper $1.604). NOTE: solver clears on c_j+ETA (ranking
  unaffected by uniform ETA; forgot ETA first → p_T was $1.448, fixed).
- **16_wacc_channel.do** — income-group WACC bands (HIC8/UMIC12/LMIC15/LIC18) +
  CRF annuity. Reproduces EXACTLY: HIC ρ=$1.581, LIC $1.874, gap $0.293. Table 3 col4.
- **17_bilateral_lambda.do** — 85×85 λ_ij from bloc(W/C/N)+EU/APEC/DEPA+sanctions,
  per-buyer training sourcing. **PARTIAL/training-side proxy only**: HHI_T≈0.58,
  welfare≈1.7% — does NOT match published bilateral 4.7%/0.46 (those include
  inference + full DWL). Documented as indicative in README.
- **18_construction_regression.do** — OLS ln($/W)~ln gdp_pcap+ln pop+urban+seismic
  +region dummies; 52-city→ISO map via strpos (ASCII-safe). N=37, R²≈0.48. Table A7.
- **19_export_tables.do** — writes all 11 tables (1,2,3,A1–A8) to output/table*.csv;
  static tables (1,2,A4,A8) as definitional content.
All 19 steps run clean end-to-end. Bugs fixed during build: step15 ETA, step17
missing `clear` before each `input` block. README §2 has a per-table fidelity
table. Constants live in the .do files (carbon prices, GRID_CI_2024, income
groups, blocs, EU/APEC/DEPA) — transcribed from add_calibration_v33.py.

### Stata pipeline refactor — solve_tagged wrapper (May 29, 2026)
DRY + robustness refactor of the solver-call boilerplate. Added `solve_tagged`
to `_solver_program.do`: runs `solve_equilibrium`, forwards its r() scalars, and
suffix-tags the 3 output vars (exporter_share/shadow_value/is_exporter) with an
**exact-name-only** drop (varabbrev forced off locally → immune to the
abbreviation bug by construction). Steps 08 (`_lam0`,`_sov`) and 09 (`_cr`,
`_cr_sov`) now call `solve_tagged, lambda(...) suffix(...)` — removed all 12
manual renames + 2 dead `cap drop` lines. Step 12 still calls solve_equilibrium
directly (single call, no tagging). Applied to both Programs/Stata/ and
Replication/code/. Re-validated via stata-runner: ALL STEPS COMPLETE, every
headline number identical bit-for-bit (DCF NPV $353,362,628, etc.).

### Stata replication package built + pipeline bug-fixed end-to-end (May 29, 2026)
Built self-contained `Replication/` folder (user choices: Stata-only pipeline,
all data included as-is, self-contained folder, generic clean package):
- `run_all.do` — portable master (sets `global root` from `c(pwd)`, all params
  in one place; ported from `Programs/Stata/00_master.do`).
- `code/` — 14 step do-files + `_solver_program.do` (NOT the original
  00_master.do; run_all.do replaces it).
- `data/` — full copy of `Data/` (212MB). Stata reads only 8 analysis-ready
  CSVs; the 3 large raw files (ERA5 .nc 110MB, wondernetwork pings 49MB,
  ripe_atlas 37MB) are upstream-only (Python preprocessing, out of scope) but
  included per user choice. README flags this.
- `output/` — shipped with reference results from the validated run.
- `README.md` — quick-start, step→table map, data-source table, scope note.

**Validated end-to-end via the stata-runner agent** (Stata batch fails from the
shell — see [[feedback_stata_batch_shell]]). Found & fixed **4 pre-existing bugs**
in the Stata pipeline (it had clearly never been run to completion). Fixed in
BOTH `Programs/Stata/` (source) and `Replication/code/`:
1. `06_regime_assignment.do`: `list in 1/5`/`1/10` → `r(198)` when `contract`
   left fewer rows. Fixed to `if _N>0 list in 1/`=min(N,_N)'`.
2. **varabbrev bug (steps 8–11):** vars renamed to `*_lam0`/`*_cr`, then a bare
   `cap drop shadow_value` (varabbrev ON, Stata default) abbreviation-matched and
   silently deleted the renamed copy → `r(111)`. Fixed via `set varabbrev off`
   in run_all.do + 00_master.do, plus a save/restore guard in `_solver_program.do`.
3. `10_inference_sourcing.do`: tempfile key renamed `best_inf_source`→`iso3` for
   a display loop, then merged on `best_inf_source` → `r(111)`. Fixed: rename key
   back before save.
4. step 10→11 key mismatch: `inference_sourcing.dta` saved with `iso3_k` (from
   postfile) but step 11 merges `1:1 iso3`. Fixed: rename `iso3_k`→`iso3` before
   save (only step 11 reads it; nothing after the save uses iso3_k).

**Validated headline numbers (all match paper):** cost-recovery top-5 KGZ/CAN/
ETH/XKX/TJK (13-country spec); training p_T=$1.592, HHI_T=0.29; reliability top-5
CAN/NOR/FIN/SWE/ISL; full-sovereignty welfare cost 6.0%; **Kyrgyzstan DCF NPV
$353M / IRR 17.6% / payback Yr 6** (exact match to Appendix D). 6 sensitivity
scenarios.

**Scope caveat (documented in README):** Stata `09_cost_recovery` is the
13-country (v32-era) cost-recovery spec; the v33 published headline top-5 uses
the symmetric-LRMC 56-country refinement (Appendix G) built separately in Python
(`work/lrmc_symmetric/`), which is NOT in this Stata package.

### Reference author-name format — all-but-last inverted (May 29, 2026, auto-commit 2118803)
User clarified house style: 3+ author refs invert EVERY author except the last
(`Liu, Z., Wierman, A., Chen, Y., Raber, B., and J. Moriarty.`), NOT the
first-inverted-only form. Reformatted all 15 multi-author entries that were
still first-inverted-only (Barroso, Biglaiser, Calcaterra (14 authors),
Chandramowli, Flucker, Hausmann, Helpman, Katz, Lehdonvirta, Liu, Pilz, Sastry
(19), Sevilla, Stojkoski, Straub (9)). Alvarez/Arkolakis/Aykut/Bailey were
already correct (Wave 5). Hersbach keeps "et al." (42 authors). Kept each first
author's inversion stable so REF_KEY_MAP/ITALIC_IN_REFS prefixes still match;
verified no italic title/venue runs lost (Katz/Sastry/Sevilla correctly have no
italic — arXiv/report quoted titles). Rule now recorded in
[[feedback-paper-formatting-conventions]]. 314/314 pass, citation audit clean.

### Reference-list audit + et-al fixes (May 29, 2026, auto-commit 43f08b0)
Ran the `econ-reference-validator` agent over the `new_refs` block. Reference
LIST (bibliography) house style = spell out ALL authors (Calcaterra has 14
spelled out); in-text uses "et al." Four list entries improperly used "et al.":
- **Sastry et al. (2024)** arXiv:2402.08797 — spelled out all 19 authors
  (Sastry…Coyle), verified from arXiv. Title stays quoted (arXiv, not a journal).
- **Chandramowli (2024)** — entry was WRONG (title "Impact of Emerging
  Technologies on Electricity Demand and Prices" / publisher "Rhodium Group
  Analysis" — misattributed). Real source: ICF report *Power Surge: Navigating
  US Electricity Demand Growth*, 5 authors (Chandramowli, Cook, Mackovyak,
  Parmar, Scheller), Oct 2024. Switched to report style (italic title via
  ITALIC_IN_REFS — updated the existing `'Chandramowli'` key from 'Rhodium
  Group Analysis' to the new title; do NOT add a 2nd key, F601). In-text 19%
  wholesale-price-by-2028 claim matches ICF/Utility Dive.
- **Hersbach et al. (2020)** ERA5 — KEPT "et al." (42 authors, impractical;
  core QJRMS 146(730):1999–2049 confirmed correct).
- **Straub et al. (2026)** WB Infrastructure Foundations — RESOLVED (auto-commit
  f4d8b75): user supplied the full team; now spelled out as "Straub, S., H. He,
  Y. Li, X. Lyu, J. Steinbuks, E. Vergara Cobos, C. Dann, M. García-Santana, and
  H. Selod. (2026)." Title italic via existing ITALIC_IN_REFS['Straub'].
  (The report PDF is NOT in Literature/; only the Aykut EMDEs report cites it,
  also as "et al." — `Data_Centers_are_Good.pdf` = the Alvarez et al. 2026 NBER
  paper, cover confirms WP 35194 / May 2026 / 4 authors, Alvarez entry verified.)
- **Net result: the ONLY "et al." left in the reference LIST is Hersbach (ERA5,
  42 authors), kept deliberately.**

Also fixed: **Korinek & Stiglitz (2021)** title "AI, Globalization…" →
"Artificial Intelligence, Globalization…" (NBER 28453 confirmed correct).
Verified and left unchanged: **Alvarez et al. (2026)** NBER **35194 is correct**
(NBER is in w35xxx for 2026 — agent's "too high" guess was wrong). Left Sevilla
"arXiv Working Paper No." label alone (not an et-al issue; user just reviewed it).

flake8 clean, 314/314 tests pass, citation audit clean (0 broken/orphan), all
italic runs verified in docx.

### v33 Wave 5 copy-edits integrated (May 29, 2026, auto-commit 12631ca)
Integrated a fresh batch of user Word copy-edits into `add_calibration_v33.py`
(the Wave 4 edits I first saw in a stale git diff were already in the script —
that diff was comparing against an outdated committed `_user_edited.txt`
baseline, not real pending work; the fresh `integrate_word_edits.py` run is
ground truth). Applied 14 edits:
- ¶15: "model, making three contributions" → "model and makes three contributions"
- ¶31: inserted "the" before "UN General Assembly"; "mutual data-adequacy
  agreement" → "mutual data adequacy agreement"
- ¶74: "intra-bloc pair with data-adequacy" → "with data adequacy"
- ¶95: "Countries combining" → "Countries that combine"; "regardless of the
  choice of parameter" → "regardless of the chosen parameter"
- ¶100 (endogenous-prices caveat): "in every horizon" → "across all horizons";
  "counties that ever host…3.9 percent level effect" → "counties that have ever
  hosted…3.9 percent effect"
- ¶103: "the cost at which capital can be financed" → "the cost of financing capital"
- 6 reference entries reformatted: Anderson "J.E."→"J." (×2); Arkolakis/Aykut/
  Bailey invert 2nd author ("A. Costinot"→"Costinot, A." pattern, last author
  stays "First Last"); Caoui "E. H."→"E."
- fn (demand proxy): "would predict, while" → "would predict. At the same time,"
- fn (latency cone): inserted prose "there exists some country" before the ∃ omath
- fn (cost-recovery): "For Ethiopia, it uses" → "Ethiopia uses"

Also fixed a latent back-link bug: both Anderson CITATIONS anchors were the
ambiguous prefix `'Anderson, J.E.'`, so `find_ref_key` mapped both refs to the
same bookmark. Made both anchors fully specific (`'Anderson, J. and E. van
Wincoop'` / `'…and D. Marcouiller'`) and updated the two ITALIC_IN_REFS keys to
match. Generation now reports "Fixed 3 orphan back-link(s)"; citation audit clean.

Skipped (noise, per established precedent): all `run_format` underline/font_color
deltas adjacent to citations (Word hyperlink styling); the ¶74 `0.04–0.07`
en-dash→hyphen (Word autocorrect — same para keeps `0.4–0.6` en-dash); the ¶3
version-stamp + abstract-format "changes" (dynamic timestamp shifts fuzzy
paragraph alignment by one). Equation audit: 3 token DIFFs were all script-correct
Unicode (− U+2212, ′ U+2032) vs degraded ASCII in the user doc — NOT edits to adopt.

flake8 clean. 314/314 tests pass. Citation count unchanged at 53 (ref list);
new untracked `Literature/Data_Centers_are_Good.pdf` left alone (not requested).

### v33 polish + Alvarez integration (May 13–14, 2026, pushed 1601edd)
Two waves of integrate-edits within the v33 doc.

**Wave 1 — new §7.2 paragraph "Form of the sovereignty wedge"**
Inserted before "Cost of capital" in §7.2. Three inline `omath(p,
[_msub('λ', 'jk')])` calls render λ_{jk}. Notes that the ad valorem
form is a simplification (gov cloud certs / sanctions are fixed-cost
entry margins), λ_{jk} is treated as fixed though shocks are
stochastic, and a Monte Carlo with stochastic λ_{jk}+fixed costs is
left to future work. Resists premature abstraction — kept three
explicit `omath` calls rather than a `_lam_jk()` closure (CLAUDE.md
"three similar lines beats a premature abstraction").

**Wave 2 — user Word edits integrated (12 changes)**
- fn 1: acknowledgements added (Ivan Torre, Christine Ann McDaniel,
  Erhan Artuc)
- ¶13: "FLOP exporting" now followed by gloss "where FLOP denotes
  floating-point operations, the standard unit of computational work"
- ¶32: "literatures" → "bodies of literature"
- ¶74: "rather than assigned" → "rather than being assigned"
- ¶84: Oxford-comma join for shadow-value list (changed
  `", ".join(mu_labels)` to `', '.join(mu_labels[:-1]) + ', and ' +
  mu_labels[-1]` when len ≥ 2)
- ¶90: removed stray closing ")" after "above-world-price costs"
- ¶91: "significant in aggregate dollars" → "high in aggregate dollars"
  (also updated `test_welfare_cost_qualified` assertion)
- ¶99: "Fiscal sustainability is a concern: …" split into two new
  sentences ("Regulated tariffs … raising concerns about financial
  sustainability. Exporting compute at scale …")
- ¶100: inserted Alvarez et al. (2026) sentence on US data-center
  revenue → local electricity prices (+0.9% per log unit, 3.9% level
  effect on retail prices in ever-hosting counties)
- ¶103: "specification the advantage … compresses substantially," →
  "specification, the advantage … compresses,"
- ¶104: "host-country financial exposure" → "the host country's
  financial exposure"
- New reference: Alvarez, F., Argente, D., Chow, J., and D. Van Patten.
  (2026). "Data Centers and Local Economies in the Age of AI: A
  Shift-Share Approach." NBER Working Paper No. 35194. CITATIONS,
  ITALIC_IN_REFS, and references list all updated.

Skipped: 25 underline/font_color "None → True/1F3864" run-format
changes adjacent to citations — confirmed Word hyperlink-styling
noise, not user intent. Also skipped: 0.04–0.07 en-dash → hyphen in
¶74 (paragraph still has 0.4–0.6 en-dash; was a Word autocorrect
artifact, not a real edit).

Citation count 48 → 51. Test count unchanged at 314. flake8 clean.

### Test suite update — prose-agnostic invariants (Apr 23, 2026)
Added `TestProseAgnosticRelationships` class (16 tests) + 3 new
fixtures (`docx_para_texts`, `iso_to_name`, `docx_tables_v33`).
Suite 298 → 314 tests. Categories covered: cross-ref resolution
(Table/Figure captions), numbering density (main 1..6 and B.1..B.5
equations as 1×2 tables), Table A1/A2 cell ↔ data matching, WACC
inline formula round-trip, CAPEX share consistency, parenthetical
and HHI bounds, percent-decimal membership test with curated
literature-cited allow-list, anti-regression for v28 floor and v32
Canada-second phrasings. Key lesson: the existing `docx_text`
fixture concatenates table cells into prose via `<w:t>` run
extraction — new `docx_para_texts` strips `<w:tbl>` blocks first.
Extending the skill `write-paper-tests` with these patterns.

### v33 — Referee response (Apr 17–18, 2026, auto-commits through f930d61)
Responses to `referee_report_v32.md` implemented end-to-end in a single
script fork:

**Issue 4.3 — Symmetric LRMC cost-recovery (commit history: 51e0984…d6cb2c4)**
- `SUBSIDY_ADJ` extended from 13 → 56 countries (13 IMF-based developing +
  43 OECD/HI symmetric adjustment). 29 middle-income developing economies
  retain observed tariffs.
- Carbon adders: EMBER 2024 grid CI × 2024 ETS prices (EU ETS $70.94,
  UK $47.32, Canada $58.48, US weighted $3.81, NZ $39.50, SGP $18.60;
  KR/JP/AU/IL/CL/MX/TR/CO zero — <$10/tCO₂ effective).
- Cross-subsidy add-backs: DEU $0.038 (EEG), FRA $0.015 (ARENH),
  USA $0.015 (Borenstein 2012, Davis-Hausman 2016), KOR $0.020 (KEPCO),
  ESP/ITA/NLD/BEL $0.010 each, JPN 0.
- **New Appendix G** "Symmetric LRMC Construction" (6 paragraphs,
  `write_lrmc_appendix()` inserted after Appendix F workload).
- **New top-5 spec (2)**: Kyrgyzstan, Ethiopia, Kosovo, Canada, Tajikistan
  (was KGZ, CAN, ETH, XKX, TJK). Canada drops rank 2→4 on $0.008/kWh
  carbon adder. Poland +21, Germany +10, USA +10, France +12; Nordic/Swiss
  move ≤ 2 positions. p_T = $1.604/hr, HHI_T = 0.986.
- Pipeline outputs in `work/lrmc_symmetric/` (build script + 8 CSVs +
  DIFF_REPORT + appendix_E1_text.md), fully tested.

**Issue 4.2 — Sovereignty premium weight justification (commit 9d72aeb)**
- §5 "Sovereignty premium" paragraph gains explicit calibration targets:
  intra-bloc + data-adequacy → λ≈0; typical cross-bloc no-agreement →
  λ∈[0.04, 0.07]; adversarial/sanctioned → λ→∞. Plus Benz-Jaax 16%
  upper bound + Table 3 uniform robustness reference.

**Issue 3.3 — Theoretical scaffolding for λ_{ij} (commit d6cb2c4)**
- Two new §3.2 paragraphs after equation (2):
  - Functional-form layer: Anderson and van Wincoop (2003) justifies
    the multiplicative (1+λ) wedge; additive G/R/S decomposition per
    Benz-Jaax iceberg structure.
  - Microfoundation layer: Anderson and Marcouiller (2002), Antràs
    (2003) — incomplete-contracts / insecure-trade framework.
    G_ij proxies dispute-resolution willingness; R_ij proxies
    enforceable data-handling floors; S_ij proxies no-enforcement.
- Three new references + ITALIC_IN_REFS entries.

**Issue 3.1 — WACC channel promoted to Table 3 + Introduction (commit f930d61)**
- New `WACC_BY_GROUP`: HIC 8% / UMIC 12% / LMIC 15% / LIC 18%
  (WB FY2025 bands). `INCOME_GROUP` maps all 85 ISO3s (43/28/13/1).
- `rho_hw_wacc(iso)` uses capital-recovery factor CRF(r,N); reproduces
  paper §7.2 exactly: $1.58/hr at 8%, $1.87/hr at 18%, $0.29 gap ≈ 4×
  top-20 electricity-cost spread.
- Table 3 extended from 9 → **12 columns** (4 spec blocks): (1) Raw,
  (2) CR, (3) Bilateral, **(4) CR + host WACC**. Each: Country / P_j / Type.
- Table 3 notes describe spec (4) and the four WACC bands.
- Introduction Para 11 now includes 3-sentence WACC bridge citing
  Calcaterra et al. (2024) and pointing to Table 3 col (4).

**Test suite**: 187 → 258 → **273 tests** (all passing). New classes:
`TestSymmetricLRMC*` (10 classes, 71 tests: Scope/CarbonPrices/
CarbonIntensity/CarbonAdder/CrossSubsidy/PriceEffect/Ranking/CostFormula/
Equilibrium/Files), `TestWACCChannel` (9 tests), `TestWACCPromotedInIntro`
(6 tests). Renames: `test_13_countries_adjusted` → `test_56_countries_adjusted`,
`test_version_stamp_v32` → `test_version_stamp_v33`. Prop 4 relaxed to
majority inclusion (symmetric LRMC adds cheap-but-remote training exporters
that fail latency-cone inference).

**Still open from referee report**:
- 3.2 — Welfare-framing reconciliation across §6.2 and §8
- 4.1 — Audience focus (subordinate JIE-style framing)
- 4.4 — HHI domain note (basis-points vs [0,1])
- 5.x — Minor polish batch (α notation clash, Fig 1 p_L→p_I symbol bug,
  K-bar rendering, EMDE expansion, share-sum rounding 76.9→77,
  HHI precision, "Watch This Space", anchor caps, repeated WB 2025,
  fn 4 street price, conclusion ¶4 overreach, abstract length)
- §6 Lit additions: Hummels-Schaur (2013), Grossman-Rossi-Hansberg
  (2008), Ferracane-van der Marel (2021), Sevilla et al. (2022)

### v32 (Apr 9-11, 2026, pushed 92283c0)
Major reviewer-response session. Key changes from v31:
- **Reviewer fixes (1a-1j)**: HHI formula fixed (display eq with proper Σ), PUE(θ) defined in §3.1, latency notation unified (l_{jk}/l̄, no d_{ij}), stray K̄j deleted, p_T* → p_T in Prop 1, λ seller/buyer clarification added, K_{I,j→k} notation defined in B.4, footnote 9 formal latency-cone condition
- **Reviewer fixes (2a-2i)**: Graphics (not Graphic), Heckscher-Ohlin attribution + H-O hybrid acknowledged, World Bank sentence rephrased, Deloitte and Google (2020), ADB (not ABD), G_{ij} ∈ [0,1] normalization stated, HHI 0.996 "dominant exporter" phrasing, uniform 20% + Greenland named, welfare gains (not losses) phrasing
- **§7 restructured**: 7.1 Robustness to parameter variation / 7.2 Caveats and omitted frictions / 7.3 Extensions; Katz et al. moved to §6.2
- **Notation audit**: Eq (1) construction term dimensionally fixed (p_{L,j} = per-GPU cost), footnote 7 Section 6→7, Q_{T,X} unified in Appendix B
- **Figure 1 replaced**: calibration strategy → model structure diagram (5-tier SVG); generate_figures.py added
- **Tests**: 119 → 172 (TestDocumentContent, TestCitationIntegrity, TestEquationStructure classes)
- **New helpers**: omath_para() for display-mode equations, _sq_frac() for HHI squared ratios
- **3 blank lines before JEL** on title page (protected from empty-paragraph cleanup)

### v24 edit integration (Feb 22-23, 2026, pushed fd2533a)
Multiple rounds of integrating user's manual Word edits into the generation script:
- **Section restructuring**: Sections renumbered (6→6/7/8), heading levels adjusted, content moved between sections
- **Paragraph moves**: Calibration approach to Section 5, tiering to Section 7.1, demand centers reordered
- **Text edits**: Removed duplicate intro paragraphs, condensed λ_{ij} examples, updated road map
- **Deletions**: "FLOP exporting is a form of value chain upgrading" sentence, Section 6 intro paragraph (N=85), sovereignty sentence from demand centers
- **Fixes**: Missing space ",as"→", as"; "such as"→"including"; empty ¶84 removed
- **Conclusion split**: Single long paragraph → two (results + developing countries)
- **Lint cleanup**: Fixed all flake8 errors (E128/E124/E127/E226/E303/E306/E501/E117/E241, F841 unused vars)
- **Cost-recovery countries (13)**: Algeria, Egypt, Ethiopia, Iran, Kazakhstan, Nigeria, Qatar, Russia, Saudi Arabia, South Africa, Turkmenistan, UAE, Uzbekistan
- Developing countries paragraph only created if runtime data produces content (prevents empty ¶84)

### v30 Table 3 merge (Feb 27, 2026, pushed ee2335e)
Merged Table 3a (cost specs, 11 cols portrait) + Table 3b (sovereignty specs, 7 cols) into single Table 3 (13 cols, landscape):
- **Dropped**: Δ column, λₖ* column, redundant tiered column (identical to bilateral)
- **Renumbered**: old (5) Uniform → (4), old (6) FDI → (5)
- **Layout**: Country + (1) Raw [cⱼ/Rank/Type] + (2) CR [cⱼ/Rank/Type] + (3) Bilateral [cⱼ/Rank/Type] + (4) Uniform [Type/Rank] + (5) FDI [Type]
- **Table A2** expanded to match (13 cols, all 85 countries)
- **Prose**: all Table 3a/3b refs → Table 3; column numbers updated; Table3b bookmark removed
- **Notes**: merged from both tables; tiering explanation kept as note

### v29 floor removal (Feb 26, 2026)
Executed 3-phase protocol from `floor_removal_protocol.md` to remove institutional floor (ξ_floor=0.30) from equation (3):
- **Phase 1** (`compute_v29.py`): New ξ_eff = G^0.50 × R^0.50; c_adj = ρ + (c_cr − ρ)/ξ; 85 countries + 5 sensitivity specs
- **Phase 2** (`phase2_xml_edits.py`): 7 paragraph XML edits (A-G) removing all "floor" text, OMML elements, Table A3 row deletions
- **Phase 3** (`phase3_table_updates.py`): Updated Tables A1, 3a, A2, A3 with new values
- **Key result change**: All top 15 now advanced economies (0 developing, was 6). KGZ drops from ~rank 1 to 79.
- **Efficiency-adjusted top 5**: Norway, Canada, Finland, Sweden, Iceland
- **Sensitivity**: 0 developing in top 15 across ALL omega values (0.30-0.85)
- **Table A3**: 5 specs (was 7) — Baseline, High governance, Low hardware, High hardware, Form A
- Output: `flop_trade_model_v29.docx`

### Earlier sessions (v21)
- Sessions 1-5: v20→v21 restructure, track changes, DCF bug fix, tool fixes, citation formatting
- See git history for details
