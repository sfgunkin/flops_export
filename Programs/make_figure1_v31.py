"""Generate Figure 1: Calibration strategy flowchart for v31 (2 steps, no FDI).

Flow: Observed tariffs → Cost-recovery prices → Bilateral sovereignty
Shows delivered cost P, not production cost c.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

OUT = Path(r"F:\onedrive\__documents\papers\FLOPsExport\Documents\calibration_strategy_v31.png")

# ── Colours ──────────────────────────────────────────────────────────
BLUE_BG    = '#dce6f5'
BLUE_EDGE  = '#7a9ec7'
PEACH_BG   = '#fce5d0'
PEACH_EDGE = '#d4915c'
STEP1_CLR  = '#1a5ca0'
STEP2_CLR  = '#8b4513'
RED_TXT    = '#c03030'
GREEN_TXT  = '#1a6e1a'
ARR_CLR    = '#444444'

# Tighter canvas: content spans x≈0.5–10.5, y≈0.5–9.5
fig = plt.figure(figsize=(11, 10))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 11)
ax.set_ylim(0, 10)
ax.axis('off')
fig.patch.set_facecolor('white')

BW, BH = 3.4, 1.5   # box width, height


def rbox(x, y, w, h, title, sub, bg, edge, lw=2.2):
    """Rounded box with title + italic subtitle."""
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.20",
                           facecolor=bg, edgecolor=edge, linewidth=lw)
    ax.add_patch(patch)
    cx = x + w / 2
    ax.text(cx, y + h * 0.64, title, ha='center', va='center',
            fontsize=16.5, fontweight='bold', color='#1a1a1a',
            fontfamily='sans-serif')
    ax.text(cx, y + h * 0.28, sub, ha='center', va='center',
            fontsize=11.5, fontstyle='italic', color='#555555',
            fontfamily='sans-serif')
    return cx, y + h / 2


def harrow(x1, y, x2, label_top='', label_bot=''):
    """Horizontal arrow with two-line label."""
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=ARR_CLR, lw=2))
    mx = (x1 + x2) / 2
    if label_top:
        ax.text(mx, y + 0.22, label_top, ha='center', va='center',
                fontsize=11, color=ARR_CLR)
    if label_bot:
        ax.text(mx, y - 0.22, label_bot, ha='center', va='center',
                fontsize=11, color=ARR_CLR)


# ══════════════════════════════════════════════════════════════════════
#  STEP 1 — Cost adjustments  (upper region)
# ══════════════════════════════════════════════════════════════════════
ax.text(0.6, 9.1, 'Step 1: Cost adjustments',
        fontsize=20, fontweight='bold', color=STEP1_CLR)

# Box 1: Observed tariffs
x1, y1 = 0.8, 7.0
cx1, cy1 = rbox(x1, y1, BW, BH,
                'Observed tariffs', 'National electricity prices',
                BLUE_BG, BLUE_EDGE)

# Box 2: Cost-recovery prices
x2, y2 = 6.2, 7.0
cx2, cy2 = rbox(x2, y2, BW, BH,
                'Cost-recovery prices', 'LRMC at opportunity cost',
                BLUE_BG, BLUE_EDGE)

# Arrow box1 → box2
harrow(x1 + BW + 0.1, cy1, x2 - 0.1, 'Remove', 'subsidies')

# Spec labels under boxes — delivered cost P (no sovereignty → P = c)
ax.text(cx1, y1 - 0.38, 'Specification (1)',
        ha='center', fontsize=12, color=RED_TXT, fontweight='bold')
ax.text(cx1, y1 - 0.75, r'$P_{jk} = c_j$  (observed tariffs)',
        ha='center', fontsize=10.5, color='#555555')

ax.text(cx2, y2 - 0.38, 'Specification (2)',
        ha='center', fontsize=12, color=RED_TXT, fontweight='bold')
ax.text(cx2, y2 - 0.75, r'$P_{jk} = c_j$  (cost-recovery)',
        ha='center', fontsize=10.5, color='#555555')


# ══════════════════════════════════════════════════════════════════════
#  STEP 2 — Trade friction adjustments  (lower region)
# ══════════════════════════════════════════════════════════════════════
ax.text(0.6, 5.2, 'Step 2: Trade friction adjustments',
        fontsize=20, fontweight='bold', color=STEP2_CLR)

# Vertical arrow from Cost-recovery box down to Bilateral box
v_top = y2 - 0.9      # below the Spec (2) labels
v_bot = 3.5 + BH + 0.1
ax.annotate('', xy=(cx2, v_bot), xytext=(cx2, v_top),
            arrowprops=dict(arrowstyle='->', color=ARR_CLR, lw=2))
ax.text(cx2 + 1.0, (v_top + v_bot) / 2 + 0.15, 'Apply bilateral',
        ha='center', fontsize=10.5, color=ARR_CLR)
ax.text(cx2 + 1.0, (v_top + v_bot) / 2 - 0.2, r'sovereignty $\lambda_{ij}$',
        ha='center', fontsize=10.5, color=ARR_CLR)

# Box 3: Bilateral sovereignty
x3 = cx2 - BW / 2
y3 = 2.0
cx3, cy3 = rbox(x3, y3, BW, BH,
                'Bilateral sovereignty',
                'Geopolitical + regulatory\n+ sanctions',
                PEACH_BG, PEACH_EDGE)

# Spec (3) label — delivered cost P includes sovereignty markup
ax.text(cx3, y3 - 0.45, 'Specification (3)',
        ha='center', fontsize=12, color=RED_TXT, fontweight='bold')
ax.text(cx3, y3 - 0.90, r'$P_{jk} = c_j \,(1 + \lambda_{ij})$',
        ha='center', fontsize=11, color=GREEN_TXT, fontweight='bold')

# ── Robustness: Uniform sovereignty (dashed box, to the left) ───────
UW, UH = 3.0, 1.25
ux = x3 - UW - 1.5
uy = y3 + (BH - UH) / 2
uni = FancyBboxPatch((ux, uy), UW, UH, boxstyle="round,pad=0.15",
                      facecolor='white', edgecolor='#aaaaaa',
                      linewidth=1.5, linestyle='--')
ax.add_patch(uni)
ucx = ux + UW / 2
ax.text(ucx, uy + UH * 0.64, 'Uniform sovereignty',
        ha='center', fontsize=14, fontweight='bold', color='#777777')
ax.text(ucx, uy + UH * 0.28, r'$\lambda$ = 0.10 for all pairs',
        ha='center', fontsize=10.5, fontstyle='italic', color='#999999')

# Dashed arrow bilateral ← uniform
ax.annotate('', xy=(ux + UW + 0.1, cy3),
            xytext=(x3 - 0.1, cy3),
            arrowprops=dict(arrowstyle='<-', color='#aaaaaa',
                            lw=1.3, linestyle='dashed'))
mid_a = (ux + UW + x3) / 2
ax.text(mid_a, cy3 + 0.22, 'Robustness',
        ha='center', fontsize=10, color='#aaaaaa')
ax.text(mid_a, cy3 - 0.22, 'check',
        ha='center', fontsize=10, color='#aaaaaa')

ax.text(ucx, uy - 0.45, 'Confirms bilateral result\nis not knife-edge',
        ha='center', fontsize=10, color='#999999')

# ── Save ────────────────────────────────────────────────────────────
fig.savefig(str(OUT), dpi=180, facecolor='white',
            bbox_inches='tight', pad_inches=0.3)
print(f"Saved: {OUT}")
plt.close()
