#!/usr/bin/env python
"""Keep the JITED submission manuscripts in lockstep with the current v34 paper.

Single source of truth: ``Documents/flop_trade_model_v34.docx`` (built by
``add_calibration_v34.py``).  The two files the journal actually receives are
derived from the SAME generator:

    JITED_manuscript_anonymous.docx          <- add_calibration_v34.py --anon
    JITED_manuscript_with_author_details.docx <- add_calibration_v34.py --author-details

This script rebuilds both derived manuscripts from the current generator,
verifies that their paper body (everything from "1. Introduction" onward) is
IDENTICAL to the current main docx, and copies them into
``Documents/JITED_submission/`` only when their content actually changed.  A
.docx is a zip, and python-docx repacks the container on every save, so raw
bytes differ run-to-run even when nothing changed; comparison is therefore on
extracted paragraph text, never on file hashes.

Usage
-----
    python Programs/sync_jited_submission.py                # sync derived -> JITED
    python Programs/sync_jited_submission.py --rebuild-main # also rebuild+commit main first
    python Programs/sync_jited_submission.py --check        # verify only, never write

Exit code is non-zero if body-parity fails (a real content drift) so the call
can gate a commit or CI step.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import docx

# UTF-8 stdout so the Kyrgyzstan characters / subscripts in the paper print on
# a cp1252 Windows console instead of crashing.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover - older interpreters
    pass

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "Documents"
GEN = ROOT / "Programs" / "add_calibration_v34.py"
JITED = DOCS / "JITED_submission"

MAIN = DOCS / "flop_trade_model_v34.docx"

# (generator flag, generator output, canonical JITED submission filename)
DERIVED = [
    ("--anon", DOCS / "flop_trade_model_v34_anon.docx",
     JITED / "JITED_manuscript_anonymous.docx"),
    ("--author-details", DOCS / "flop_trade_model_v34_authordetails.docx",
     JITED / "JITED_manuscript_with_author_details.docx"),
]

BODY_ANCHOR = "1. Introduction"


def paras(path: Path) -> list[str]:
    """Non-empty stripped paragraph texts, in document order."""
    return [p.text.strip() for p in docx.Document(str(path)).paragraphs
            if p.text.strip()]


def body(ps: list[str]) -> list[str]:
    """Paper body: everything from the Introduction heading onward.

    Front matter (title, author line, version stamp, abstract/JEL/keywords, and
    -- in the author-details build -- the Statements & Declarations block) lives
    ABOVE the anchor and is intentionally allowed to differ between manuscripts.
    """
    for i, t in enumerate(ps):
        if t == BODY_ANCHOR:
            return ps[i:]
    raise SystemExit(f"FATAL: body anchor {BODY_ANCHOR!r} not found in document")


def regenerate(flag: str) -> None:
    print(f"  regenerating {flag} ...", flush=True)
    r = subprocess.run([sys.executable, str(GEN), flag], cwd=str(ROOT),
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        raise SystemExit(f"FATAL: generator failed for {flag} (exit {r.returncode})")


def main() -> int:
    check_only = "--check" in sys.argv
    rebuild_main = "--rebuild-main" in sys.argv

    if rebuild_main:
        if check_only:
            raise SystemExit("--rebuild-main and --check are mutually exclusive")
        print("Rebuilding MAIN v34 (auto-commits + runs test hook) ...", flush=True)
        r = subprocess.run([sys.executable, str(GEN)], cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit(f"FATAL: main generation failed (exit {r.returncode})")

    main_body = body(paras(MAIN))
    print(f"MAIN body: {len(main_body)} paragraphs (anchor '{BODY_ANCHOR}')\n")

    drift = False
    updated = []
    for flag, out, dest in DERIVED:
        print(f"{dest.name}")
        regenerate(flag)
        fresh = paras(out)

        # 1) body parity: the paper content must match main exactly
        if body(fresh) != main_body:
            drift = True
            print("  ** BODY DRIFT vs main -- derived paper text differs! **")
            import difflib
            sm = difflib.SequenceMatcher(a=main_body, b=body(fresh), autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    continue
                for x in main_body[i1:i2]:
                    print(f"     - main: {x[:110]}")
                for x in body(fresh)[j1:j2]:
                    print(f"     + {dest.stem}: {x[:110]}")
            continue
        print("  body parity vs main: OK")

        # 2) content-compare fresh derived vs the file currently in JITED_submission
        current = paras(dest) if dest.exists() else None
        if current == fresh:
            print("  JITED copy already current: no change\n")
            continue

        if check_only:
            drift = True  # out of sync, and we were told not to fix it
            print("  JITED copy is STALE (would be updated without --check)\n")
            continue

        import shutil
        shutil.copyfile(out, dest)
        updated.append(dest.name)
        print("  JITED copy UPDATED\n")

    print("=" * 60)
    if drift:
        print("RESULT: OUT OF SYNC" + (" (check-only, nothing written)" if check_only else ""))
        return 1
    if updated:
        print("RESULT: synced -> " + ", ".join(updated))
    else:
        print("RESULT: already in sync -- no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
