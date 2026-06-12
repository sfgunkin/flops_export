"""Extract ground-truth tables from the published paper docx into CSVs.

Iterates the document body in order, tracking the most recent paragraph text,
and when a w:tbl is encountered, associates it with the preceding table-title
paragraph (e.g. "Table 3.", "Table A1." ...). Cell text is taken raw
(strip()'d). CSVs are written with utf-8-sig encoding.
"""
import csv
import os
import re

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(HERE, "..", "..", "Documents", "flop_trade_model_v33.docx")

TARGETS = {
    "Table 3.": "paper_table3.csv",
    "Table A1.": "paper_tableA1.csv",
    "Table A2.": "paper_tableA2.csv",
    "Table A3.": "paper_tableA3.csv",
    "Table A6.": "paper_tableA6.csv",
}


def para_text(p_elem):
    """Concatenate all w:t text in a paragraph, including text inside hyperlinks."""
    return "".join(t.text or "" for t in p_elem.iter(qn("w:t")))


def main():
    doc = Document(DOCX)
    found = {}
    last_para_texts = []  # keep a few recent paragraph texts (title may be 1-2 paras back)

    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            txt = para_text(child).strip()
            if txt:
                last_para_texts.append(txt)
                last_para_texts = last_para_texts[-3:]
        elif child.tag == qn("w:tbl"):
            # find which target (if any) this table belongs to
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
                rows = []
                for row in tbl.rows:
                    rows.append([cell.text.strip() for cell in row.cells])
                found[label] = rows
            # reset so a following untitled table doesn't reuse the title
            last_para_texts = []

    for prefix, fname in TARGETS.items():
        out = os.path.join(HERE, fname)
        if prefix not in found:
            print(f"NOT FOUND: {prefix}")
            continue
        rows = found[prefix]
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(rows)
        ncols = max(len(r) for r in rows)
        print(f"{prefix} -> {fname}: {len(rows)} rows x {ncols} cols")


if __name__ == "__main__":
    main()
