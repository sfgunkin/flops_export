"""
Apply 5 proofread fixes to flop_trade_model_v20.docx:
1. [12] Missing "$9 billion" figure (cloud exports)
2. [58] India/Canada ordering in top-5 demand centers
3. [60] "55 non-ECA" → "56 non-ECA"
4. [61] Ireland ($1.28→$1.58) and Greenland ($1.32→$1.62) stale costs
5. [70] Clarify "hardware amortization" vs "hardware and networking" (80% vs 94%)
"""

import sys, os
sys.path.insert(0, r"F:\onedrive\__documents\papers\FLOPsExport\Programs")

from docx import Document
from docx.oxml.ns import qn

SRC = r"F:\onedrive\__documents\papers\FLOPsExport\Documents\flop_trade_model_v20.docx"
DST = r"F:\onedrive\__documents\papers\FLOPsExport\Documents\flop_trade_model_v20.docx"

def replace_in_runs(para_element, old_text, new_text):
    """Replace text across runs in a paragraph, preserving formatting."""
    t_elements = []
    for r in para_element.findall(f'.//{qn("w:r")}'):
        for t in r.findall(qn('w:t')):
            t_elements.append(t)
    full = ''.join(t.text or '' for t in t_elements)
    if old_text not in full:
        return False
    # Simple case: text within a single run
    for t in t_elements:
        if t.text and old_text in t.text:
            t.text = t.text.replace(old_text, new_text, 1)
            if t.text.startswith(' ') or t.text.endswith(' '):
                t.set(qn('xml:space'), 'preserve')
            return True
    # Cross-run case: build char map
    char_map = []
    for t in t_elements:
        for i, ch in enumerate(t.text or ''):
            char_map.append((t, i))
    start = full.index(old_text)
    end = start + len(old_text)
    # Put replacement text in the first run's t element
    first_t = char_map[start][0]
    first_idx = char_map[start][1]
    orig = first_t.text
    first_t.text = orig[:first_idx] + new_text
    if first_t.text.startswith(' ') or first_t.text.endswith(' '):
        first_t.set(qn('xml:space'), 'preserve')
    # Clear characters from subsequent t elements
    for pos in range(start + 1, end):
        t_el = char_map[pos][0]
        ch_idx = char_map[pos][1]
        if t_el is not first_t:
            if ch_idx == 0 and pos == end - 1:
                t_el.text = (t_el.text or '')[1:]
            elif ch_idx == 0:
                pass  # Will handle below
            else:
                pass
    # More robust: rebuild all affected t elements after first
    affected_ts = []
    for pos in range(start, end):
        t_el = char_map[pos][0]
        if t_el not in affected_ts:
            affected_ts.append(t_el)
    # For all t_elements after the first affected, remove the consumed characters
    for t_el in affected_ts[1:]:
        chars_to_remove = []
        for pos in range(start, end):
            if char_map[pos][0] is t_el:
                chars_to_remove.append(char_map[pos][1])
        if chars_to_remove:
            old_txt = t_el.text or ''
            new_txt = ''.join(ch for i, ch in enumerate(old_txt) if i not in chars_to_remove)
            t_el.text = new_txt
            if new_txt and (new_txt.startswith(' ') or new_txt.endswith(' ')):
                t_el.set(qn('xml:space'), 'preserve')
    # Fix the first t element - only keep up to first_idx + new_text
    # Actually we already set it above. But we might have leftover chars from the old text
    orig_first = ''.join(t.text or '' for t in t_elements)  # re-read
    return True


doc = Document(SRC)
fixes_applied = []

for para in doc.paragraphs:
    text = para.text

    # Fix 1: [12] Missing "$9 billion" figure
    if 'Cloud computing exports already exceed' in text and 'billion annually' in text:
        if replace_in_runs(para._element, 'exceed  billion', 'exceed $9 billion'):
            fixes_applied.append('[12] Added "$9 billion" figure for cloud exports')
        elif replace_in_runs(para._element, 'exceed billion', 'exceed $9 billion'):
            fixes_applied.append('[12] Added "$9 billion" figure for cloud exports (no space)')

    # Fix 2: [58] India/Canada ordering — should be descending by share
    if 'India (2.9%), Canada (3%)' in text:
        if replace_in_runs(para._element,
                           'India (2.9%), Canada (3%)',
                           'Canada (3%), India (2.9%)'):
            fixes_applied.append('[58] Reordered India/Canada to descending share order')

    # Fix 3: [60] "55 non-ECA" → "56 non-ECA"
    if '30 in ECA, 55 non-ECA' in text:
        if replace_in_runs(para._element,
                           '30 in ECA, 55 non-ECA',
                           '30 in ECA, 56 non-ECA'):
            fixes_applied.append('[60] Changed "55 non-ECA" to "56 non-ECA" (total = 86)')

    # Fix 4: [61] Ireland and Greenland stale costs
    if 'Ireland ($1.28/hr)' in text:
        if replace_in_runs(para._element, 'Ireland ($1.28/hr)', 'Ireland ($1.58/hr)'):
            fixes_applied.append('[61] Updated Ireland cost $1.28 → $1.58')
    if 'Greenland ($1.32/hr)' in text:
        if replace_in_runs(para._element, 'Greenland ($1.32/hr)', 'Greenland ($1.62/hr)'):
            fixes_applied.append('[61] Updated Greenland cost $1.32 → $1.62')

    # Fix 5: [70] Clarify "hardware amortization" → "hardware and networking costs"
    # The second occurrence: "hardware amortization accounts for roughly 94%"
    if 'hardware amortization accounts for roughly 94%' in text:
        if replace_in_runs(para._element,
                           'hardware amortization accounts for roughly 94% of engineering costs and is identical everywhere',
                           'hardware and networking costs account for roughly 94% of engineering costs and are identical everywhere'):
            fixes_applied.append('[70] Clarified "hardware amortization" → "hardware and networking costs" (94% = $1.51/$1.60)')

# Set metadata
doc.core_properties.author = 'Michael Lokshin'

doc.save(DST)

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print(f"Saved to {DST}")
print(f"\nFixes applied ({len(fixes_applied)}):")
for f in fixes_applied:
    print(f"  - {f}")
if len(fixes_applied) < 5:
    print(f"\nWARNING: Expected 5+ fixes, only applied {len(fixes_applied)}")
