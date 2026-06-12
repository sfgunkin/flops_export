"""Compare Stata-exported paper tables against ground-truth cells extracted
from flop_trade_model_v33.docx (paper_*.csv built by extract_paper_tables.py).

Compares DATA cells positionally (header rows skipped on both sides, since
the Stata CSVs use plain ASCII variable names as headers while the paper
uses styled multi-row headers).

Usage:  python compare_tables.py
Exit code 0 = all cells match; 1 = differences found (printed).
"""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parents[1] / "Replication" / "output"

CHECKS = [
    # (stata csv, paper csv, stata header rows, paper header rows)
    ("table3_rankings_top25.csv", "paper_table3.csv", 1, 2),
    ("tableA1_calibration_parameters.csv", "paper_tableA1.csv", 1, 1),
    ("tableA2_rankings_all.csv", "paper_tableA2.csv", 1, 2),
    ("tableA3_sensitivity.csv", "paper_tableA3.csv", 1, 1),
    ("tableA6_dcf_sensitivity.csv", "paper_tableA6.csv", 1, 1),
]


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [[c.strip() for c in row] for row in csv.reader(f)]


def norm(cell):
    # collapse internal whitespace variants (thin/no-break spaces)
    return (cell.replace(" ", " ").replace(" ", " ")
            .replace("\n", " ").strip())


def main():
    n_diff = 0
    for stata_name, paper_name, s_hdr, p_hdr in CHECKS:
        s_path = OUT / stata_name
        p_path = HERE / paper_name
        if not s_path.exists():
            print(f"[{stata_name}] MISSING Stata output")
            n_diff += 1
            continue
        s_rows = read_rows(s_path)[s_hdr:]
        p_rows = read_rows(p_path)[p_hdr:]
        label = stata_name.split("_")[0]
        if len(s_rows) != len(p_rows):
            print(f"[{label}] row count differs: stata={len(s_rows)} "
                  f"paper={len(p_rows)}")
            n_diff += 1
        table_diffs = 0
        for i, (sr, pr) in enumerate(zip(s_rows, p_rows), 1):
            if len(sr) != len(pr):
                print(f"[{label}] row {i}: column count differs "
                      f"stata={len(sr)} paper={len(pr)}")
                table_diffs += 1
                continue
            for j, (sc, pc) in enumerate(zip(sr, pr), 1):
                if norm(sc) != norm(pc):
                    print(f"[{label}] row {i} col {j}: "
                          f"stata={sc!r} paper={pc!r}")
                    table_diffs += 1
        if table_diffs == 0 and len(s_rows) == len(p_rows):
            print(f"[{label}] OK — {len(s_rows)} data rows, all cells match")
        n_diff += table_diffs
    print(f"\nTotal differences: {n_diff}")
    return 0 if n_diff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
