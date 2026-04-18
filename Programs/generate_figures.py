#!/usr/bin/env python3
"""
Generate Figure 1 (model structure) and Figure 1b (regime grid)
for the FLOP trade model paper.

Usage:
    python generate_figures.py [--output-dir DIR] [--png] [--dpi 300]

Requires: cairosvg (only if --png)
    pip install cairosvg --break-system-packages

Font: Uses DejaVu Sans for full Unicode subscript coverage.
      Installed by default on Ubuntu/Debian.
"""

import argparse
import os

# ---------------------------------------------------------------------------
# Notation fragments — rendered with SVG <tspan> markup for subscripts
# rather than Unicode subscript codepoints. The tspan approach is
# font-agnostic: PNG rasterizers (cairosvg, Inkscape, librsvg) render the
# glyphs correctly regardless of whether the local font has Unicode
# subscript coverage. Unicode subscript codepoints (U+2096 ₖ, U+2C7C ⱼ,
# U+1D62 ᵢ, U+209C ₜ) require DejaVu Sans or Noto; on systems without
# those fonts they rasterize as black boxes — the bug this fixes.
# ---------------------------------------------------------------------------
FONT = "Arial, Helvetica, sans-serif"

TAU = "\u03C4"      # tau (Greek, in every standard font)
LAMBDA = "\u03BB"   # lambda
MDASH = "\u2014"
CHECK = "\u2713"
CROSS = "\u2717"


def _sub(base, sub):
    """Render `base` followed by subscript `sub` using SVG tspan markup.
    Works in any SVG renderer and any font."""
    return (f'{base}<tspan baseline-shift="sub" font-size="0.7em">'
            f'{sub}</tspan>')


def _bar(letter):
    """Render a letter with an overbar (macron) via SVG tspan."""
    return (f'<tspan text-decoration="overline">{letter}</tspan>')


# Pre-built notation fragments (SVG markup, embed inside <text>...</text>)
C_j = _sub('c', 'j')                           # c_j
K_j = _sub('K', 'j')                           # K_j
P_T = _sub('p', 'T') + '*'                     # p_T*
P_I = _sub('p', 'I') + '*'                     # p_I*
P_I_k = _sub('p', 'I') + '*(k)'                # p_I*(k)
TAU_I = _sub(TAU, 'I') + ' \u00b7 l'           # τ_I · l
LAM_jk = _sub(LAMBDA, 'jk')                    # λ_jk
D_ij = _sub('d', 'ij')                         # d_ij
L_BAR = _bar('l')                              # l̄

REGIME_COND = f"{C_j} vs {P_T}, {P_I}, {LAM_jk}, {D_ij}"


def _css():
    """Shared CSS styles for both figures."""
    return '''
.gray-fill  { fill:#F1EFE8; stroke:#5F5E5A; }
.gray-title { fill:#2C2C2A; font-weight:500; font-size:14px; }
.gray-sub   { fill:#5F5E5A; font-size:12px; }
.teal-fill  { fill:#E1F5EE; stroke:#0F6E56; }
.teal-title { fill:#04342C; font-weight:500; font-size:14px; }
.teal-sub   { fill:#0F6E56; font-size:12px; }
.purple-fill  { fill:#EEEDFE; stroke:#534AB7; }
.purple-title { fill:#26215C; font-weight:500; font-size:14px; }
.purple-sub   { fill:#534AB7; font-size:12px; }
.coral-fill  { fill:#FAECE7; stroke:#993C1D; }
.coral-title { fill:#4A1B0C; font-weight:500; font-size:14px; }
.coral-sub   { fill:#993C1D; font-size:12px; }
.arr { stroke:#5F5E5A; stroke-width:1.5; fill:none; }'''


def _arrow_marker():
    return '''<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</marker>'''


def make_figure1():
    """Figure 1: Model structure — endowments through prices to regimes."""
    return f'''<svg width="680" height="562" viewBox="0 0 680 562"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
<defs>
{_arrow_marker()}
<style>{_css()}</style>
</defs>

<!-- Tier 1: Country endowments (gray) -->
<rect class="gray-fill" x="40"  y="30" width="142" height="56" rx="8" stroke-width="0.5"/>
<text class="gray-title" x="111" y="56" text-anchor="middle">Electricity</text>
<text class="gray-sub"   x="111" y="74" text-anchor="middle">dollars per kWh</text>

<rect class="gray-fill" x="192" y="30" width="142" height="56" rx="8" stroke-width="0.5"/>
<text class="gray-title" x="263" y="56" text-anchor="middle">Reliability</text>
<text class="gray-sub"   x="263" y="74" text-anchor="middle">grid uptime</text>

<rect class="gray-fill" x="344" y="30" width="142" height="56" rx="8" stroke-width="0.5"/>
<text class="gray-title" x="415" y="56" text-anchor="middle">Sovereignty</text>
<text class="gray-sub"   x="415" y="74" text-anchor="middle">political risk</text>

<rect class="gray-fill" x="496" y="30" width="142" height="56" rx="8" stroke-width="0.5"/>
<text class="gray-title" x="567" y="56" text-anchor="middle">Capital cost</text>
<text class="gray-sub"   x="567" y="74" text-anchor="middle">financing cost</text>

<line x1="111" y1="86" x2="240" y2="140" class="arr" marker-end="url(#arrow)"/>
<line x1="263" y1="86" x2="300" y2="140" class="arr" marker-end="url(#arrow)"/>
<line x1="415" y1="86" x2="380" y2="140" class="arr" marker-end="url(#arrow)"/>
<line x1="567" y1="86" x2="440" y2="140" class="arr" marker-end="url(#arrow)"/>

<!-- Tier 2: Production cost (teal) -->
<rect class="teal-fill" x="200" y="140" width="280" height="56" rx="8" stroke-width="0.5"/>
<text class="teal-title" x="340" y="166" text-anchor="middle">Production cost {C_j}</text>
<text class="teal-sub"   x="340" y="184" text-anchor="middle">combined input costs</text>

<line x1="300" y1="196" x2="150" y2="244" class="arr" marker-end="url(#arrow)"/>
<line x1="380" y1="196" x2="530" y2="244" class="arr" marker-end="url(#arrow)"/>

<!-- Tier 3a: World training price (teal, left) -->
<rect class="teal-fill" x="40" y="244" width="220" height="92" rx="8" stroke-width="0.5"/>
<text class="teal-title" x="150" y="268" text-anchor="middle">World training price {P_T}</text>
<text class="teal-sub"   x="150" y="288" text-anchor="middle">global market</text>
<text class="teal-sub"   x="150" y="306" text-anchor="middle">binding {K_j} raises {P_T}</text>
<text class="teal-sub"   x="150" y="322" text-anchor="middle">above c(1) {MDASH} Prop. 2</text>

<!-- Tier 3b: Capacity (purple, center) -->
<rect class="purple-fill" x="280" y="244" width="120" height="92" rx="8" stroke-width="0.5"/>
<text class="purple-title" x="340" y="272" text-anchor="middle">Capacity {K_j}</text>
<text class="purple-sub"   x="340" y="294" text-anchor="middle">land, water,</text>
<text class="purple-sub"   x="340" y="310" text-anchor="middle">grid, siting</text>

<!-- Tier 3c: Regional inference price (teal, right) -->
<rect class="teal-fill" x="420" y="244" width="220" height="92" rx="8" stroke-width="0.5"/>
<text class="teal-title" x="530" y="268" text-anchor="middle">Inference price {P_I_k}</text>
<text class="teal-sub"   x="530" y="288" text-anchor="middle">regional market</text>
<text class="teal-sub"   x="530" y="306" text-anchor="middle">iceberg cost {TAU_I}</text>
<text class="teal-sub"   x="530" y="322" text-anchor="middle">latency threshold {L_BAR}</text>

<line x1="280" y1="290" x2="262" y2="290" class="arr" marker-end="url(#arrow)"/>
<line x1="400" y1="290" x2="418" y2="290" class="arr" marker-end="url(#arrow)"/>

<line x1="150" y1="336" x2="280" y2="380" class="arr" marker-end="url(#arrow)"/>
<line x1="530" y1="336" x2="400" y2="380" class="arr" marker-end="url(#arrow)"/>

<!-- Tier 4: Regime conditions (teal) -->
<rect class="teal-fill" x="200" y="380" width="280" height="56" rx="8" stroke-width="0.5"/>
<text class="teal-title" x="340" y="406" text-anchor="middle">Regime conditions</text>
<text class="teal-sub"   x="340" y="424" text-anchor="middle">{REGIME_COND}</text>

<line x1="215" y1="436" x2="95"  y2="480" class="arr" marker-end="url(#arrow)"/>
<line x1="275" y1="436" x2="218" y2="480" class="arr" marker-end="url(#arrow)"/>
<line x1="340" y1="436" x2="340" y2="480" class="arr" marker-end="url(#arrow)"/>
<line x1="405" y1="436" x2="463" y2="480" class="arr" marker-end="url(#arrow)"/>
<line x1="465" y1="436" x2="585" y2="480" class="arr" marker-end="url(#arrow)"/>

<!-- Tier 5: Five equilibrium regimes (coral) — Proposition 1 -->
<rect class="coral-fill" x="40"  y="480" width="110" height="72" rx="8" stroke-width="0.5"/>
<text class="coral-title" x="95"  y="502" text-anchor="middle">EE</text>
<text class="coral-sub"   x="95"  y="522" text-anchor="middle">T: export</text>
<text class="coral-sub"   x="95"  y="540" text-anchor="middle">I: export</text>

<rect class="coral-fill" x="163" y="480" width="110" height="72" rx="8" stroke-width="0.5"/>
<text class="coral-title" x="218" y="502" text-anchor="middle">IE</text>
<text class="coral-sub"   x="218" y="522" text-anchor="middle">T: import</text>
<text class="coral-sub"   x="218" y="540" text-anchor="middle">I: export</text>

<rect class="coral-fill" x="285" y="480" width="110" height="72" rx="8" stroke-width="0.5"/>
<text class="coral-title" x="340" y="502" text-anchor="middle">ID</text>
<text class="coral-sub"   x="340" y="522" text-anchor="middle">T: import</text>
<text class="coral-sub"   x="340" y="540" text-anchor="middle">I: domestic</text>

<rect class="coral-fill" x="408" y="480" width="110" height="72" rx="8" stroke-width="0.5"/>
<text class="coral-title" x="463" y="502" text-anchor="middle">DD</text>
<text class="coral-sub"   x="463" y="522" text-anchor="middle">T: domestic</text>
<text class="coral-sub"   x="463" y="540" text-anchor="middle">I: domestic</text>

<rect class="coral-fill" x="530" y="480" width="110" height="72" rx="8" stroke-width="0.5"/>
<text class="coral-title" x="585" y="502" text-anchor="middle">II</text>
<text class="coral-sub"   x="585" y="522" text-anchor="middle">T: import</text>
<text class="coral-sub"   x="585" y="540" text-anchor="middle">I: import</text>
</svg>'''


def make_figure1b():
    """Figure 1b: 3x3 regime feasibility grid (Proposition 1)."""
    cap = f"Rows: training {MDASH} Columns: inference"
    return f'''<svg width="680" height="500" viewBox="0 0 680 500"
     xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
<defs>
<style>
.head-fill     {{ fill:#F1EFE8; stroke:#5F5E5A; }}
.head-text     {{ fill:#2C2C2A; font-weight:500; font-size:14px; }}
.feasible-fill {{ fill:#FAECE7; stroke:#993C1D; }}
.feasible-code {{ fill:#4A1B0C; font-weight:500; font-size:18px; }}
.feasible-sub  {{ fill:#993C1D; font-size:12px; }}
.ruled-fill    {{ fill:#F1EFE8; stroke:#888780; stroke-dasharray:4 3; }}
.ruled-code    {{ fill:#888780; font-weight:500; font-size:18px; }}
.ruled-sub     {{ fill:#888780; font-size:12px; }}
.caption       {{ fill:#2C2C2A; font-size:12px; }}
</style>
</defs>

<text class="caption" x="380" y="35" text-anchor="middle">{cap}</text>

<rect class="head-fill" x="180" y="60" width="140" height="40" rx="6" stroke-width="0.5"/>
<text class="head-text" x="250" y="85" text-anchor="middle">Export</text>
<rect class="head-fill" x="320" y="60" width="140" height="40" rx="6" stroke-width="0.5"/>
<text class="head-text" x="390" y="85" text-anchor="middle">Domestic</text>
<rect class="head-fill" x="460" y="60" width="140" height="40" rx="6" stroke-width="0.5"/>
<text class="head-text" x="530" y="85" text-anchor="middle">Import</text>

<rect class="head-fill" x="60" y="100" width="120" height="120" rx="6" stroke-width="0.5"/>
<text class="head-text" x="120" y="165" text-anchor="middle">Export</text>
<rect class="head-fill" x="60" y="220" width="120" height="120" rx="6" stroke-width="0.5"/>
<text class="head-text" x="120" y="285" text-anchor="middle">Domestic</text>
<rect class="head-fill" x="60" y="340" width="120" height="120" rx="6" stroke-width="0.5"/>
<text class="head-text" x="120" y="405" text-anchor="middle">Import</text>

<rect class="feasible-fill" x="180" y="100" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="feasible-code" x="250" y="138" text-anchor="middle">EE  {CHECK}</text>
<text class="feasible-sub"  x="250" y="166" text-anchor="middle">Training + inference</text>
<text class="feasible-sub"  x="250" y="184" text-anchor="middle">exporter</text>
<text class="feasible-sub"  x="250" y="202" text-anchor="middle">Cheapest producers</text>

<rect class="ruled-fill" x="320" y="100" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="ruled-code" x="390" y="148" text-anchor="middle">ED  {CROSS}</text>
<text class="ruled-sub"  x="390" y="175" text-anchor="middle">Ruled out</text>
<text class="ruled-sub"  x="390" y="193" text-anchor="middle">Proposition 4</text>

<rect class="ruled-fill" x="460" y="100" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="ruled-code" x="530" y="148" text-anchor="middle">EI  {CROSS}</text>
<text class="ruled-sub"  x="530" y="175" text-anchor="middle">Ruled out</text>
<text class="ruled-sub"  x="530" y="193" text-anchor="middle">Proposition 4</text>

<rect class="ruled-fill" x="180" y="220" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="ruled-code" x="250" y="268" text-anchor="middle">DE  {CROSS}</text>
<text class="ruled-sub"  x="250" y="295" text-anchor="middle">Ruled out</text>
<text class="ruled-sub"  x="250" y="313" text-anchor="middle">Cost ordering</text>

<rect class="feasible-fill" x="320" y="220" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="feasible-code" x="390" y="258" text-anchor="middle">DD  {CHECK}</text>
<text class="feasible-sub"  x="390" y="286" text-anchor="middle">Both domestic</text>
<text class="feasible-sub"  x="390" y="304" text-anchor="middle">Sovereignty premium</text>
<text class="feasible-sub"  x="390" y="322" text-anchor="middle">justifies both</text>

<rect class="ruled-fill" x="460" y="220" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="ruled-code" x="530" y="262" text-anchor="middle">DI  {CROSS}</text>
<text class="ruled-sub"  x="530" y="288" text-anchor="middle">Ruled out</text>
<text class="ruled-sub"  x="530" y="306" text-anchor="middle">Sovereignty</text>
<text class="ruled-sub"  x="530" y="322" text-anchor="middle">+ latency</text>

<rect class="feasible-fill" x="180" y="340" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="feasible-code" x="250" y="378" text-anchor="middle">IE  {CHECK}</text>
<text class="feasible-sub"  x="250" y="406" text-anchor="middle">Inference hub</text>
<text class="feasible-sub"  x="250" y="424" text-anchor="middle">Regional low-cost</text>
<text class="feasible-sub"  x="250" y="442" text-anchor="middle">{C_j} above {P_T}</text>

<rect class="feasible-fill" x="320" y="340" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="feasible-code" x="390" y="378" text-anchor="middle">ID  {CHECK}</text>
<text class="feasible-sub"  x="390" y="406" text-anchor="middle">Hybrid</text>
<text class="feasible-sub"  x="390" y="424" text-anchor="middle">Isolated or</text>
<text class="feasible-sub"  x="390" y="442" text-anchor="middle">sovereign inference</text>

<rect class="feasible-fill" x="460" y="340" width="140" height="120" rx="6" stroke-width="0.5"/>
<text class="feasible-code" x="530" y="378" text-anchor="middle">II  {CHECK}</text>
<text class="feasible-sub"  x="530" y="406" text-anchor="middle">Full importer</text>
<text class="feasible-sub"  x="530" y="424" text-anchor="middle">High-cost</text>
<text class="feasible-sub"  x="530" y="442" text-anchor="middle">no sovereignty</text>
</svg>'''


def svg_to_png(svg_content, png_path, dpi=300):
    """Rasterize SVG to PNG. Prefers a headless browser (Playwright) as the
    reference renderer for <tspan baseline-shift> subscripts; falls back to
    cairosvg if Playwright is unavailable. Browser rendering is font-agnostic
    and produces identical output to what Word users will see."""
    try:
        _svg_to_png_playwright(svg_content, png_path, dpi)
        return
    except ImportError:
        pass
    import cairosvg
    cairosvg.svg2png(
        bytestring=svg_content.encode("utf-8"),
        write_to=png_path,
        scale=dpi / 96.0,
    )


def _svg_to_png_playwright(svg_content, png_path, dpi):
    """Rasterize SVG using a headless Chromium browser."""
    import re
    from playwright.sync_api import sync_playwright
    # Extract intrinsic width/height to size the viewport precisely
    m_w = re.search(r'width="(\d+)"', svg_content)
    m_h = re.search(r'height="(\d+)"', svg_content)
    w_px = int(m_w.group(1)) if m_w else 800
    h_px = int(m_h.group(1)) if m_h else 600
    scale = dpi / 96.0
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>html,body{margin:0;padding:0;background:white;}</style>'
        f'</head><body>{svg_content}</body></html>'
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={'width': w_px, 'height': h_px},
            device_scale_factor=scale,
        )
        page.set_content(html, wait_until='load')
        svg_handle = page.query_selector('svg')
        svg_handle.screenshot(path=png_path, omit_background=False)
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Generate FLOP trade model figures")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--dpi", type=int, default=300, help="PNG DPI")
    parser.add_argument("--png", action="store_true", help="Also generate PNG")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    figures = [
        ("figure1_model_structure", make_figure1),
        ("figure1b_regime_grid", make_figure1b),
    ]
    for name, func in figures:
        svg = func()
        svg_path = os.path.join(args.output_dir, f"{name}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"[OK] {svg_path}")
        if args.png:
            png_path = os.path.join(args.output_dir, f"{name}.png")
            svg_to_png(svg, png_path, args.dpi)
            print(f"[OK] {png_path} ({args.dpi} DPI)")


if __name__ == "__main__":
    main()
