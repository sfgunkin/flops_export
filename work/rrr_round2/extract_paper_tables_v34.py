"""Extract ALL analytical/static table exhibits from the current paper docx
(v34) into CSVs under v34/, for full-package validation against the RRR
reproducibility review RR_EUR_2026_669.

Body iteration: a table is associated with the closest preceding "Table X."
title paragraph.  Figure 1 is a drawing, not a table, and is excluded (the
review classifies it as non-analytical).

Reading goes through docxkit (`tables.read_all`), not python-docx.  Reason,
from the toolkit's own field notes: reading a document's tables through
python-docx silently loses every cell whose text is a tracked insertion --
it returns ''.  These CSVs are the ground truth the Stata package is proven
cell-exact against, so a silent '' would read as a package failure.

docxkit rows are CELL-indexed (one entry per <w:tc>); the exhibits are
compared column-by-column against `export delimited` output, which is
grid-indexed, so a horizontally merged cell is expanded across the grid
columns it spans -- the same shape python-docx's `row.cells` produced, so
the emitted CSVs are unchanged.
"""
import csv
import os

from docxkit import text_of, utf8_stdout
from docxkit.find import body_elements
from docxkit.tables import read_all
from docxkit.testing import load_xml

utf8_stdout()

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(HERE, "..", "..", "Documents", "flop_trade_model_v34.docx")
OUTDIR = os.path.join(HERE, "v34")

TARGETS = {
    "Table 1.": "paper_table1.csv",
    "Table 2.": "paper_table2.csv",
    "Table 3.": "paper_table3.csv",
    "Table A1.": "paper_tableA1.csv",
    "Table A2.": "paper_tableA2.csv",
    "Table A3.": "paper_tableA3.csv",
    "Table A4.": "paper_tableA4.csv",
    "Table A5.": "paper_tableA5.csv",
    "Table A6.": "paper_tableA6.csv",
    "Table A7.": "paper_tableA7.csv",
    "Table A8.": "paper_tableA8.csv",
}


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    # A typographic line break inside a header cell is a <w:br/>, which
    # carries no text of its own, so a w:t/m:t sweep would weld the two
    # lines into one word ("Trainingdomestic production cost"). Give it a
    # newline to contribute, matching what these CSVs have always held;
    # the comparison harness folds whitespace runs anyway.
    xml = load_xml(DOCX).replace("<w:br/>", "<w:t>\n</w:t>")
    tables = {t.start: t for t in read_all(xml)}

    found = {}
    last_para_texts = []
    for kind, start, end in body_elements(xml):
        if kind == "p":
            txt = text_of(xml[start:end]).strip()
            if txt:
                last_para_texts.append(txt)
                last_para_texts = last_para_texts[-3:]
            continue
        label = None
        for recent in reversed(last_para_texts):
            for prefix in TARGETS:
                if recent.startswith(prefix):
                    label = prefix
                    break
            if label:
                break
        if label and label not in found:
            found[label] = tables[start].grid_rows(xml)
        last_para_texts = []

    for prefix, fname in TARGETS.items():
        out = os.path.join(OUTDIR, fname)
        if prefix not in found:
            print(f"NOT FOUND: {prefix}")
            continue
        rows = found[prefix]
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(rows)
        ncols = max(len(r) for r in rows)
        print(f"{prefix} -> v34/{fname}: {len(rows)} rows x {ncols} cols")


if __name__ == "__main__":
    main()
