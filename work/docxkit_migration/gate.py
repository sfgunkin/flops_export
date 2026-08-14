"""Migration gate: the rebuilt paper must still BE the golden paper.

The docxkit migration is a refactor of how the paper is built and checked,
not a revision of the paper.  Every step is therefore gated on a
`docxkit.compare` of the rebuild against `golden_v34.docx`, frozen from
commit f5cbff9 (the submitted text).  Anything the diff reports other than
the dynamic version stamp is a regression the migration introduced.

    python work/docxkit_migration/gate.py            # rebuild, then compare
    python work/docxkit_migration/gate.py --no-build # compare what is on disk

Exit code is non-zero when the rebuild differs from the golden, so the call
can gate a commit.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from docxkit import utf8_stdout
from docxkit.compare import compare

utf8_stdout()

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "work" / "docxkit_migration" / "golden_v34.docx"
BUILT = ROOT / "Documents" / "flop_trade_model_v34.docx"
GEN = ROOT / "Programs" / "add_calibration_v34.py"

# The one paragraph that is SUPPOSED to differ between two builds: the
# version stamp carries a build timestamp.  Everything else must match.
STAMP = "v34  —"

# Report sections that describe a real difference in what a reader sees.
# `formula_format` is excluded on purpose: it fires only on Word's stripped
# `m:sty="i"` in a file Word has re-saved, and both sides here are builds.
REAL = ("structure", "text", "formula", "format", "hyperlinks",
        "integrity", "stripped_fields", "comments", "formula_format", "glyph")


def _is_stamp(entry: dict) -> bool:
    """True for the version-stamp paragraph, whatever section reports it."""
    for key in ("context", "text", "from", "to"):
        value = entry.get(key)
        if isinstance(value, str) and value.startswith(STAMP):
            return True
    return False


def main() -> int:
    if "--no-build" not in sys.argv:
        print("Rebuilding paper ...", flush=True)
        r = subprocess.run([sys.executable, str(GEN), "--no-commit"],
                           cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            sys.stdout.write(r.stdout)
            sys.stderr.write(r.stderr)
            print(f"FATAL: build failed (exit {r.returncode})")
            return 2

    if not GOLDEN.exists():
        print(f"FATAL: golden baseline missing: {GOLDEN}")
        return 2

    report = compare(str(GOLDEN), str(BUILT))
    failures = 0
    for section in REAL:
        entries = [e for e in report.get(section, []) if not _is_stamp(e)]
        if not entries:
            continue
        failures += len(entries)
        print(f"\n== {section.upper()} ({len(entries)}) ==")
        for e in entries[:20]:
            print("   ", str(e)[:300])
        if len(entries) > 20:
            print(f"    ... {len(entries) - 20} more")

    print("\n" + "=" * 60)
    if failures:
        print(f"GATE FAILED: {failures} difference(s) vs golden")
        return 1
    print("GATE PASSED: rebuild is the golden paper (version stamp aside)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
