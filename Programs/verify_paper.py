#!/usr/bin/env python
"""Every structural check the FLOPs paper has, in one place, over docxkit.

The value tests (``test_paper_values.py``) verify what the paper SAYS
against the data; this verifies what the document IS -- that its citation
apparatus resolves, that its figure and table anchors are the house
convention, that the markup is one Word will open, and that the two
manuscripts the journal received still carry the paper's own abstract.

    python Programs/verify_paper.py             # gates + advisory audits
    python Programs/verify_paper.py --quick     # gates only

Gates fail the run (exit 1). The advisory audits report and never fail:
reference style and stray math are judgement calls, and a check that
cannot be overruled by a person stops being read.
"""
from __future__ import annotations

import sys
from pathlib import Path

from docxkit import read_parts, text_of, utf8_stdout
from docxkit.citations import audit_links
from docxkit.crossrefs import audit as crossref_audit
from docxkit.find import paragraphs
from docxkit.lint import lint_parts
from docxkit.package import text_parts
from docxkit.testing import DOCUMENT, FOOTNOTES, latest_version

utf8_stdout()

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "Documents"
JITED = DOCS / "JITED_submission"

# The three manuscripts that must agree on the paper's own words: the
# working paper and the two files the journal received.
DERIVED = [JITED / "JITED_manuscript_anonymous.docx",
           JITED / "JITED_manuscript_with_author_details.docx"]


def abstract_of(path: Path) -> str:
    """The abstract paragraph's text, label included."""
    xml = read_parts(path)[DOCUMENT].decode("utf-8")
    for m in paragraphs(xml):
        t = text_of(m.group(0)).strip()
        if t.startswith("Abstract"):
            return t
    raise SystemExit(f"FATAL: no abstract paragraph in {path.name}")


def main() -> int:
    quick = "--quick" in sys.argv
    paper = latest_version(DOCS, "flop_trade_model")
    parts = read_parts(paper)
    body = parts[DOCUMENT].decode("utf-8")
    print(f"Verifying {paper.name}\n" + "=" * 60)

    failures: list[str] = []

    # ---- gate: the citation apparatus resolves --------------------------
    issues, stats = audit_links(parts)
    print(f"citations   {stats['bookmarks']} bookmarks, {stats['links']} links, "
          f"{stats['broken']} broken, {stats['unlinked']} unlinked mentions")
    for issue in issues[:10]:
        print(f"              - {issue}")
    if issues:
        failures.append(f"{len(issues)} citation issue(s)")

    # ---- gate: figure/table anchors are the house convention ------------
    # Footnotes carry citation bookmarks the body links to, so an audit
    # over the body alone calls them dangling; `also` is what makes the
    # answer the true one.
    others = [xml for name, xml in text_parts(parts) if name == FOOTNOTES]
    state = crossref_audit(body, also=others)
    print(f"crossrefs   {len(state['linked'])} linked, "
          f"{len(state['dangling'])} dangling, "
          f"{len(state['misplaced_anchor'])} misplaced")
    for key in ("dangling", "misplaced_anchor", "misnamed"):
        for line in state[key][:10]:
            print(f"              - {key}: {line}")
    if state["dangling"] or state["misplaced_anchor"]:
        failures.append("cross-reference anchors")

    # ---- gate: markup Word will open ------------------------------------
    problems = lint_parts(parts)
    print(f"lint        {len(problems)} structural problem(s)")
    for p in problems[:10]:
        print(f"              - {p}")
    if problems:
        failures.append(f"{len(problems)} lint problem(s)")

    # ---- gate: the submitted manuscripts carry the paper's abstract -----
    # sync_jited_submission.py checks the BODY, from the Introduction
    # anchor down. The abstract is front matter and sits above it, so an
    # abstract edit -- exactly what the author made in July -- is outside
    # that check and needs its own.
    want = abstract_of(paper)
    for path in DERIVED:
        if not path.exists():
            print(f"abstract    MISSING {path.name}")
            failures.append(f"{path.name} missing")
            continue
        got = abstract_of(path)
        ok = "OK" if got == want else "DRIFTED"
        print(f"abstract    {ok:<8} {path.name}")
        if got != want:
            failures.append(f"{path.name} abstract")

    if not quick:
        print("-" * 60)
        _advisory(parts, body)

    print("=" * 60)
    if failures:
        print("FAILED: " + "; ".join(failures))
        return 1
    print("ALL GATES PASSED")
    return 0


def _advisory(parts: dict[str, bytes], body: str) -> None:
    """Audits worth reading and not worth failing a build over."""
    from docxkit.equations import prose_math
    from docxkit.footnotes import sizes
    from docxkit.refstyle import HOUSE, audit as refstyle_audit
    from docxkit.wordcount import count

    report = refstyle_audit(parts, HOUSE)
    print(f"refstyle    {len(report.issues)} finding(s) (advisory)")
    for row in report.issues[:8]:
        print(f"              - {row}")

    findings = prose_math(body)
    print(f"prose math  {len(findings)} symbol(s) loose in prose (advisory)")
    for f in findings[:5]:
        print(f"              - {f}")

    notes = parts.get(FOOTNOTES)
    if notes:
        styles = parts.get("word/styles.xml")
        fn = sizes(notes.decode("utf-8"),
                   styles_xml=styles.decode("utf-8") if styles else None)
        print(f"footnotes   {'one size' if fn.ok else 'MIXED sizes'} (advisory)")

    counts = count(parts)
    print("words       " + ", ".join(f"{k} {v:,}"
                                     for k, v in counts.as_dict().items()))
    print(f"            total {counts.total():,}")


if __name__ == "__main__":
    raise SystemExit(main())
