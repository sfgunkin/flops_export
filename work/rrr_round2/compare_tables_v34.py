"""Full-package validation: compare EVERY table exhibit of the paper (v34)
against the replication package's exported CSVs, mirroring the RRR
reproducibility review's exhibit checklist (RR_EUR_2026_669).

- Strict cell-string comparison for Tables 1, 2, 3, A1, A2, A3, A4, A6, A8
  (the package exports these as the paper's exact cell strings).
- Numeric comparison for Table A5 (paper prints $ millions at 1 decimal;
  the package exports the raw year-by-year model dataset) and Table A7
  (paper prints coefficients/SEs at 3 decimals; the package exports full-
  precision regression output).

Usage: python -X utf8 compare_tables_v34.py
Exit 0 = every exhibit matches; 1 = differences (printed).
"""
import csv
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
V34 = HERE / "v34"
OUT = HERE.parents[1] / "Replication" / "output"

# (stata csv, paper csv, stata header rows to skip, paper header rows to skip)
STRICT = [
    ("table1_regime_taxonomy.csv", "paper_table1.csv", 0, 0),
    ("table2_model_parameters.csv", "paper_table2.csv", 0, 0),
    ("table3_rankings_top25.csv", "paper_table3.csv", 1, 2),
    ("tableA1_calibration_parameters.csv", "paper_tableA1.csv", 1, 1),
    ("tableA2_rankings_all.csv", "paper_tableA2.csv", 1, 2),
    ("tableA3_sensitivity.csv", "paper_tableA3.csv", 1, 1),
    ("tableA4_facility_spec.csv", "paper_tableA4.csv", 0, 0),
    ("tableA6_dcf_sensitivity.csv", "paper_tableA6.csv", 1, 1),
    ("tableA8_workload_classification.csv", "paper_tableA8.csv", 0, 0),
]


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [[c.strip() for c in row] for row in csv.reader(f)]


def norm(cell):
    """Fold whitespace runs (line breaks, thin/no-break spaces) to one space."""
    return re.sub(r'\s+', ' ', cell).strip()


def compare_strict(stata_name, paper_name, s_hdr, p_hdr):
    diffs = 0
    s_path = OUT / stata_name
    if not s_path.exists():
        print(f"[{stata_name}] MISSING package output")
        return 1
    s_rows = read_rows(s_path)[s_hdr:]
    p_rows = read_rows(V34 / paper_name)[p_hdr:]
    label = stata_name.split("_")[0]
    if len(s_rows) != len(p_rows):
        print(f"[{label}] row count differs: package={len(s_rows)} "
              f"paper={len(p_rows)}")
        diffs += 1
    for i, (sr, pr) in enumerate(zip(s_rows, p_rows), 1):
        ncol = max(len(sr), len(pr))
        for j in range(ncol):
            sc = sr[j] if j < len(sr) else ""
            pc = pr[j] if j < len(pr) else ""
            if norm(sc) != norm(pc):
                print(f"[{label}] row {i} col {j + 1}: "
                      f"package={sc!r} paper={pc!r}")
                diffs += 1
    if diffs == 0:
        print(f"[{label}] OK — {len(p_rows)} data rows, all cells match")
    return diffs


def compare_a5():
    """Paper Table A5 ($M, 1 decimal; Total row) vs kyrgyzstan_dcf export."""
    diffs = 0
    pkg = read_rows(OUT / "tableA5_dcf_cashflow.csv")
    hdr = pkg[0]
    idx = {name: hdr.index(name) for name in
           ["year", "total_capex", "revenue", "total_opex", "ebitda",
            "fcf", "cum_cf"]}
    years = {}
    for row in pkg[1:]:
        years[row[idx["year"]]] = {k: float(row[idx[k]]) for k in idx
                                   if k != "year"}
    paper = read_rows(V34 / "paper_tableA5.csv")[1:]
    cols = ["total_capex", "revenue", "total_opex", "ebitda", "fcf", "cum_cf"]
    tot = {c: 0.0 for c in cols}
    for r in paper:
        yr = r[0]
        if yr == "Total":
            expect = [f"{tot[c] / 1e6:.1f}" for c in
                      ["total_capex", "revenue", "total_opex", "ebitda",
                       "fcf"]] + [""]
        else:
            vals = years.get(yr)
            if vals is None:
                print(f"[tableA5] paper year {yr!r} missing from package")
                diffs += 1
                continue
            for c in cols:
                tot[c] += vals[c]
            expect = [f"{vals[c] / 1e6:.1f}" for c in cols]
        for j, e in enumerate(expect, 1):
            got = r[j] if j < len(r) else ""
            if norm(got) != norm(e):
                print(f"[tableA5] year {yr} col {j + 1}: paper={got!r} "
                      f"package-derived={e!r}")
                diffs += 1
    if diffs == 0:
        print(f"[tableA5] OK — {len(paper)} data rows (16 years + Total), "
              "all values match at the paper's precision")
    return diffs


def compare_a7():
    """Paper Table A7 (3-dp coefficients, SEs in parens) vs step-18 export."""
    diffs = 0
    pkg = read_rows(OUT / "tableA7_construction_regression.csv")
    hdr = pkg[0]
    vi, ci, si = hdr.index("variable"), hdr.index("coef"), hdr.index("se")
    est = {row[vi]: (float(row[ci]), float(row[si])) for row in pkg[1:]
           if row[ci] not in ("", "0") or row[vi] == "_cons"}
    rowmap = {
        "Intercept": "_cons",
        "ln(GDP per capita)": "ln_gdp_pcap",
        "ln(Population)": "ln_pop",
        "Urban population share": "urban_share",
        "Seismic zone indicator": "seismic_high",
        "East Asia & Pacific": "1.region_id",
        "Latin America & Caribbean": "3.region_id",
        "Middle East": "4.region_id",
        "North America": "5.region_id",
        "South Asia": "6.region_id",
        "Sub-Saharan Africa": "7.region_id",
    }
    paper = read_rows(V34 / "paper_tableA7.csv")[1:]
    for r in paper:
        var = r[0]
        key = rowmap.get(var)
        if key is None or key not in est:
            print(f"[tableA7] paper row {var!r} not mapped to package output")
            diffs += 1
            continue
        coef, se = est[key]
        e_coef, e_se = f"{coef:.3f}", f"({se:.3f})"
        if norm(r[1]) != e_coef:
            print(f"[tableA7] {var} coef: paper={r[1]!r} package={e_coef!r}")
            diffs += 1
        if norm(r[2]) != e_se:
            print(f"[tableA7] {var} se: paper={r[2]!r} package={e_se!r}")
            diffs += 1
    if diffs == 0:
        print(f"[tableA7] OK — {len(paper)} coefficient rows, all match at "
              "the paper's precision")
    return diffs


def main():
    n = 0
    for args in STRICT:
        n += compare_strict(*args)
    n += compare_a5()
    n += compare_a7()
    print(f"\nTotal differences across all 11 exhibits: {n}")
    return 0 if n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
