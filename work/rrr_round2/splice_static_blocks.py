"""Splice static_blocks.do into 19_export_tables.do, replacing the old
hand-written Table 1/2/A4/A8 blocks (the span from the Table 1 banner through
the Table A8 export line)."""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


def splice(do_path):
    frag = io.open(os.path.join(HERE, "static_blocks.do"),
                   encoding="utf-8").read()
    src = io.open(do_path, encoding="utf-8").read()
    banner_old = "// " + "═" * 78 + "\n// Table 1"
    banner_new = "// " + "=" * 78 + "\n// Table 1"
    start = (src.index(banner_old) if banner_old in src
             else src.index(banner_new))
    end_marker_new = ('export delimited using '
                      '"$output/tableA8_workload_classification.csv", '
                      'replace novarnames')
    end_marker_old = ('export delimited using '
                      '"$output/tableA8_workload_classification.csv", '
                      'replace')
    if end_marker_new in src:
        end = src.index(end_marker_new) + len(end_marker_new)
    else:
        end = src.index(end_marker_old) + len(end_marker_old)
    new = src[:start] + frag.rstrip() + "\n" + src[end:]
    with io.open(do_path, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    print(f"{do_path}: replaced {end - start} chars; file now {len(new)} chars")


if __name__ == "__main__":
    targets = sys.argv[1:] or [
        os.path.join(ROOT, "Replication", "code", "19_export_tables.do"),
    ]
    for t in targets:
        splice(t)
