---
description: Integrate manual Word edits back into the Python generation script
---

# Integrate Word Edits

You are integrating manual edits the user made in a Word document back into
the Python generation script that produces it.

## Step 1: Identify files

From conversation context, memory files, or by asking the user, determine:
- **Edited document**: the `.docx` file the user has been editing in Word
- **Generation script**: the `.py` file that produces the document
- **Baseline document** (optional): a previously generated `.docx` to compare against (avoids re-running the script)

If these are not clear, ask the user before proceeding.

## Step 2: Run the comparison tool

```bash
python C:/Users/Ezhik/tools/integrate_word_edits.py \
  --edited "<edited_doc>" \
  --script "<gen_script>" \
  [--baseline "<baseline_doc>"]
```

Read both stdout (the change table) and the `_word_edits.json` file it produces.

## Step 3: Present the change table

Show the user the full table of detected changes. Group them by type:
1. Text changes
2. Formula (OMML) changes
3. Paragraph formatting changes
4. Run formatting changes (bold, italic, etc.)
5. Inserted/deleted paragraphs

For each change, note the paragraph number and a short context snippet.

## Step 4: Apply changes to the generation script

For each change the user approves (default: apply all unless user says otherwise):

- **Text changes**: Find the corresponding `p.add_run('...')` or string literal
  in the script and modify it to match the edited text.

- **Formula changes**: Find the corresponding `omath(p, [...])` or
  `omath_display(doc, body, cursor, [...], eq_num=...)` call and update the
  OMML helper arguments (e.g., `_mr`, `_v`, `_t`, `_msub`, `_msup`, `_nary`)
  to produce the new formula.

- **Paragraph formatting** (`space_before`, `space_after`, `line_spacing`, etc.):
  Find the `mkp(...)` call or the line that sets `paragraph_format.space_after`
  etc., and adjust the value.

- **Run formatting** (`bold`, `italic`, `underline`, `font.size`, etc.):
  Find the relevant `add_run(...)` call and add/modify `.bold = True`,
  `.italic = True`, etc. on the run object.

- **Blank paragraphs inserted**: Add `p, cur = mkp(doc, body, cursor); p.add_run(' ')`
  (or equivalent) at the correct position in the script.

- **Paragraphs deleted**: Remove the corresponding `mkp(...)` / `add_run(...)` block.

### Skip logic
If a change appears to be a **prior Claude audit fix** (e.g., consistent
formatting normalisation, spacing standardisation applied across many
paragraphs), note it as "skipped (Claude audit fix)" and explain why.

## Step 5: Regenerate and verify

After applying changes to the script:
1. Run the generation script to produce a new document
2. Re-run the comparison tool against the user-edited doc
3. If unexpected diffs remain (e.g., stray `\n` line breaks vs paragraph breaks,
   wrong Unicode characters), fix them in the script and re-run until only
   intentional differences remain (title/timestamp are expected)

## Step 6: Automatic audit

After verification passes, audit the regenerated document for common issues.
Read the `_user_edited.txt` and `_script_baseline.txt` extracts and check:

1. **Paragraph splitting**: When the user split a paragraph, verify the script
   uses `p, cur = mkp(...)` for each new paragraph instead of `\n` within a
   single paragraph. Word paragraph breaks (`mkp`) ≠ in-paragraph line breaks
   (`\n`). A `\n` creates a `<w:br>` soft break which looks similar but differs
   semantically and will show up as a diff.

2. **Formula symbols**: Check that OMML formulas in changed paragraphs render
   correctly. Compare the Unicode text of formulas in the new baseline against
   the user-edited version. Watch for:
   - `\u2217` (∗) vs `*` (asterisk)
   - `\u2212` (−) vs `-` (hyphen-minus)
   - Superscript `\u2217` vs `*` in `_msubsup` calls (both work but must match)

3. **Orphaned content**: When text is moved between paragraphs (e.g., amortization
   sentence moved from Data to Calibration), verify:
   - The text was removed from the original location
   - The text appears at the new location
   - No duplicate content exists

4. **Citation consistency**: If edited paragraphs contain citations
   (parenthetical references like "Author Year"), verify they still appear and
   match entries in the CITE_MAP / REF_KEY_MAP so citation linking won't break.

5. **Footnote integrity**: If paragraphs with `make_footnote()` calls were
   modified, verify the footnote is still attached to the correct paragraph and
   the numbering sequence is consistent.

6. **Formatting preservation**: Spot-check that italic headers
   (`add_italic(p, 'Topic. ')`) and bold proposition titles
   (`r.bold = True`) are preserved in modified paragraphs.

Report any issues found and fix them before proceeding to the summary.

## Step 6b: Citation cross-reference audit

Run the citation audit tool on the regenerated document:

```bash
python C:/Users/Ezhik/tools/check_citation_links.py "<regenerated_doc>"
```

This checks:
1. Every in-text citation has a hyperlink to its reference bookmark
2. Every reference has a back-link to the in-text citation
3. No broken hyperlinks (pointing to non-existent bookmarks)
4. No orphan references (in reference list but never cited)
5. Unlinked citation-like text that should have been linked

Known limitations (not real issues):
- Equation bookmarks live in table cells — the tool may report them as missing
- Footnote citations (Google, UNCTAD, DOJ) live in `footnotes.xml` and may
  appear as orphan references — verify manually

Citation style rules:
- **3+ authors**: Always use "et al." (e.g., "Hausmann et al. 2007", never
  "Hausmann, Hwang, and Rodrik 2007"). Update both the CITATIONS list and
  any in-text `add_run()` strings.
- Both narrative "Author (Year)" and parenthetical "Author Year" forms must
  exist in CITE_MAP (auto-generated from CITATIONS).

## Step 7: Final summary

Present a table:

```
Change # | Action   | Reason
---------|----------|----------------------------------
1        | Applied  |
2        | Applied  |
3        | Skipped  | Claude audit spacing fix
4        | Applied  |
...
```

And report any remaining diffs from the verification run. If there are
unexpected differences, investigate and resolve them.

## Important notes
- Always read the generation script before making changes — understand the
  helper functions (`mkp`, `omath`, `omath_display`, `_mr`, `_v`, etc.)
- Preserve the script's coding style and conventions
- Do not reformat or refactor code beyond what is needed for the edits
- If the user-edited doc has the file locked (open in Word), the tool will
  attempt to close it via win32com — warn the user if this happens
- **Paragraph breaks vs line breaks**: Use `p, cur = mkp(doc, body, cur)` to
  start a new paragraph. Never use `\n` to simulate a paragraph split — it
  creates a soft line break (`<w:br>`) that is semantically different and will
  show up as a diff against the user's version.
- **Baseline safety**: The comparison tool snapshots the edited file before
  running the generation script (which may overwrite the same path). If using
  `--baseline`, ensure it points to a different file than `--edited`.
- **Track Changes**: The tool handles `<w:ins>` (includes text) and `<w:del>`
  (excludes text). If the user-edited doc has unresolved Track Changes, the
  tool will warn. The extracted text reflects the "accepted" state.
- **Noise filtering**: The tool filters format inheritance noise only in one
  direction: when the *script* sets an explicit value (e.g., `bold=True`,
  `space_before=0pt`) but *Word* shows `None` (inherited from style). The
  reverse — user sets explicit formatting and script has `None` — is treated
  as a real edit and reported. Formula XML noise (same Unicode, different XML)
  is also filtered.
- **Run formatting changes**: `underline: None → True` and `font_color` changes
  on citation text are typically from Word's hyperlink styling, not user edits.
  True user formatting changes are `bold`/`italic` on non-hyperlink runs.
