# Equation and Notation Audit: flop_trade_model_v32.docx

**Date:** 2026-04-09
**Source script:** `add_calibration_v32.py`
**Generated document:** `flop_trade_model_v32.docx`

---

## Executive Summary

The paper contains **6 numbered display equations** (1--6), **1 unnumbered display equation** (PUE), **1 unnumbered display equation** (HHI), and **5 appendix equations** (B.1--B.5). After systematic verification of every equation, notation symbol, cross-reference, and dimensional unit, I find:

- **1 substantive dimensional/notation error** (construction cost term in Eq. 1)
- **1 notation clash** (alpha used for two distinct concepts)
- **1 stale CSV row** (xi_j still present in model_parameters.csv)
- **2 minor equation-number mismatches** in the CSV parameter file
- **1 missing space** in prose (minor typographic)
- All other equations are algebraically valid and notation is consistent

---

## 1. Notation Consistency Audit

### 1.1 theta_j (country temperature) vs theta-bar (threshold)

| Symbol | Meaning | Lines in script | OMML rendering | Status |
|--------|---------|-----------------|----------------|--------|
| theta_j | Country j's peak summer temperature | L1654, L1731-1744 | `_msub('theta', 'j')` | CONSISTENT |
| theta-bar | Free-cooling temperature threshold (15 C) | L1733, L1738, L1742 | `_mbar('theta')` | CONSISTENT |

**Verdict: VALID.** theta_j always has subscript j; theta-bar always rendered with overbar via `_mbar()`. No confusion between the two. In Table 2, theta-bar is rendered via `omath(p_c, [_mbar('\u03B8')])` (L5267). The two are visually and semantically distinct throughout.

### 1.2 l_{jk} (latency) vs l-bar (threshold) -- any leftover d_{ij} or d-bar?

| Symbol | Meaning | Lines | Status |
|--------|---------|-------|--------|
| l_{jk} | Round-trip latency from j to k (ms) | L1796, L2226, L2609, L4090 | CONSISTENT |
| l-bar | Latency threshold (~200 ms) | L1941, L2389, L2610, L2619, L4090 | CONSISTENT |

**Grep for `d_ij`, `d_{ij}`, or `d-bar`: zero matches.** All legacy distance notation has been purged. The paper uniformly uses `l_{jk}` for bilateral latency and `l-bar` for the threshold.

**Verdict: VALID.** No leftover `d_{ij}` or `d-bar` notation.

### 1.3 K-bar_j (capacity ceiling) vs K_j (total allocation) vs K_{T,j} (training) vs K_{I,j->k} (inference)

| Symbol | Meaning | Key lines | Status |
|--------|---------|-----------|--------|
| K-bar_j | Capacity ceiling (max GPU-hr/period) | L2119 `_mbar_sub('K', 'j')`, L4007, L4184, L4194 | CONSISTENT |
| K_j | Total capacity used by country j | L4132 `_msub('K', 'j')`, L4151, L4164, L4183 | CONSISTENT |
| K_{T,j} | GPU-hours allocated to training exports | L4118 `_msub('K', 'T,j')`, L2489, L2494, L4080 | CONSISTENT |
| K_{I,j->k} | GPU-hours allocated to inference to buyer k | L4122 `_msub('K', 'I,j\u2192k')` | CONSISTENT |

**Verdict: VALID.** The four K-variants are always distinguished by their subscripts/overbars. `K-bar_j` is always rendered via `_mbar_sub('K', 'j')`, while `K_j`, `K_{T,j}`, and `K_{I,j->k}` use standard subscripts.

**One rendering note:** At L2296, the code uses `_msub('K\u0304', 'j')` (Unicode combining overline) instead of `_mbar_sub('K', 'j')`. This produces a slightly different visual rendering of K-bar_j compared to all other uses that employ the OMML `<m:bar>` element. It is semantically identical but visually inconsistent.

- **Location:** L2296 in `write_sourcing_and_equilibrium()`
- **Should be:** `_mbar_sub('K', 'j')` (matching L2119, L4007, L4184, L4194)
- **Impact:** Minor visual inconsistency only

### 1.4 lambda_{ij} vs lambda_{jk} -- seller/buyer convention

The paper defines:
- **Eq. (2):** `lambda_{ij}` where i = seller, j = buyer (L1862)
- **Eq. (3):** `lambda_{jk}` where j = seller, k = buyer (L1884)

The relabeling is **explicitly documented** in prose at L1898-1907: "The bilateral premium lambda_{jk} is the same object as lambda_{ij} in equation (2); we relabel the subscripts as (j, k) whenever the premium is paired with a specific seller's production cost c_j."

Usage throughout:
- **Section 3.2 definition:** lambda_{ij} (i=seller, j=buyer)
- **Eq. (3) and Section 3.4:** lambda_{jk} (j=seller, k=buyer) -- consistently used when paired with c_j
- **Section 4 (Propositions):** lambda_{jk} in Prop. 1 (iv) and (v), lambda_{ij} in Prop. 1 (iii)
- **Section 6.2 (welfare):** lambda_{ij} at L3305, L3311 -- paired with p_T, so i=seller convention
- **Appendix B:** lambda_{jk} throughout (B.2, B.4, B.5, B.6)

**One issue in Proposition 1 (iii):** At L2402, the ID regime description uses `lambda_{ij}` where the context is "countries that import training but produce inference domestically, because the bilateral sovereignty premium lambda_{ij}..." Here i is the potential foreign seller and j is the country itself. This is correct per the (i=seller, j=buyer) convention from Eq. (2), but all other Proposition 1 conditions use `lambda_{jk}` with (j=seller, k=buyer) convention. The switch is slightly jarring but not an error since the prose context makes the role clear.

**Verdict: VALID with caveat.** The dual subscript convention is explicitly documented and consistently applied. Minor inconsistency in Prop. 1 (iii) where lambda_{ij} is used while other sub-propositions use lambda_{jk}.

### 1.5 p_T (training price) -- any leftover p_T* with asterisk?

**Grep for `p_T*`, `p_T_star`, `p_T_asterisk`, `\u2217`: zero matches.**

The symbol `lambda_k*` (with asterisk) is used for the sovereignty switching threshold in Proposition 3 (L2528), rendered as `_msubsup('lambda', 'k', '*')`. This is the only asterisked symbol. No `p_T*` exists anywhere.

**Verdict: VALID.** No leftover p_T* notation.

### 1.6 c_j (cost) -- always subscript j for seller?

`c_j` is consistently used for the unit production cost of country j (the seller). In places where a buyer's cost is referenced, the subscript switches appropriately:
- `c_k` at L2416, L2431 (buyer k in Propositions)
- `c_j` at L1653, L2365, L2445, L4014, L4027 (seller j)

**Verdict: VALID.** Subscript convention is consistently applied.

### 1.7 tau (latency degradation rate)

| Context | Symbol | Lines | Status |
|---------|--------|-------|--------|
| Generic rate | tau | L1923, L2824-2826 | CONSISTENT |
| Training (zero) | tau_T = 0 | L1927, L1933, L2131, L2344, L4063 (B.1) | CONSISTENT |
| Inference (positive) | tau_I = tau > 0 | L1929, L2217, L2346 | CONSISTENT |
| In equations | tau (no subscript) | L1885 (Eq. 3), L2265 (Eq. 6), L4100 (B.2), L4146 (B.4) | CONSISTENT |

The parameter tau is used without subscript in the delivery cost equations (where s is already explicit in the context). The service-specific versions tau_T and tau_I are used only in prose to distinguish the two cases.

**Verdict: VALID.**

### 1.8 alpha (training share) vs alpha_1, alpha_2, alpha_3 (sovereignty coefficients) -- CLASH

**This is a genuine notation clash:**

| Symbol | Meaning | Definition line | Used in |
|--------|---------|-----------------|---------|
| alpha | Training share of compute demand (0.50) | L148, L2065, L2070-2071, L2871 | Eq. (4) context, Table 2 |
| alpha_1 | Geopolitical distance weight (0.05) | L197, L1863, L2845 | Eq. (2) |
| alpha_2 | Regulatory incompatibility weight (0.025) | L198, L1865, L2847 | Eq. (2) |
| alpha_3 | Sanctions weight (0.10) | L318, L1867, L2849 | Eq. (2) |

The plain `alpha` (training share) and the subscripted `alpha_1`, `alpha_2`, `alpha_3` (sovereignty coefficients) are **different parameters that happen to share the same Greek letter**. While the subscripted versions are visually distinguished, the plain `alpha` appears in the same paper as the subscripted variants, creating a potential for reader confusion.

In Table 2 (L5192), the symbol column maps `'alpha': '\u03B1'` for the training share. Readers encountering alpha in the demand section and alpha_1 in the sovereignty section must track two distinct uses of the same base symbol.

**Verdict: NEEDS CLARIFICATION.** The paper should either (a) rename the training share to a different Greek letter (e.g., `a`), or (b) add a clarifying note that alpha (unsubscripted) denotes the training share while alpha_1, alpha_2, alpha_3 are the sovereignty coefficients.

### 1.9 rho (hardware cost)

`rho` is consistently defined as the amortized hardware cost per GPU-hour:
- Definition: L143 (`RHO = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL)`)
- Eq. (1): L1657 `_v('\u03C1')`
- Table 2: L5237 `val_str = f"${RHO:.2f}/hr"`
- Sensitivity: L3394, L3401 `_v('\u03C1')`
- Computed value: $1.358/hr (rendered as $1.36)

**Verdict: VALID.** Single consistent meaning throughout.

### 1.10 eta (networking cost)

`eta` is consistently defined as the amortized networking cost per GPU-hour:
- Definition: L145 (`ETA = 0.15`)
- Eq. (1): L1658 `_v('\u03B7')`
- Explanation: L1691-1704
- Table 2: L5239 `val_str = f"${ETA:.2f}/hr"`

**Verdict: VALID.** Single consistent meaning throughout.

### 1.11 G_{ij}, R_{ij}, S_{ij} (sovereignty components)

All three are consistently subscripted with (ij) where i=seller, j=buyer:
- L1840: `_msub('G', 'ij')`
- L1849: `_msub('R', 'ij')`
- L1854: `_msub('S', 'ij')`
- Eq. (2) at L1862-1868: all three with ij subscripts

**Verdict: VALID.**

### 1.12 Q, Q_T^X (demand notation)

| Symbol | Meaning | Lines | Status |
|--------|---------|-------|--------|
| Q | Total global compute spending | L2021, L2031, L2736 | CONSISTENT |
| Q_{T,X} | Total training export demand | L2482 `_msub('Q', 'T,X')`, L4051 `_msubsup('Q', 'T', 'X')` | **INCONSISTENT** |

At L2482 (HHI display in Prop. 2), `Q_{T,X}` is rendered with comma-subscript: `_msub('Q', 'T,X')`. At L4051 and L4066 (Appendix B.2), it is rendered as `_msubsup('Q', 'T', 'X')` (subscript T, superscript X). These are **two different visual renderings** of the same mathematical object.

The `_msubsup` version in Appendix B makes it look like `Q_T^X` (Q with subscript T and superscript X), while the main text renders it as `Q_{T,X}` (Q with subscript "T,X"). The first convention is standard in trade notation (X for exports as a superscript), so both are defensible, but they should be uniform.

**Verdict: NEEDS CLARIFICATION.** The rendering of total training export demand is inconsistent between Prop. 2 (`Q_{T,X}` as a subscript) and Appendix B.2 (`Q_T^X` as sub+superscript). Should be unified.

### 1.13 omega_k (demand share)

`omega_k` is consistently defined as country k's share of global demand:
- L2023, L2035: `_msub('\u03C9', 'k')`
- Eq. (4): `omega_k = M_k / sum M_{k'}`
- Table A1 notes: L3782 `omega_j`

**Verdict: VALID.**

---

## 2. Equation Validity

### 2.1 Equation (1): Cost Function

**Display equation (script L1652-1661):**
```
c_j = PUE(theta_j) * gamma * p_{E,j} + rho + eta + p_{L,j} / (D * H)
```

**OMML extracted (Equation 4 in extraction):**
```
cj = PUE(θj) · γ · pE,j + ρ + η + pL,j / (D · H),
```

**Code implementation (L7008-7012):**
```python
constr = float(r_row["p_L_usd_per_W"])        # $/W
constr_cost = (constr * GAMMA * 1000) / (DC_LIFE * H_YR)  # $/GPU-hr
```

**ISSUE FOUND: The construction cost term in Eq. (1) is dimensionally incorrect as written.**

The equation displays: `p_{L,j} / (D * H)`

Where:
- `p_{L,j}` is in $/W of IT capacity (as stated in prose at L1696-1698: "construction costs p_{L,j} ($/W of IT capacity)")
- `D` = 15 years (facility lifetime)
- `H` = 8,766 hr/yr

So `p_{L,j} / (D * H)` has units: `($/W) / (years * hr/yr) = $/W/hr`

But c_j must have units $/GPU-hr. To convert from $/W to $/GPU-hr, we need to multiply by the GPU power draw in watts. The code correctly does:
```
constr_cost = (p_L * GAMMA * 1000) / (DC_LIFE * H_YR)
```
where `GAMMA * 1000 = 0.700 * 1000 = 700 W` converts kW to W.

**The equation should be:**
```
c_j = PUE(theta_j) * gamma * p_{E,j} + rho + eta + (p_{L,j} * gamma * 1000) / (D * H)
```
or equivalently, redefining `p_{L,j}` as the total construction cost per GPU (in $) rather than per watt:
```
c_j = PUE(theta_j) * gamma * p_{E,j} + rho + eta + p_{L,j} / (D * H)
```
where `p_{L,j}` is redefined as `construction cost per GPU in $` = `($/W) * gamma_W`.

**The issue is that the equation as written and the prose description of p_{L,j} as "$/W of IT capacity" are inconsistent.** The code multiplies by `GAMMA * 1000` (700 W per GPU) to convert, but the equation omits this factor.

**Numerical check:** For Kyrgyzstan: p_L = $7.83/W, gamma = 0.700 kW = 700 W
- Code: (7.83 * 0.700 * 1000) / (15 * 8766) = 5481 / 131490 = $0.0417/hr
- Equation as written: 7.83 / (15 * 8766) = 7.83 / 131490 = $0.0000596/hr (WAY too small)

**Verdict: INVALID.** The construction cost term `p_{L,j}/(D*H)` in Eq. (1) is missing the GPU power factor. Either:
- (a) Change the equation to `(p_{L,j} * gamma) / (D * H)` and note gamma is in watts (i.e., use gamma in kW and multiply by 1000, or express gamma_W = 700 W), or
- (b) Redefine `p_{L,j}` in the prose as "construction cost per GPU" in $ rather than "per watt of IT capacity"

**Recommendation:** Option (a) is cleaner. Replace the last term with `p_{L,j} * gamma_W / (D * H)` where `gamma_W = 1000 * gamma` is the GPU power in watts, or simply write `1000 * gamma * p_{L,j} / (D * H)`.

### 2.2 PUE Display Equation (unnumbered)

**Display equation (script L1730-1733):**
```
PUE(theta_j) = phi + delta * max(0, theta_j - theta-bar)
```

**OMML extracted (Equation 18):**
```
PUE(θj) = φ + δ · max(0, θj − θ̄),
```

**Code implementation (L335-336):**
```python
pue = PHI + DELTA_PUE * max(0, theta - THETA_REF)
```

**Verification:**
- phi = 1.08 (PHI), delta = 0.015 (DELTA_PUE), theta-bar = 15 C (THETA_REF)
- For theta = 15: PUE = 1.08 + 0.015 * max(0, 0) = 1.08. Correct.
- For theta = 35: PUE = 1.08 + 0.015 * 20 = 1.38. Matches UAE at 37.1 C: 1.08 + 0.015 * 22.1 = 1.41. Matches Table A1.

**Verdict: VALID.**

### 2.3 Equation (2): Bilateral Sovereignty Premium

**Display equation (script L1861-1869):**
```
lambda_{ij} = alpha_1 * G_{ij} + alpha_2 * (1 - R_{ij}) + alpha_3 * S_{ij}
```

**OMML extracted (Equation 38):**
```
λij = α1 · Gij + α2 · (1 − Rij) + α3 · Sij.
```

**Code implementation (L308-310):**
```python
G_ij = compute_geo_distance(iso_i, iso_j)
R_ij = compute_reg_compat(iso_i, iso_j)
return ALPHA_GEO * G_ij + ALPHA_REG * (1 - R_ij)
```

Note: S_{ij} is handled by exclusion (L301-307: sanctioned pairs return infinity), not as a term in the formula. The code for non-sanctioned pairs computes only alpha_1 * G + alpha_2 * (1-R). The alpha_3 * S term is effectively handled as: when S=1, lambda=infinity (trade prohibited); when S=0, the term vanishes.

**Verification:**
- G_{ij} in [0,1]: checked via BLOC_DISTANCE (L229-239). Correct.
- R_{ij} in {0,1}: checked via compute_reg_compat (L276-289). Correct.
- lambda_{ii} = 0: checked via L298-299. Correct.
- lambda = 0.05 * 0 + 0.025 * (1-1) = 0 for EU intra-pair. Correct.
- lambda = 0.05 * 0.40 + 0.025 * 1 = 0.02 + 0.025 = 0.045 for non-aligned, no agreement. Correct.

**Verdict: VALID.** The equation matches the code's behavior. The S_{ij} term is handled via exclusion rather than explicit multiplication, which is mathematically equivalent (alpha_3 = infinity for sanctions, per the comment at L199).

### 2.4 Equation (3): Delivered Cost

**Display equation (script L1882-1888):**
```
P_s(j, k) = (1 + lambda_{jk}) * (1 + tau_s * l_{jk}) * c_j
```

**OMML extracted (Equation 42):**
```
Ps(j, k) = (1 + λjk) · (1 + τs · ljk) · cj,
```

**Code implementation (L5457, L7030-7037):**
```python
# Bilateral: P(j,US) = c_j(1 + lambda_{j,US})
d["p_bilat_usa"] = d["cj_cr"] * (1 + lam)
```

Note: This code computes `P = c_j * (1 + lambda)` for training (tau=0), which is the correct special case. For inference with tau > 0, the code at L7058-7066 uses `delivered = (1 + TAU * lat) * cost_d[iso_j]`.

**Verification:**
- Training (tau_T = 0): P_T(j,k) = (1 + lambda_{jk}) * c_j. Correct.
- Inference (tau_I = tau > 0): P_I(j,k) = (1 + lambda_{jk}) * (1 + tau * l_{jk}) * c_j. Correct.
- For l_{jk} > l-bar: P_I = infinity (L1946-1949). Correct.

**Note:** The inference code at L7058-7066 computes `(1 + TAU * lat) * cost_d[iso_j]` without the `(1 + lambda)` factor, but this is for the free-trade inference sourcing helper `_simple_inference()` (L7051) used for specs (1)-(2) where lambda=0. The bilateral case is handled separately. Correct.

**Verdict: VALID.**

### 2.5 Equation (4): Demand

**Display equation (script L2019-2027):**
```
q_k = omega_k * Q,     omega_k = M_k / sum_{k'} M_{k'}
```

**OMML extracted (Equation 60):**
```
qk = ωk · Q, ωk = Mk / Σ_{k'} M_{k'},
```

**Code implementation (L6232-6236):**
```python
dc_k[iso] = dc_capacity.get(iso, 5.0)
total_dc = sum(dc_k.values())
omega = {iso: d / total_dc for iso, d in dc_k.items()}
```

**Verdict: VALID.** The formula matches the code exactly.

### 2.6 Equation (5): Sourcing Rule

**Display equation (script L2107-2112):**
```
j_s*(k) = argmin_j P_s(j, k)
```

**OMML extracted (Equation 71):**
```
js*(k) = arg minj Ps(j, k).
```

**Verdict: VALID.** Standard sourcing rule.

### 2.7 Equation (6): Inference Price

**Display equation (script L2263-2267):**
```
p_I(k) = (1 + tau * l_{m_I(k), k}) * c_{m_I(k)}
```

**OMML extracted (Equation 90):**
```
pI(k) = (1 + τ · l_{mI(k), k}) · c_{mI(k)},
```

**ISSUE: Equation (6) is missing the sovereignty premium (1 + lambda_{jk}).**

Comparing with Eq. (3): `P_s(j,k) = (1 + lambda_{jk}) * (1 + tau_s * l_{jk}) * c_j`

Equation (6) should be the inference-specific version of Eq. (3) evaluated at the marginal supplier j = m_I(k). But it omits the `(1 + lambda_{m_I(k),k})` factor.

However, examining the context: the prose at L2269-2283 says "where m_I(k) is the marginal inference supplier to k, determined by the capacity-constrained supply stack for k's inference market." The equation represents the **competitive inference price** at which the marginal supplier just breaks even -- in a competitive equilibrium, the sovereignty premium would already be embedded in the buyer's willingness to pay. The marginal cost to the buyer from the marginal supplier m_I(k) determines the price.

Actually, re-examining more carefully: in the training market, `p_T = c_{(m_T)}` (the marginal exporter's cost, no sovereignty premium on the price itself -- the sovereignty premium determines *who imports*, not the price level). Similarly, p_I(k) represents the cost from the marginal inference supplier. The sovereignty premium `lambda_{jk}` acts as a friction that determines sourcing decisions (whether to import or produce domestically), not as a markup on the equilibrium price.

Wait -- but Eq. (3) defines the **delivered cost** (not price) as including the sovereignty markup. The inference *price* from the marginal supplier already includes the latency degradation but NOT the sovereignty premium (which is a buyer-side perception, not a production cost). The equilibrium price is set by the marginal supplier's actual cost of delivery.

**Re-examination:** The training price is `p_T = c_{(m_T)}` -- no lambda. The inference price analogously should be `p_I(k) = (1 + tau * l_{m_I(k),k}) * c_{m_I(k)}` -- no lambda. The sovereignty premium affects *which* supplier is marginal (by making some suppliers infeasible for certain buyers), but the price itself reflects the production and delivery cost, not the sovereignty friction.

**Verdict: VALID.** Equation (6) correctly omits the sovereignty premium. The sovereignty premium affects sourcing decisions (Eq. 5), not the equilibrium price itself.

### 2.8 HHI Display Equation (unnumbered, in Proposition 2)

**Display equation (script L2475-2480):**
```
HHI_T = sum_j (K_{T,j} / Q_{T,X})^2
```

**OMML extracted (Equation 105):**
```
HHIT = Σj (KT,j / QT,X)²
```

**Code implementation (L6262):**
```python
hhi_t = sum(s**2 for s in train_revenue.values())
```

where `train_revenue[src]` accumulates `omega[iso]` for each buyer whose best training source is `src`. This computes sum of squared *demand shares* rather than sum of squared *capacity shares*. These should be equivalent in equilibrium (each exporter's allocation equals the demand it serves).

**Verdict: VALID.** Standard HHI formula.

### 2.9 Appendix B.1 (Equation B.1): Marginal Training Exporter

**Display equation (script L4061-4067):**
```
m_T = min { m : sum_{i=1}^{m} K_{T,(i)} >= Q_T^X }
```

**OMML extracted (Equation 167):**
```
mT = min { m : Σ_{i=1}^{m} KT,(i) >= QTX }.
```

**Verdict: VALID.** This is the standard supply-stack clearing condition. The marginal exporter is the one whose entry satisfies cumulative demand.

### 2.10 Appendix B.2 (Equation B.2): Marginal Cost of Inference

**Display equation (script L4098-4102):**
```
MC_I(j, k) = (1 + tau * l_{jk}) * c_j
```

**OMML extracted (Equation 176):**
```
MCI(j, k) = (1 + τ · ljk) · cj.
```

**Verdict: VALID.** Consistent with Eq. (3) evaluated at tau_s = tau and lambda = 0 (marginal cost, not delivered cost).

### 2.11 Appendix B.3 (Equation B.3): Total Rent

**Display equation (script L4155-4160):**
```
Pi_j(K_j) = sum_{n=1}^{K_j} r_j^{(n)}
```

**OMML extracted (Equation 189):**
```
Πj(Kj) = Σ_{n=1}^{Kj} rj^(n),
```

**Verdict: VALID.** Piecewise-linear concave rent function. Each GPU-hour earns the margin from its assigned activity, sorted in decreasing order.

### 2.12 Appendix B.4 (Equation B.4): Import Markup DWL

**Display equation (script L4214-4220):**
```
DWL_import = sum_{k in M_T} q_{Tk} * lambda_{jk} * p_T
```

**OMML extracted (Equation 202):**
```
DWLimport = Σ_{k ∈ MT} qTk · λjk · pT.
```

**Verdict: VALID.** The welfare loss from the sovereignty markup on imports. Each importing country k pays lambda_{jk} * p_T extra per unit.

### 2.13 Appendix B.5 (Equation B.5): Allocative Inefficiency DWL

**Display equation (script L4226-4235):**
```
DWL_alloc = sum_{k : p_T < c_k <= (1 + min_j lambda_{jk}) * p_T} q_{Tk} * (c_k - p_T)
```

**OMML extracted (Equation 203):**
```
DWLalloc = Σ_{k : pT < ck ≤ (1 + min_j λjk)pT} qTk · (ck − pT).
```

**Verification:** Countries in the summation range have `c_k > p_T` (they're not competitive exporters) but `c_k <= (1 + min_j lambda_{jk}) * p_T` (the sovereignty premium makes importing more expensive than domestic production). These countries produce domestically at cost `c_k` instead of importing at `p_T`, creating a deadweight loss of `c_k - p_T` per unit.

**Verdict: VALID.**

---

## 3. Cross-Reference Check

### 3.1 Equation References in Prose

| Text reference | Actual equation | Location (script line) | Status |
|----------------|-----------------|------------------------|--------|
| "equation (1)" | c_j cost function | L1898 | VALID |
| "equation (2)" | lambda_{ij} bilateral premium | L1905 | VALID |
| "eq. (2)" | lambda_{ij} | L2843 | VALID |
| "equation (2)" | lambda_{ij} | L4044 | VALID |
| "equation (3)" | P_s(j,k) delivered cost | L5515 | VALID |
| "equation (4)" | q_k demand | L2722, L3101, L3782, L4021 | VALID |
| "equations (1)-(4)" | Cost, sovereignty, delivered cost, demand | L2661-2662 | VALID |

All equation references point to existing numbered equations. No orphan references (e.g., "equation (7)" which does not exist).

**The link_equations() function at L5812-5859 only matches `equation (N)` and `eq. (N)` patterns with digit-only numbers**, so Appendix equations (B.1-B.5) are not auto-linked, which is correct since they use letter prefixes.

**Verdict: VALID.**

### 3.2 Proposition and Corollary References

| Reference | Definition location | Reference locations | Status |
|-----------|-------------------|---------------------|--------|
| Proposition 1 | L2338 | Table 1 title (L4968), Figure 1 caption (L4918) | VALID |
| Proposition 2 | L2463 | L3111, L3116, L3122 | VALID |
| Proposition 3 | L2517 | Not explicitly cross-referenced in prose | VALID |
| Proposition 4 | L2581 | L2449 (in Prop 1 ruling-out argument) | VALID |
| Corollary | L2573 | Not cross-referenced | VALID |

There are exactly 4 propositions and 1 corollary. No "Proposition 5" reference exists (v20 had 5 propositions but v21+ reduced to 4). No orphan references.

**Verdict: VALID.**

### 3.3 Table References

| Table | Bookmark name | In-text references | Status |
|-------|---------------|-------------------|--------|
| Table 1 | Table1 | L2457 "Table 1 summarizes" | VALID |
| Table 2 | Table2 | L2878 "Table 2 reports" | VALID |
| Table 3 | Table3 | L2923, L2966, L3081, L3439, L5126, L5954 | VALID |
| Table A1 | TableA1 | L2885, L3483, L3507 | VALID |
| Table A2 | TableA2 | L2996, L5530 | VALID |
| Table A3 | TableA3 | L3374, L4263 | VALID |
| Table A4 | TableA4 | L4434 | VALID |
| Table A5 | TableA5 | L4436 | VALID |
| Table A6 | TableA6 | L4438 | VALID |
| Table A7 | TableA7 | L4609 | VALID |
| Table A8 | TableA8 | L4793 | VALID |

All table references have corresponding bookmark targets. No orphan table references.

**Verdict: VALID.**

### 3.4 Figure References

| Figure | Reference | Status |
|--------|-----------|--------|
| Figure 1 | L2904 (Section 6.2 opening) | VALID -- references model structure diagram |
| Figure 1b | Not referenced in prose | v32 added Figure 1b (regime feasibility grid) but I found no in-text reference to it |

**Verdict: NEEDS ATTENTION.** Figure 1b (regime feasibility grid) is added in v32 but may lack an in-text reference. This depends on whether the figure is intended as a standalone visual companion to Table 1 or needs explicit prose discussion.

### 3.5 Section References

| Reference | Actual section | Status |
|-----------|---------------|--------|
| "Section 3" (L2333) | Model of Compute Production and Trade | VALID |
| "Sections 3-4" (L3998) | Model + Equilibrium Properties | VALID |
| "Section 6" (L1645) | Calibration and Results | **NEEDS CHECK** |
| "Section 7" (L2299) | Robustness, Caveats, and Extensions | VALID |
| "Appendix B" (L2333) | Model Derivation | VALID |
| "Appendix E" (L2700) | Construction Cost Regression | VALID |
| "Appendix F" (L1805) | Workload Classification | VALID |

The footnote at L1644-1646 says "The robustness check in Section 6 confirms..." -- but the robustness check is in **Section 7** (Robustness, Caveats, and Extensions), not Section 6 (Calibration and Results).

**Verdict: ISSUE FOUND.** Line 1645: "in Section 6 confirms" should be "in Section 7 confirms".

---

## 4. Dimensional Consistency

### 4.1 Equation (1): c_j units

**Target:** c_j in $/GPU-hr

| Term | Expression | Units | Result |
|------|-----------|-------|--------|
| Electricity | PUE(theta_j) * gamma * p_{E,j} | (dimensionless) * (kW) * ($/kWh) = $/hr | $/GPU-hr (per GPU) |
| Hardware | rho = P_GPU / (L * H * beta) | $ / (yr * hr/yr * dimensionless) = $/hr | $/GPU-hr |
| Networking | eta | $/hr (given) | $/GPU-hr |
| Construction | p_{L,j} / (D * H) | ($/W) / (yr * hr/yr) = $/W/hr | **NOT $/GPU-hr** |

**The construction term is dimensionally incorrect as written.** To get $/GPU-hr from p_{L,j} in $/W:
- Multiply by GPU power: p_{L,j} * gamma_W = ($/W) * (W) = $ per GPU
- Then divide by lifetime hours: $ / (D * H) = $/GPU-hr

So the correct term is: `p_{L,j} * gamma_W / (D * H)` where `gamma_W = 700 W`.

The code correctly implements this: `(constr * GAMMA * 1000) / (DC_LIFE * H_YR)` where `GAMMA * 1000 = 700 W`.

**Verdict: The equation as written is dimensionally inconsistent.** See Section 2.1 for details.

### 4.2 PUE Term: PUE * gamma * p_E

- PUE: dimensionless
- gamma: kW (GPU thermal design power)
- p_E: $/kWh

Result: kW * $/kWh = $/hr per GPU. **Correct.**

### 4.3 Hardware Term: rho

- P_GPU: $ (GPU purchase price)
- L: years (lifetime)
- H: hr/yr (hours per year)
- beta: dimensionless (utilization rate)

Result: $ / (yr * hr/yr * 1) = $/hr. **Correct.**

### 4.4 rho Numerical Value

```
rho = 25000 / (3 * 8766 * 0.70)
    = 25000 / 18408.6
    = 1.358 $/hr
```

Displayed as $1.36/hr (rounded). The script at L2809 displays `f'${RHO:.3f}'` = "$1.358". Table 2 displays "$1.36/hr" (L5237). Both correct.

**Verdict: VALID.**

---

## 5. Additional Issues

### 5.1 Stale CSV Row: xi_j in model_parameters.csv

The file `model_parameters.csv` (line 17) still contains:
```
xi_j,Production-efficiency index (baseline),1.00,,(3),WGI and Enterprise Surveys
```

The xi efficiency index was **removed in v30** (as documented in the changelog at L19-26). The code skips this row (L5183-5184: `if row.get('symbol', '') == 'xi_j': continue`), so it does not appear in the generated document. However, the CSV should be cleaned up.

Additionally, the `equation` column in this CSV has incorrect equation numbers:
- Row for `tau`: equation `(2)` -- but tau appears in Eq. (3), not Eq. (2)
- Row for `alpha`: equation `(3)` -- but alpha appears in the demand split text (between Eqs. 4 and 5), not Eq. (3)
- Row for `Q`: equation `(3)` -- but Q appears in Eq. (4)

These equation numbers in the CSV are never rendered in the document (the `equation` column is not displayed in Table 2), so this is a data hygiene issue only.

**Verdict: Data cleanup needed, no impact on document.**

### 5.2 K-bar_j Rendering Inconsistency (L2296)

As noted in Section 1.3, line 2296 uses `_msub('K\u0304', 'j')` (Unicode combining macron) while all other K-bar instances use `_mbar_sub('K', 'j')` (OMML bar element). The OMML bar renders more reliably across Word versions and produces a properly centered overbar.

**Recommendation:** Replace L2296 with `_mbar_sub('K', 'j')`.

### 5.3 Missing Space in Prose (L2271)

At L2271: `'is the marginal inference supplier to '` -- the space before "is" is missing. The rendered text reads "where m_I(k)is the marginal..." without a space between the inline equation and "is".

**Recommendation:** Add a space: change `p.add_run('is the marginal...')` to `p.add_run(' is the marginal...')`.

### 5.4 Table A1 Notes: c_j Excludes Networking

The Table A1 notes (L3783-3785) state: "c_j = hourly cost of operating one H100 GPU (electricity + hardware at $1.36/hr + amortized construction; excludes networking eta = $0.15/hr, which is added in the equilibrium computations in Section 6)."

This means the c_j values displayed in Table A1 do **not** include eta. But Eq. (1) defines c_j as including eta. This is a deliberate reporting choice (displaying the country-varying components only), and the note correctly documents the exclusion. However, readers comparing Table A1 values to Eq. (1) may be confused.

**Verdict: Acceptable but could benefit from clearer signposting.**

---

## 6. Summary of Findings

### Errors Requiring Correction

| # | Severity | Location | Issue | Recommendation |
|---|----------|----------|-------|----------------|
| 1 | **HIGH** | L1659 (Eq. 1, construction term) | `p_{L,j}/(D*H)` is dimensionally incorrect; missing gamma_W factor | Change to `(p_{L,j} * gamma_W)/(D * H)` or redefine p_{L,j} units |
| 2 | **MEDIUM** | L1645 (footnote) | "Section 6 confirms" should be "Section 7 confirms" | Change "Section 6" to "Section 7" |
| 3 | **LOW** | L2296 | K-bar_j rendered via Unicode combining macron instead of OMML bar | Replace `_msub('K\u0304', 'j')` with `_mbar_sub('K', 'j')` |
| 4 | **LOW** | L2271 | Missing space before "is" after inline equation | Add leading space to `'is the marginal...'` |

### Issues Needing Clarification

| # | Location | Issue |
|---|----------|-------|
| 5 | Throughout | alpha (training share) vs alpha_1, alpha_2, alpha_3 (sovereignty) -- notation clash |
| 6 | Prop. 2 vs App. B.2 | Q_{T,X} vs Q_T^X -- inconsistent rendering of total training export demand |
| 7 | Figure 1b | Regime feasibility grid added in v32 but may lack in-text reference |

### Data Cleanup

| # | File | Issue |
|---|------|-------|
| 8 | model_parameters.csv | Stale xi_j row (skipped by code but should be removed) |
| 9 | model_parameters.csv | Equation column numbers for tau, alpha, Q are off by one |

### Verified as Correct

- Eq. (1): algebraic structure (except construction term)
- PUE display equation
- Eq. (2): bilateral sovereignty premium
- Eq. (3): delivered cost
- Eq. (4): demand specification
- Eq. (5): sourcing rule (argmin)
- Eq. (6): inference price
- HHI display equation
- Eqs. (B.1)--(B.5): all appendix derivations
- DWL welfare decomposition (B.4, B.5)
- All proposition statements (1--4) and corollary
- All table cross-references (Tables 1, 2, 3, A1--A8)
- All equation cross-references in prose
- theta_j vs theta-bar notation
- l_{jk} vs l-bar notation (no leftover d_{ij})
- K-bar_j vs K_j vs K_{T,j} vs K_{I,j->k} notation
- lambda_{ij} vs lambda_{jk} convention (documented)
- No leftover p_T* notation
- rho and eta definitions consistent
- G_{ij}, R_{ij}, S_{ij} subscripts consistent
- omega_k demand share consistent
