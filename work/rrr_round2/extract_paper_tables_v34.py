"""Extract ALL analytical/static table exhibits from the current paper docx
(v34) into CSVs under v34/, for full-package validation against the RRR
reproducibility review RR_EUR_2026_669.

Same approach as extract_paper_tables.py (body iteration; a table is
associated with the closest preceding "Table X." title paragraph; cell text
taken raw). Figure 1 is a drawing, not a table, and is excluded (the review
classifies it as non-analytical).
"""
import csv
import os

from docx import Document
from docx.table import Table
from docx.oxml.ns import qn

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


def para_text(p_elem):
    return "".join(t.text or "" for t in p_elem.iter(qn("w:t")))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    doc = Document(DOCX)
    found = {}
    last_para_texts = []

    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            txt = para_text(child).strip()
            if txt:
                last_para_texts.append(txt)
                last_para_texts = last_para_texts[-3:]
        elif child.tag == qn("w:tbl"):
            label = None
            for recent in reversed(last_para_texts):
                for prefix in TARGETS:
                    if recent.startswith(prefix):
                        label = prefix
                        break
                if label:
                    break
            if label and label not in found:
                tbl = Table(child, doc)
                rows = [[c.text.strip() for c in row.cells] for row in tbl.rows]
                found[label] = rows
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
