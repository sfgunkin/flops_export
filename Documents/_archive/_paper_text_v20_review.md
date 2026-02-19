# Systematic Proofread: _paper_text_v20.txt

**Date:** 2026-02-18
**Scope:** Number consistency, forward/back references, duplicate/contradictory statements, style consistency, grammar/spelling, logical flow.

---

## 1. NUMBER CONSISTENCY

### 1a. Country count: 86 vs. "30 + 55 = 85"

- **[3] Abstract:** "Calibrating the model for 86 countries"
- **[60] Section 6, first sentence:** "The model is calibrated for [N] countries (30 in ECA, 55 non-ECA comparators)"
- **[79] Conclusion:** "86 countries"
- **[80] Conclusion:** "Across 86 countries"

**Issue:** 30 + 55 = 85, not 86. Either one of the sub-counts is wrong, or the total should be 85. Verify against the actual Table A2 row count.

### 1b. Top-5 cost-recovery ranking consistency

- **[62] Section 6:** "The five cheapest producers become Kyrgyzstan ($1.58/hr), Canada ($1.59/hr), Ethiopia ($1.59/hr), Kosovo ($1.60/hr), and Tajikistan ($1.60/hr)."
- **[70] Section 6 (reliability-adjusted):** "the five cheapest producers become Canada ($1.61/hr), Norway ($1.62/hr), Finland ($1.62/hr), Sweden ($1.63/hr), and Iceland ($1.64/hr)."

These are two different rankings (cost-recovery vs. reliability-adjusted), so the difference is expected and correct. No issue.

### 1c. Hardware cost share: "over 80 percent" vs. "roughly 94%"

- **[70] Section 6:** "hardware amortization dominates the per-GPU-hour cost, accounting for over 80 percent of the total"
- **[70] Section 6, same paragraph, a few sentences later:** "Because hardware amortization accounts for roughly 94% of engineering costs"
- **[80] Conclusion:** "hardware amortization is uniform and accounts for 94% of per-GPU-hour costs"
- **[164] Appendix C:** "hardware amortization accounts for approximately 94 percent of total cost"

**Issue:** Within [70], the text first says "over 80 percent" and then says "roughly 94%." These are in the same paragraph and appear contradictory. The 94% figure is used everywhere else. The "over 80 percent" appears to be an error or an earlier draft remnant. Should be harmonized.

### 1d. Demand shares arithmetic: do they sum correctly?

- **[58] Section 5:** "The five largest demand centers (United States of America (43%), China (26%), India (2.9%), Canada (3%), and Australia (2%)) account for 77% of global demand."

**Issue:** 43 + 26 + 2.9 + 3 + 2 = 76.9%, which rounds to 77%. This is fine. However, Canada (3%) is listed as larger than India (2.9%), but the text calls India the third-largest and Canada the fourth-largest by ordering. The ordering appears to be: US, China, Canada, India, Australia -- but India is listed third and Canada fourth in the parenthetical. Check whether Canada or India is actually third-largest; the current ordering (India before Canada in the list) contradicts the share sizes (3% > 2.9%).

### 1e. Inference supplier shares

- **[65] Section 6:** "the top five suppliers being Canada (46%), Kyrgyzstan (26%), Kosovo (6%), the United Kingdom (3%), and India (3%), collectively accounting for 84% of global inference demand"

**Issue:** 46 + 26 + 6 + 3 + 3 = 84%. Checks out.

### 1f. "87% of cloud computing exports"

- **[12] Introduction:** "the United States accounting for 87% of the global total (World Bank 2025)"
- **[18] Lit review:** "account for 87% of cloud computing exports (Stojkoski et al. 2024)"

**Issue:** The same 87% figure is attributed to World Bank (2025) in [12] and to Stojkoski et al. (2024) in [18]. These may be consistent if the World Bank report cites Stojkoski, but the reader sees two different sources for the same number. Verify or clarify attribution.

### 1g. "77% of colocation data center capacity"

- **[18] Lit review:** "high-income countries hold 77% of colocation data center capacity"
- **[58] Section 5:** "The five largest demand centers ... account for 77% of global demand"

These are different statistics (high-income countries' share of colocation capacity vs. top-5 countries' share of total demand), but the coincidence of "77%" in both could confuse readers. Not an error, but worth noting.

---

## 2. MISSING TEXT / GARBLED PLACEHOLDERS

### 2a. Missing dollar figure in [12]

- **[12] Introduction:** "Cloud computing exports already exceed  billion annually"

**Issue:** There is a blank space where a dollar amount should appear (e.g., "$XX billion"). The number was lost, likely a formula/field that did not render to plain text.

### 2b. Equations rendered as blanks throughout

Numerous paragraphs contain blank spaces where mathematical symbols, variable names, or equation numbers should appear. This is a systematic artifact of the text extraction (OMML/LaTeX not rendering to plain text). Examples:

- [22]: "Consider  countries" (should be "N countries")
- [23]: ", where  is the baseline PUE" (variable names missing)
- [25]: "where  is GPU power draw" (variable names missing)
- [32]: "where  if  and  if " (conditions missing)
- [34]: "Let  denote the volume" (variable missing)
- [40]: "Since , training is a homogeneous good" (condition missing)
- [46]-[50]: Proposition formal statements have blank variables
- [53]: "equations (2) and (3)" -- but earlier the text refers to "equation (1)" in [25]-[26]. Check that equation numbering in the actual document matches these references.

**Note:** These blanks are likely an artifact of the .txt extraction and not present in the .docx. However, it is worth verifying that the original document actually renders all equations correctly.

---

## 3. FORWARD/BACK REFERENCES

### 3a. Section references in the roadmap

- **[14]:** "Section 2 reviews the related literature. Section 3 develops the model... Section 4 derives the equilibrium properties... Section 5 describes the data. Section 6 calibrates the model... Section 7 concludes."
- Actual headings: Section 1 [7], Section 2 [15], Section 3 [19], Section 4 [44], Section 5 [52], Section 6 [59], Section 7 [78].

All section references match the actual heading numbers. Correct.

### 3b. Section 4 heading: "Equilibrium Properties Results"

- **[44]:** "4. Equilibrium Properties Results"

**Issue:** This heading is awkward -- "Properties Results" appears to be two nouns jammed together. Likely should be "Equilibrium Properties" or "Equilibrium Results" or "Equilibrium Properties and Results." Compare with [14], which describes Section 4 as deriving "the equilibrium properties." The heading has an extra word.

### 3c. Equation references

- **[26]:** "equation (1)" -- referring to the cost equation in [24]-[25]. Correct.
- **[53]:** "equations (2) and (3)" -- equation (2) is the delivered cost in [31]-[32], equation (3) is demand in [34]-[35]. Correct.
- **[57]:** "equation (2)" -- reliability index appears in the delivered cost equation. Correct.
- **[58]:** "equation (3)" -- demand equation. Correct.
- **[140] Table 1 notes:** "equation 2" -- correct.
- **[143] Table A2 notes:** "equation (3)" and "equation (4)" -- equation (4) is the sourcing rule in [38]. Correct.

No equation numbering errors found (to the extent verifiable from this text rendering).

### 3d. Table and Figure references

- **Table 1** referenced in [58] ("Table 1 reports all model parameters") and present at [139]. Correct.
- **Table A2** referenced in [55], [61], [73], [74], [77] and present at [142]. Correct.
- **Table A3** referenced in [74] ("Table A3 in Appendix C") and present at [165] under Appendix C. Correct.
- **Table A4** present at [169]. Not explicitly cross-referenced from main text, but part of Appendix D. Acceptable.
- **Table A5** present at [171]. Same.
- **Table A6** referenced in [174] and present at [173]. Correct.
- **Figure 1** referenced in [62] and present at [130]. Correct.
- **Figure 2** referenced in [65] and present at [133]. Correct.
- **Figure 3** referenced in [70] and present at [136]. Correct.

No missing table/figure references found. All exist and are cross-referenced.

### 3e. Appendix references

- **[43]:** "derived in Appendix B" -- Appendix B exists at [144]. Correct.
- **[45]:** "Full derivations appear in Appendix B." Correct.
- **[74]:** "Table A3 in Appendix C" -- Appendix C exists at [163]. Correct.

### 3f. Proposition references

- **[65]:** "confirming Proposition 2" -- Proposition 2 is about capacity constraints reducing concentration, and the HHI result confirms it. Correct.
- **[65]:** "consistent with Proposition 4" -- Proposition 4 is about shadow value of grid expansion. Correct.

No proposition reference errors found.

---

## 4. DUPLICATE OR CONTRADICTORY STATEMENTS

### 4a. Near-duplicate: "no formal framework" stated twice

- **[13] Introduction:** "no formal trade model of compute exists"
- **[20] Section 3 opening:** "no formal framework links production costs to trade patterns"

**Issue:** These are near-duplicates. The Section 3 opener repeats the gap statement from the Introduction almost verbatim. The phrasing in [18] (lit review) also ends with a similar claim: "has not been addressed." Consider whether [20] needs this restatement or could transition more directly.

### 4b. Contradiction within [70]: "over 80 percent" vs. "roughly 94%"

Already flagged above under 1c. The same paragraph says both. These cannot both be correct descriptions of the same quantity.

### 4c. Potential tension: Figure 2 description vs. Proposition 1 taxonomy

- **[46] Proposition 1:** Three regimes: exporter, domestic producer, importer.
- **[135] Figure 2 notes:** Four regimes: "full import," "import training + build inference domestically," "full domestic." Missing is a fourth regime (the text says "four trade regimes" but the notes only describe three categories).

**Issue:** The Figure 2 notes describe three regimes (dark blue, light blue, red) but the paragraph says "one of four trade regimes." This is inconsistent. Either the figure description is missing a regime, or the count "four" is wrong. (The missing regime is likely "export" -- countries that export training and/or inference.)

### 4d. Welfare cost of sovereignty: "6.0%" appears only in the conclusion

- **[80] Conclusion:** "at a demand-weighted welfare cost of 6.0% of average compute spending"

**Issue:** This specific number (6.0%) does not appear anywhere in the main body (Sections 4-6) or the appendices. It is introduced for the first time in the Conclusion. Key quantitative results should be presented in the Results section first, then summarized in the Conclusion. Either the number was cut from Section 6 in an earlier edit, or Section 6 needs to include this result.

---

## 5. STYLE CONSISTENCY

### 5a. Proposition numbering

Propositions 1-5 are numbered sequentially in [46]-[50]. The "Welfare cost of sovereignty" in [51] is not numbered as a proposition -- this appears intentional (it is a corollary/discussion, not a formal proposition). Consistent.

### 5b. Section numbering

Sections 1-7 are numbered correctly. Subsections 3.1-3.4 are present. Section 4 has no subsections. Section 5 has no subsections. Section 6 has no subsections. This is consistent.

### 5c. Paragraph numbering gap

- The paragraph numbering jumps from [82] to [84], skipping [83].

**Issue:** Paragraph [83] is missing from the sequence. This is likely an artifact of the extraction (an empty paragraph or page break), but worth verifying that no text was lost between the end of the conclusion [82] and the References heading [84].

### 5d. British vs. American spelling

- **[73]:** "behaviour" (British)
- Rest of paper uses American spelling conventions throughout.

**Issue:** "behaviour" in [73] should be "behavior" for consistency with the rest of the paper.

### 5e. Inconsistent use of "percent" vs. "%"

- **[70]:** "roughly 40 percent," "over 80 percent," "roughly 94%," "about 20%"
- **[164]:** "approximately 94 percent"

**Issue:** The paper mixes "percent" (spelled out) and "%" (symbol), sometimes within the same paragraph [70]. Pick one convention and apply it consistently.

---

## 6. GRAMMAR / SPELLING / MISSING WORDS

### 6a. Missing enumeration marker in three contributions

- **[13]:** "The paper makes three contributions. It decomposes the cost... Second, it calibrates... Third, it characterizes..."

**Issue:** The first contribution is introduced without "First," while the second and third use "Second" and "Third." Should begin "First, it decomposes..." for parallel structure.

### 6b. "Kyrgyz" context in [73]

- **[73]:** "competing with residential heating in winter (when Kyrgyz hydropower output drops)"

This is acceptable usage ("Kyrgyz" as adjective). No issue.

### 6c. Construction cost range wording in [61]

- **[61]:** "At the expensive end, Ireland ($1.28/hr) and Greenland ($1.32/hr) face high electricity prices."

**Issue:** These are described as being "at the expensive end," but $1.28 and $1.32 are total unit costs that are lower than the cost-recovery top-5 ($1.58-$1.60). The context is the observed-tariff (subsidized) ranking, so "expensive" is relative to the subsidized range. However, since costs under observed tariffs start at $1.41 (Iran) per [61], Ireland at $1.28/hr and Greenland at $1.32/hr would be *cheaper* than Iran, not at the expensive end. This seems contradictory to the stated ranking where Iran is cheapest at $1.41. Check whether Ireland and Greenland costs are correct; they appear to be construction-cost figures that were mixed up with total unit costs, or the ranking description is wrong.

**Update on re-reading:** The text says "the cheapest producer is Iran ($1.41/hr)... At the expensive end, Ireland ($1.28/hr)." If Iran is cheapest at $1.41, then Ireland at $1.28 would be even cheaper, not more expensive. This is a clear numerical error. Either the Ireland/Greenland figures are wrong, or they should be higher than Iran's $1.41 (e.g., perhaps $2.28 or $1.82?).

### 6d. Kyrgyzstan GDP figure

- **[66]:** "a country with a GDP of under $15 billion"
- **[12]:** "Kyrgyzstan's $3.8 billion in goods exports (World Bank 2024)"

GDP under $15 billion and goods exports of $3.8 billion are plausible and not contradictory (exports are a fraction of GDP). No issue.

### 6e. Sanctions exposure scoring

- **[57]:** "sanctions exposure (0 for unrestricted, 0.5 for comprehensive sanctions)"

**Issue:** The scale seems inverted from what would be expected. If the reliability index is a product, and sanctioned countries should have *lower* reliability, then sanctions exposure of 0.5 for sanctioned countries (multiplied) would halve the index -- which is the intended direction. But the label "0 for unrestricted" means unrestricted countries get a zero sanctions score, which when multiplied would make the entire reliability index zero. This seems like a description error: the text likely means the *sanctions penalty* is 0 for unrestricted (so the sanctions *component* fed into the product is 1.0 for unrestricted and 0.5 for sanctioned). The description is ambiguous and could confuse readers.

### 6f. UNCTAD (2025) in references but not cited

- **[124]:** UNCTAD. (2025). Technology and Innovation Report 2025.

**Issue:** This reference does not appear to be cited anywhere in the body text. It should either be cited or removed from the reference list.

### 6g. Cloudscene (2025) citation

- **[58]:** "449 in Cloudscene" -- cited in text
- **[89]:** Cloudscene. (2025). -- present in references. Correct.

### 6h. Deloitte and Google (2020) in references

- **[91]:** Deloitte and Google. (2020). "Milliseconds Make Millions."

**Issue:** This reference does not appear to be explicitly cited in the text. The text in [56] mentions "industry evidence that web-service revenue declines by 1% per 100 ms of additional latency" but cites no source for this specific claim. The Deloitte and Google (2020) report is likely the intended source for this statement but is not cited in-line.

---

## 7. LOGICAL FLOW

### 7a. Section 3 opening repeats literature gap

As noted in 4a, [20] re-states the gap already established in [13] and [18]. This creates a sense of repetition. The Section 3 opener could instead begin with "This section models compute as a tradable good..." without the redundant gap statement.

### 7b. Subsidy discussion appears late in Section 6

- The subsidy adjustment methodology is briefly introduced in [62] ("the calibration replaces subsidized tariffs with cost-recovery prices"), but the detailed subsidy discussion [72] appears much later, after the trade flow results [65]-[68] and the governance discussion [69]-[71].

**Issue:** The reader encounters cost-recovery results in [62] without understanding the full methodology, which is only explained in [72]. Consider moving [72] immediately after [62], or at least signposting it: "Section 6.X below details the subsidy adjustment."

### 7c. [70] is an extremely long paragraph

- **[70]** covers: EU regulation, US export controls, GPU access, grid reliability, reliability index, reliability-adjusted top-5, hardware cost shares (80% vs 94%), cross-country cost spread, governance quality, water scarcity, and liquid cooling.

**Issue:** This paragraph tries to do too much. It spans at least 8 distinct topics. Breaking it into 3-4 focused paragraphs would improve readability. (Flagging as a structural issue, not a style preference, because the paragraph's length makes it difficult to follow the argument.)

---

## 8. SUMMARY OF ISSUES BY SEVERITY

| # | Para | Issue | Severity |
|---|------|-------|----------|
| 1 | [60] | 30 + 55 = 85, not 86 | HIGH |
| 2 | [12] | Missing dollar amount ("exceed  billion") | HIGH |
| 3 | [61] | Ireland ($1.28) and Greenland ($1.32) listed as "expensive end" but cheaper than the stated cheapest (Iran $1.41) | HIGH |
| 4 | [70] | "over 80 percent" contradicts "roughly 94%" in same paragraph | HIGH |
| 5 | [135] | Figure 2 notes describe 3 regimes but says "four trade regimes" | MEDIUM |
| 6 | [80] | Welfare cost "6.0%" introduced for first time in Conclusion | MEDIUM |
| 7 | [13] | First contribution missing "First," before enumeration | MEDIUM |
| 8 | [44] | Section heading "Equilibrium Properties Results" appears malformed | MEDIUM |
| 9 | [58] | India (2.9%) listed before Canada (3%) -- order inconsistent with share sizes | MEDIUM |
| 10 | [73] | "behaviour" (British) vs. American spelling elsewhere | LOW |
| 11 | [70] | Mixes "percent" (spelled out) and "%" symbol in same paragraph | LOW |
| 12 | [20] | Near-duplicate of gap statement from [13] | LOW |
| 13 | [124] | UNCTAD (2025) in references but never cited in text | LOW |
| 14 | [91] | Deloitte and Google (2020) in references, likely uncited | LOW |
| 15 | [57] | Sanctions scoring description ambiguous (0 = unrestricted, multiplied into product would zero it out) | LOW |
| 16 | [12]/[18] | Same "87%" figure attributed to two different sources | LOW |
| 17 | [70] | Single paragraph covers ~8 distinct topics | LOW |
| 18 | [72] | Subsidy methodology detail appears far after first use of cost-recovery results | LOW |
| 19 | [83] | Paragraph number skipped (82 to 84) -- verify no text lost | LOW |

---

*End of proofread report.*
