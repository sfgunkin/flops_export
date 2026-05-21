/*===========================================================================
  FLOPs Export Paper — Full Model Replication in Stata

  Replicates all calculations from add_calibration_v30.py:
    1. Cost calibration & cost-recovery adjustment
    2. Demand calibration (ω from DC capacity)
    3. Bilateral sovereignty premium λ_{ij}
    4. Capacity-constrained training equilibrium
    5. Inference sourcing (latency-weighted delivered cost)
    6. Welfare, HHI, regime classification
    7. Sensitivity analysis & Table 3 data

  Input:  Data/calibration_results_v3.csv, Data/country_pair_latency.csv,
          Data/raw/capacity/dc_capacity_mw.csv
  Output: Data/stata_results/country_results.{dta,csv}
===========================================================================*/

clear all
set more off
set type double

* ── Paths ─────────────────────────────────────────────────────────────────────
global root "F:/onedrive/__documents/papers/_Submitted/FLOPsExport"
global data "$root/Data"
global raw  "$root/Data/raw"
global out  "$root/Data/stata_results"
capture mkdir "$out"


* ══════════════════════════════════════════════════════════════════════════════
* PARAMETERS
* ══════════════════════════════════════════════════════════════════════════════

scalar TAU       = 0.0008
scalar PHI       = 1.08
scalar DELTA_PUE = 0.015
scalar THETA_REF = 15.0
scalar GAMMA     = 0.700
scalar GPU_PRICE = 25000
scalar GPU_LIFE  = 3
scalar GPU_UTIL  = 0.70
scalar DC_LIFE   = 15
scalar H_YR      = 365.25 * 24
scalar RHO       = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL)
scalar ETA       = 0.15
scalar ALPHA     = 0.50
scalar Q_TOTAL   = 60e9
scalar ALPHA_GEO = 0.05
scalar ALPHA_REG = 0.025
scalar LAM_UNI   = 0.10
scalar W_TIER1   = 0.10
scalar W_TIER2   = 0.20
scalar W_TIER3   = 0.70
scalar L_BAR     = 200.0


* ══════════════════════════════════════════════════════════════════════════════
* PROGRAMS
* ══════════════════════════════════════════════════════════════════════════════

* --------------------------------------------------------------------------
* solve_equilibrium: iterative capacity-constrained training price
*   Arguments: bilateral (0/1)
*   Requires:  c_j_cr, sanctioned, omega, k_bar, lambda_min_k in memory
*   Returns:   scalars r(p_T), r(Q_TX)
* --------------------------------------------------------------------------
capture program drop solve_equilibrium
program define solve_equilibrium, rclass
    syntax , bilateral(integer)

    quietly summarize c_j_cr if sanctioned == 0
    scalar _p_T = r(min)

    forvalues iter = 1/30 {
        * Export demand
        quietly {
            if `bilateral' {
                gen _imp = (lambda_min_k < .) & ///
                    (c_j_cr > (1 + lambda_min_k) * _p_T) & !sanctioned
            }
            else {
                gen _imp = (c_j_cr > _p_T) & !sanctioned
            }
            egen _Q = total(ALPHA * omega * Q_TOTAL * _imp)
            summarize _Q, meanonly
            scalar _Q_TX = r(mean)
            drop _imp _Q
        }

        * Walk supply stack
        gsort c_j_cr
        scalar _cum = 0
        scalar _p_new = _p_T
        scalar _found = 0
        forvalues i = 1/`=_N' {
            if sanctioned[`i'] continue
            scalar _cum = _cum + k_bar[`i']
            if _cum >= _Q_TX & _Q_TX > 0 & !_found {
                scalar _p_new = c_j_cr[`i']
                scalar _found = 1
            }
        }

        if abs(_p_new - _p_T) < 0.0001 {
            scalar _p_T = _p_new
            continue, break
        }
        scalar _p_T = _p_new
    }

    return scalar p_T   = _p_T
    return scalar Q_TX  = _Q_TX
    scalar drop _p_T _p_new _Q_TX _cum _found
end

* --------------------------------------------------------------------------
* allocate_exports: assign capacity-constrained export shares
*   Arguments: suffix for variable names
*   Reads:     scalars _alloc_pT (training price), Q_TX (export demand)
*   Creates:   is_exporter_`sfx', export_share_`sfx', export_pct_`sfx',
*              hhi_T_`sfx'
* --------------------------------------------------------------------------
capture program drop allocate_exports
program define allocate_exports
    syntax , suffix(string)

    local s = "`suffix'"

    * Use scalar directly to avoid float truncation from syntax pt(real)
    gen is_exporter_`s' = (c_j_cr <= _alloc_pT) & !sanctioned
    gen export_share_`s' = 0

    gsort c_j_cr
    scalar _rem = Q_TX
    forvalues i = 1/`=_N' {
        if sanctioned[`i'] | c_j_cr[`i'] > _alloc_pT continue
        local a = min(k_bar[`i'], _rem)
        quietly replace export_share_`s' = `a' if _n == `i'
        scalar _rem = _rem - `a'
        if _rem <= 0 continue, break
    }
    scalar drop _rem

    egen _tot = total(export_share_`s')
    gen export_pct_`s' = export_share_`s' / _tot * 100 if export_share_`s' > 0

    gen _sq = (export_share_`s' / _tot)^2 if export_share_`s' > 0
    egen hhi_T_`s' = total(_sq)
    drop _sq _tot
end


* ══════════════════════════════════════════════════════════════════════════════
* 1. LOAD AND MERGE DATA
* ══════════════════════════════════════════════════════════════════════════════

import delimited "$data/calibration_results_v3.csv", clear varnames(1)
rename (rank c_j_total c_j_electricity c_j_hardware c_j_construction ///
        p_e_usd_kwh theta_summer_c p_l_usd_per_w) ///
       (rank_orig c_j_total_csv c_j_elec_csv c_j_hw_csv c_j_constr_csv ///
        p_E theta p_L)
destring rank_orig c_j_total_csv c_j_elec_csv c_j_hw_csv ///
         c_j_constr_csv pue p_E theta p_L, replace force
sort iso3
tempfile cal
save `cal'

import delimited "$raw/capacity/dc_capacity_mw.csv", clear varnames(1)
rename capacity_mw dc_cap_mw
keep iso3 dc_cap_mw n_datacenters source_tier
sort iso3
tempfile dc
save `dc'

use `cal', clear
merge 1:1 iso3 using `dc', keep(master match)
replace dc_cap_mw = 5 if mi(dc_cap_mw) | _merge == 1
drop _merge

display "Loaded " _N " countries"


* ══════════════════════════════════════════════════════════════════════════════
* 2. COST CALIBRATION & COST-RECOVERY ADJUSTMENT
* ══════════════════════════════════════════════════════════════════════════════

* PUE from primitives (cross-check only; use CSV pue for exact replication)
gen pue_calc = PHI + DELTA_PUE * max(0, theta - THETA_REF)

* Cost components (use CSV pue to match Python generation script)
gen c_elec      = GAMMA * p_E * pue
gen c_hardware  = RHO
gen c_network   = ETA
gen c_construct = (p_L * GAMMA * 1000) / (DC_LIFE * H_YR)
gen c_j_raw     = c_elec + c_hardware + c_network + c_construct

* Verify against CSV
gen _cdiff = abs(c_j_raw - (c_j_total_csv + ETA))
quietly summarize _cdiff
display "Max cost replication error: " %8.6f r(max)
drop _cdiff

* Raw cost ranking
gsort c_j_raw
gen rank_raw = _n

* Cost-reflective electricity prices (LRMC at opportunity-cost fuel price)
gen p_E_cr = p_E
quietly {
    replace p_E_cr = 0.085 if iso3 == "IRN"
    replace p_E_cr = 0.070 if iso3 == "TKM"
    replace p_E_cr = 0.065 if iso3 == "DZA"
    replace p_E_cr = 0.080 if iso3 == "EGY"
    replace p_E_cr = 0.090 if iso3 == "UZB"
    replace p_E_cr = 0.100 if iso3 == "QAT"
    replace p_E_cr = 0.100 if iso3 == "SAU"
    replace p_E_cr = 0.095 if iso3 == "ARE"
    replace p_E_cr = 0.065 if iso3 == "RUS"
    replace p_E_cr = 0.085 if iso3 == "KAZ"
    replace p_E_cr = 0.080 if iso3 == "NGA"
    replace p_E_cr = 0.095 if iso3 == "ZAF"
    replace p_E_cr = 0.050 if iso3 == "ETH"
}

gen cr_adjusted = (p_E_cr != p_E)
gen subsidy_gap = (p_E_cr - p_E) * 1000 if cr_adjusted

* Cost-recovery cost and ranking
gen c_elec_cr = GAMMA * p_E_cr * pue
gen c_j_cr    = c_elec_cr + c_hardware + c_network + c_construct
gsort c_j_cr
gen rank_cr = _n
gen delta_rank = rank_raw - rank_cr

display _newline "Top 10 (cost-recovery):"
list rank_cr iso3 country c_j_cr delta_rank if rank_cr <= 10, sep(0) noobs

count if cr_adjusted
local n_adj = r(N)
quietly summarize subsidy_gap if cr_adjusted
display "`n_adj' countries adjusted; gap $" %3.0f r(min) "-$" %3.0f r(max) "/MWh"


* ══════════════════════════════════════════════════════════════════════════════
* 3. DEMAND CALIBRATION
* ══════════════════════════════════════════════════════════════════════════════

egen total_dc = total(dc_cap_mw)
gen omega     = dc_cap_mw / total_dc
gen k_bar     = dc_cap_mw * (1000 / GAMMA) * H_YR * GPU_UTIL

gsort -omega
display _newline "Top 5 demand centers:"
list iso3 country omega dc_cap_mw in 1/5, sep(0) noobs
display "Total DC capacity: " %12.0fc total_dc[1] " MW"


* ══════════════════════════════════════════════════════════════════════════════
* 4. BLOCS, SANCTIONS, REGULATORY MEMBERSHIP
* ══════════════════════════════════════════════════════════════════════════════

gen bloc = "N"
foreach iso in USA CAN GBR FRA DEU ITA ESP PRT NLD BEL LUX AUT CHE IRL ///
    DNK NOR SWE FIN ISL GRC CZE POL HUN SVK SVN EST LVA LTU HRV BGR ///
    ROU CYP MLT JPN KOR AUS NZL ISR TWN {
    quietly replace bloc = "W" if iso3 == "`iso'"
}
foreach iso in CHN RUS BLR IRN TKM {
    quietly replace bloc = "C" if iso3 == "`iso'"
}

gen sanctioned = inlist(iso3, "IRN", "RUS", "BLR", "TKM")

gen eu = inlist(iso3, "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK") | ///
         inlist(iso3, "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL") | ///
         inlist(iso3, "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL") | ///
         inlist(iso3, "PRT", "ROU", "SVK", "SVN", "ESP", "SWE")

gen apec_cbpr = inlist(iso3, "AUS", "CAN", "JPN", "KOR", "MEX", "PHL") | ///
               inlist(iso3, "SGP", "TWN", "USA")

gen depa = inlist(iso3, "SGP", "CHL", "NZL")

sort iso3
tempfile countries
save `countries'


* ══════════════════════════════════════════════════════════════════════════════
* 5. BILATERAL LAMBDA MATRIX
* ══════════════════════════════════════════════════════════════════════════════

* Build left (i) and right (j) sides for cross join
use `countries', clear
keep iso3 bloc sanctioned eu apec_cbpr depa c_j_cr
rename (iso3 bloc sanctioned eu apec_cbpr depa c_j_cr) ///
       (iso_i bloc_i sanc_i eu_i apec_i depa_i c_i)
tempfile left
save `left'

use `countries', clear
keep iso3 bloc sanctioned eu apec_cbpr depa c_j_cr
rename (iso3 bloc sanctioned eu apec_cbpr depa c_j_cr) ///
       (iso_j bloc_j sanc_j eu_j apec_j depa_j c_j)
tempfile right
save `right'

use `left', clear
cross using `right'

* Geopolitical distance G_{ij} — matches BLOC_DISTANCE in Python
gen G_ij = 0.20                                                    // N-N default
replace G_ij = 0    if bloc_i == bloc_j & bloc_i != "N"            // W-W or C-C (allies)
replace G_ij = 0.40 if (bloc_i == "W") + (bloc_j == "W") == 1 & ///
                        (bloc_i == "N") + (bloc_j == "N") == 1     // W-N
replace G_ij = 0.55 if (bloc_i == "C") + (bloc_j == "C") == 1 & ///
                        (bloc_i == "N") + (bloc_j == "N") == 1     // C-N
replace G_ij = 0.95 if (bloc_i == "W") + (bloc_j == "W") == 1 & ///
                        (bloc_i == "C") + (bloc_j == "C") == 1     // W-C
replace G_ij = 0    if iso_i == iso_j                              // domestic

* Regulatory compatibility R_{ij}
gen R_ij = (iso_i == iso_j)
replace R_ij = 1 if eu_i   & eu_j
replace R_ij = 1 if apec_i & apec_j
replace R_ij = 1 if depa_i & depa_j

* Bilateral lambda λ_{ij}
gen lambda_ij = ALPHA_GEO * G_ij + ALPHA_REG * (1 - R_ij)
replace lambda_ij = . if iso_i == iso_j                            // domestic

* Sanctions → infinite (missing), except within-bloc sanctioned pairs
replace lambda_ij = . if (sanc_i | sanc_j) & ///
    !(sanc_i & sanc_j & bloc_i == bloc_j)

* Extract country-level aggregates
bysort iso_i: egen lambda_min_k = min(lambda_ij)

* λ to USA (for Table 3)
gen lambda_usa = lambda_ij if iso_j == "USA"

* Save full bilateral lambda matrix for bilateral inference sourcing
tempfile full_lambda
preserve
keep iso_i iso_j lambda_ij
save `full_lambda'
restore

* Collapse to country-level
preserve
keep iso_i lambda_min_k
duplicates drop iso_i, force
rename iso_i iso3
sort iso3
tempfile min_lam
save `min_lam'
restore

preserve
keep if iso_j == "USA"
keep iso_i lambda_ij
rename (iso_i lambda_ij) (iso3 lambda_usa)
sort iso3
tempfile lam_usa
save `lam_usa'
restore


* ══════════════════════════════════════════════════════════════════════════════
* 6. INFERENCE SOURCING
* ══════════════════════════════════════════════════════════════════════════════

import delimited "$data/country_pair_latency.csv", clear varnames(1)
keep iso3_from iso3_to avg_ms
* Latency direction: from = supplier (iso_j), to = buyer (iso_k)
rename (iso3_from iso3_to avg_ms) (iso_j iso_k latency)
tempfile latency
save `latency'

* Suppliers (all countries with costs)
use `countries', clear
keep iso3 c_j_cr
rename (iso3 c_j_cr) (iso_j c_j_inf)
tempfile suppliers
save `suppliers'

* Buyers × suppliers
use `countries', clear
keep iso3 c_j_cr omega sanctioned
rename (iso3 c_j_cr) (iso_k c_k_inf)
cross using `suppliers'
merge 1:1 iso_k iso_j using `latency', keep(master match)
rename _merge has_latency

replace latency = 5.0 if iso_k == iso_j & mi(latency)

* Delivered inference cost P_I(k,j) = (1 + τ·latency) · c_j
* L_BAR: exclude cross-border pairs with latency > 200ms
gen P_I_delivered = (1 + TAU * latency) * c_j_inf if has_latency == 3 | iso_k == iso_j
replace P_I_delivered = . if latency > L_BAR & iso_k != iso_j
replace P_I_delivered = . if !sanctioned & inlist(iso_j, "IRN", "RUS", "BLR", "TKM")

* Domestic inference cost
gen P_I_domestic = (1 + TAU * latency) * c_k_inf if iso_k == iso_j

* Best source per buyer
bysort iso_k (P_I_delivered): gen _rank = _n if !mi(P_I_delivered)

preserve
keep if _rank == 1
keep iso_k iso_j P_I_delivered
rename (iso_k iso_j P_I_delivered) (iso3 inf_source P_I_best)
sort iso3
tempfile inf_best
save `inf_best'
restore

preserve
keep if iso_k == iso_j
keep iso_k P_I_domestic
rename iso_k iso3
sort iso3
tempfile inf_dom
save `inf_dom'
restore


* ══════════════════════════════════════════════════════════════════════════════
* 7. EQUILIBRIUM
* ══════════════════════════════════════════════════════════════════════════════

use `countries', clear
sort iso3
merge 1:1 iso3 using `min_lam', nogen
merge 1:1 iso3 using `lam_usa', nogen keep(master match)
merge 1:1 iso3 using `inf_best', nogen keep(master match)
merge 1:1 iso3 using `inf_dom',  nogen keep(master match)

gen imports_inf = (inf_source != iso3) if inf_source != ""

* ── Pass 1: λ=0 (pure cost) ──────────────────────────────────────────────────
solve_equilibrium, bilateral(0)
scalar p_T_0    = r(p_T)
scalar Q_TX     = r(Q_TX)
scalar _alloc_pT = p_T_0
display _newline "p_T (λ=0):        $" %7.4f p_T_0 "/hr"

allocate_exports, suffix(0)

display "Training exporters (λ=0):"
list iso3 country c_j_cr export_pct_0 dc_cap_mw if is_exporter_0, sep(0) noobs
display "HHI_T (λ=0) = " %7.4f hhi_T_0[1]

* ── Pass 2: bilateral λ ──────────────────────────────────────────────────────
solve_equilibrium, bilateral(1)
scalar p_T_b    = r(p_T)
scalar Q_TX     = r(Q_TX)
scalar _alloc_pT = p_T_b
display _newline "p_T (bilateral):  $" %7.4f p_T_b "/hr"

allocate_exports, suffix(b)

display "Training exporters (bilateral):"
list iso3 country c_j_cr export_pct_b dc_cap_mw if is_exporter_b, sep(0) noobs
display "HHI_T (bilateral) = " %7.4f hhi_T_b[1]


* ══════════════════════════════════════════════════════════════════════════════
* 8. INFERENCE HHI & WELFARE
* ══════════════════════════════════════════════════════════════════════════════

* Inference revenue shares (cross-border only)
preserve
keep if inf_source != iso3 & inf_source != ""
collapse (sum) omega, by(inf_source)
rename (inf_source omega) (iso3 inf_rev_share)
gen _sq = inf_rev_share^2
egen hhi_I = total(_sq)
drop _sq
sort iso3
tempfile inf_rev
save `inf_rev'
restore

merge 1:1 iso3 using `inf_rev', nogen keep(master match)

display _newline "HHI_I = " %7.4f hhi_I[1]
gsort -inf_rev_share
display "Top 5 inference exporters:"
list iso3 country inf_rev_share if !mi(inf_rev_share) & _n <= 5, sep(0) noobs

* Welfare (uniform specification)
quietly summarize c_j_cr if !sanctioned
scalar c_min = r(min)

gen welfare_train_k = omega * max(0, c_j_cr - c_min)
gen welfare_inf_k   = omega * max(0, P_I_domestic - P_I_best) if !mi(P_I_best)
egen welfare_train  = total(welfare_train_k)
egen welfare_inf    = total(welfare_inf_k)

gen _wc = omega * c_j_cr
egen weighted_avg_cost = total(_wc)
drop _wc

scalar welfare_total = welfare_train[1] + welfare_inf[1]
scalar welfare_pct   = welfare_total / weighted_avg_cost[1] * 100

display _newline "Welfare loss: $" %7.4f welfare_total "/hr (" ///
    %5.2f welfare_pct "%)"


* ══════════════════════════════════════════════════════════════════════════════
* 9. REGIME CLASSIFICATION (5-type: EE, IE, ID, DD, II)
* ══════════════════════════════════════════════════════════════════════════════

* Training domestic if λ_min >= λ* = c_k/p_T - 1, or c_k <= p_T
gen lambda_star_k = c_j_cr / p_T_b - 1 if p_T_b > 0
gen is_dom_train  = (lambda_min_k >= lambda_star_k) | (c_j_cr <= p_T_b) ///
                    if !mi(lambda_min_k)
replace is_dom_train = 1 if c_j_cr <= p_T_b & mi(lambda_min_k)

gen is_dom_inf = (inf_source == iso3) if inf_source != ""

* Inference exporters
preserve
keep if inf_source != iso3 & inf_source != ""
keep inf_source
duplicates drop
rename inf_source iso3
gen is_inf_exporter = 1
sort iso3
tempfile inf_exp
save `inf_exp'
restore

merge 1:1 iso3 using `inf_exp', nogen keep(master match)
replace is_inf_exporter = 0 if mi(is_inf_exporter)

* Classify
gen regime = "II"
replace regime = "DD" if is_dom_train & is_dom_inf
replace regime = "ID" if !is_dom_train & is_dom_inf
replace regime = "IE" if is_inf_exporter & !is_dom_train
replace regime = "EE" if is_exporter_b
replace regime = "DD" if sanctioned

display _newline "Regime classification:"
tab regime


* ══════════════════════════════════════════════════════════════════════════════
* 10. TABLE 3: BILATERAL DELIVERED PRICE P(j, USA)
* ══════════════════════════════════════════════════════════════════════════════

gen p_bilat_usa = c_j_cr * (1 + lambda_usa) if !mi(lambda_usa)
replace p_bilat_usa = . if sanctioned

gsort c_j_cr
display _newline "Table 3 preview (top 15):"
list rank_cr iso3 country c_j_raw c_j_cr p_bilat_usa regime delta_rank ///
    in 1/15, sep(5) noobs


* ══════════════════════════════════════════════════════════════════════════════
* 11. SENSITIVITY ANALYSIS
* ══════════════════════════════════════════════════════════════════════════════

gen developing = 0
foreach iso in CHN KGZ XKX MNE ETH VNM IND KEN ARE EGY DZA UZB TJK TKM ///
    ALB MKD GEO ARM MDA UKR BIH SRB IDN MYS PHL THA COL MEX BRA ARG CHL ///
    NGA ZAF MAR SEN PAK {
    quietly replace developing = 1 if iso3 == "`iso'"
}

display _newline "Sensitivity analysis:"
local rho_base = strofreal(RHO, "%6.4f")
foreach label in baseline low_hw high_hw {
    if "`label'" == "baseline" local rho_val = RHO
    if "`label'" == "low_hw"   local rho_val = 1.30
    if "`label'" == "high_hw"  local rho_val = 1.42

    gen c_j_`label' = c_elec_cr + `rho_val' + c_network + c_construct
    gsort c_j_`label'
    gen rank_`label' = _n

    quietly count if rank_`label' <= 15 & developing
    local dev15 = r(N)

    scalar _spread = (c_j_`label'[_N] - c_j_`label'[1]) / c_j_`label'[1] * 100

    display "  [`label'] rho=$`rho_val': dev_top15=`dev15', " ///
        "spread=" %4.1f _spread "%"
    list iso3 country c_j_`label' if rank_`label' <= 5, sep(0) noobs
}
scalar drop _spread


* ══════════════════════════════════════════════════════════════════════════════
* 12. SUMMARY
* ══════════════════════════════════════════════════════════════════════════════

display _newline(2) "=== PAPER RESULTS SUMMARY ==="

display _newline "Parameters:"
display "  rho = $" %6.4f RHO "/hr,  eta = $" %4.2f ETA "/hr"
display "  gamma = " %5.3f GAMMA " kW,  phi = " %4.2f PHI
display "  tau = " %6.4f TAU ",  alpha = " %3.0f ALPHA*100 "%"
display "  Q_total = " %3.0f Q_TOTAL/1e9 "B GPU-hrs"

display _newline "Equilibrium:"
display "  p_T (lam=0)    = $" %7.4f p_T_0 "/hr"
display "  p_T (bilateral)= $" %7.4f p_T_b "/hr"
quietly count if is_exporter_0
display "  Exporters (lam=0)    = " r(N)
quietly count if is_exporter_b
display "  Exporters (bilateral)= " r(N)
display "  HHI_T (lam=0)    = " %7.4f hhi_T_0[1]
display "  HHI_T (bilateral)= " %7.4f hhi_T_b[1]
display "  HHI_I            = " %7.4f hhi_I[1]
display "  Welfare loss     = " %5.2f welfare_pct "%"

display _newline "Regimes:"
tab regime

display _newline "Cost-recovery: `n_adj' countries adjusted"


* ══════════════════════════════════════════════════════════════════════════════
* 13. EXPORT TABLES TO EXCEL
* ══════════════════════════════════════════════════════════════════════════════

capture mkdir "$root/Output"

* --------------------------------------------------------------------------
* TABLE 1: Country regime taxonomy (5×5 conceptual grid)
* --------------------------------------------------------------------------
quietly {
    putexcel set "$root/Output/Table1_regime_taxonomy.xlsx", replace

    * Header row
    putexcel A1 = ""
    putexcel B1 = ""
    putexcel C1 = "Training"
    putexcel D1 = ""
    putexcel A2 = ""
    putexcel B2 = ""
    putexcel C2 = "Exports"
    putexcel D2 = "Domestic"

    putexcel A3 = "Inference"
    putexcel B3 = "Exports"
    putexcel C3 = "EE"
    putexcel D3 = "IE"

    putexcel A4 = ""
    putexcel B4 = "Domestic"
    putexcel C4 = "ID (hybrid)"
    putexcel D4 = "DD"

    putexcel A5 = ""
    putexcel B5 = "Imports"
    putexcel C5 = "—"
    putexcel D5 = "II"

    * Bold headers
    putexcel C1:D1, bold
    putexcel C2:D2, bold
    putexcel A3:B4, bold
}
display "Table 1 saved."


* --------------------------------------------------------------------------
* TABLE 2: Model parameters (from CSV)
* --------------------------------------------------------------------------
quietly {
    preserve
    import delimited "$data/model_parameters.csv", clear varnames(1)
    drop if symbol == "xi_j"

    * Build value+unit column
    gen val_display = value + " " + unit if unit != ""
    replace val_display = value if unit == ""
    * Special formatting
    replace val_display = "$25,000" if symbol == "P_GPU"
    replace val_display = "$" + strofreal(25000 / (3 * 8766 * 0.70), "%5.2f") + "/hr" if symbol == "rho"
    replace val_display = "$0.15/hr" if symbol == "eta"

    putexcel set "$root/Output/Table2_model_parameters.xlsx", replace
    putexcel A1 = "Parameter" B1 = "Symbol" C1 = "Value" D1 = "Source"
    putexcel A1:D1, bold

    local n = _N
    forvalues i = 1/`n' {
        local r = `i' + 1
        putexcel A`r' = description[`i']
        putexcel B`r' = symbol[`i']
        putexcel C`r' = val_display[`i']
        putexcel D`r' = source[`i']
    }
    restore
}
display "Table 2 saved."


* --------------------------------------------------------------------------
* TABLE 3: Country rankings (top 25, 3 specifications, 9 columns)
*   - Proper 4-type classification (EE/IE/DD/II) per spec
*   - Inference exporters computed per cost spec
*   - Bilateral inference uses sovereignty-adjusted delivered cost
* --------------------------------------------------------------------------

* Fix USA bilateral price (domestic, no sovereignty premium)
quietly replace p_bilat_usa = c_j_cr if iso3 == "USA"

* ---- Step A: Raw equilibrium price ----
* solve_equilibrium reads c_j_cr, so temporarily swap to raw costs
quietly {
    gen _save_c = c_j_cr
    replace c_j_cr = c_j_raw
}
solve_equilibrium, bilateral(0)
scalar p_T_raw = r(p_T)
quietly {
    replace c_j_cr = _save_c
    drop _save_c
}

* ---- Step B: Raw inference exporters (no sovereignty, raw costs) ----
quietly {
    tempfile _main_t3
    save `_main_t3'

    * Load latency pairs
    import delimited "$data/country_pair_latency.csv", clear varnames(1)
    keep iso3_from iso3_to avg_ms
    rename (iso3_from iso3_to avg_ms) (supplier buyer lat_ms)
    tempfile _lat_pairs
    save `_lat_pairs'

    * Add domestic self-pairs (default 5ms)
    use `_main_t3', clear
    keep iso3
    rename iso3 buyer
    gen supplier = buyer
    gen lat_ms = 5.0
    append using `_lat_pairs'
    bysort buyer supplier (lat_ms): keep if _n == 1

    * Drop pairs exceeding latency threshold
    drop if lat_ms > L_BAR & buyer != supplier

    * Merge supplier raw cost + sanctioned
    rename supplier iso3
    merge m:1 iso3 using `_main_t3', keepusing(c_j_raw sanctioned) keep(match)
    rename (iso3 c_j_raw sanctioned) (supplier c_sup sanc_sup)
    drop _merge

    * Merge buyer sanctioned
    rename buyer iso3
    merge m:1 iso3 using `_main_t3', keepusing(sanctioned) keep(match)
    rename (iso3 sanctioned) (buyer sanc_buy)
    drop _merge

    * Delivered cost: P = (1 + tau * lat) * c_j
    gen P_del = (1 + TAU * lat_ms) * c_sup
    * Block sanctioned suppliers for non-sanctioned buyers
    replace P_del = . if !sanc_buy & sanc_sup

    * Best source per buyer
    bysort buyer (P_del): gen _rk = _n if !mi(P_del)
    keep if _rk == 1
    keep buyer supplier

    * Inference exporters = serve someone cross-border
    keep if buyer != supplier
    keep supplier
    duplicates drop
    rename supplier iso3
    gen is_inf_exp_raw = 1
    sort iso3
    tempfile _inf_raw
    save `_inf_raw'
}

* ---- Step C: Bilateral inference exporters (with sovereignty, CR costs) ----
quietly {
    * Save latency CSV to tempfile for merging
    import delimited "$data/country_pair_latency.csv", clear varnames(1)
    keep iso3_from iso3_to avg_ms
    tempfile _lat_direct
    save `_lat_direct'

    * Start from full bilateral lambda matrix
    use `full_lambda', clear
    * Lambda has (iso_i=buyer, iso_j=supplier)
    * Latency: need from=supplier to=buyer, so iso3_from=iso_j, iso3_to=iso_i
    rename (iso_j iso_i) (iso3_from iso3_to)
    merge 1:1 iso3_from iso3_to using `_lat_direct', keepusing(avg_ms) keep(master match)
    drop _merge
    rename (iso3_from iso3_to avg_ms) (supplier buyer lat_ms)

    * Default 5ms for domestic self-pairs without latency data
    replace lat_ms = 5.0 if buyer == supplier & mi(lat_ms)
    * Drop non-domestic pairs without latency
    drop if mi(lat_ms) & buyer != supplier

    * Merge supplier CR cost + sanctioned
    rename supplier iso3
    merge m:1 iso3 using `_main_t3', keepusing(c_j_cr sanctioned) keep(match)
    rename (iso3 c_j_cr sanctioned) (supplier c_sup sanc_sup)
    drop _merge

    * Merge buyer CR cost + sanctioned
    rename buyer iso3
    merge m:1 iso3 using `_main_t3', keepusing(c_j_cr sanctioned) keep(match)
    rename (iso3 c_j_cr sanctioned) (buyer c_buy sanc_buy)
    drop _merge

    * Delivered bilateral inference cost
    * Non-domestic: (1 + lambda_{kj}) * (1 + tau * lat) * c_j
    gen P_bilat = (1 + lambda_ij) * (1 + TAU * lat_ms) * c_sup if !mi(lambda_ij)
    * Domestic: (1 + tau * lat) * c_k (no sovereignty premium)
    replace P_bilat = (1 + TAU * lat_ms) * c_buy if buyer == supplier
    * Block sanctioned suppliers for non-sanctioned buyers
    replace P_bilat = . if !sanc_buy & sanc_sup

    * Best source per buyer
    bysort buyer (P_bilat): gen _rk = _n if !mi(P_bilat)
    keep if _rk == 1
    keep buyer supplier
    rename (buyer supplier) (iso3 inf_source_bilat)
    sort iso3
    tempfile _inf_bilat_src
    save `_inf_bilat_src'

    * Bilateral inference exporters = serve someone cross-border
    keep if iso3 != inf_source_bilat
    keep inf_source_bilat
    duplicates drop
    rename inf_source_bilat iso3
    gen is_inf_exp_bilat = 1
    sort iso3
    tempfile _inf_bilat_exp
    save `_inf_bilat_exp'
}

* ---- Step D: Merge results and classify types ----
quietly {
    use `_main_t3', clear
    merge 1:1 iso3 using `_inf_raw', nogen keep(master match)
    replace is_inf_exp_raw = 0 if mi(is_inf_exp_raw)

    merge 1:1 iso3 using `_inf_bilat_src', nogen keep(master match)
    gen is_dom_inf_bilat = (inf_source_bilat == iso3) if !mi(inf_source_bilat)
    replace is_dom_inf_bilat = 1 if mi(inf_source_bilat)

    merge 1:1 iso3 using `_inf_bilat_exp', nogen keep(master match)
    replace is_inf_exp_bilat = 0 if mi(is_inf_exp_bilat)

    * Spec (1) Raw: 4-type (EE/IE/DD/II)
    gen type_raw = "II"
    replace type_raw = "EE" if c_j_raw <= p_T_raw & !sanctioned
    replace type_raw = "IE" if is_inf_exp_raw & c_j_raw > p_T_raw & !sanctioned
    replace type_raw = "DD" if sanctioned

    * Spec (2) CR: 4-type (EE/IE/DD/II)
    gen type_cr = "II"
    replace type_cr = "EE" if c_j_cr <= p_T_0 & !sanctioned
    replace type_cr = "IE" if is_inf_exporter & c_j_cr > p_T_0 & !sanctioned
    replace type_cr = "DD" if sanctioned

    * Spec (3) Bilateral: 4-type (EE/IE/DD/II)
    * Uses bilateral lambda for both training and inference
    gen type_bilat = "II"
    replace type_bilat = "DD" if is_dom_train & is_dom_inf_bilat ///
        & !is_exporter_b & !sanctioned
    replace type_bilat = "IE" if is_inf_exp_bilat & !is_dom_train ///
        & !is_exporter_b & !sanctioned
    replace type_bilat = "EE" if is_exporter_b
    replace type_bilat = "DD" if sanctioned

    * Flags: * = sanctioned, dagger = developing exporter
    gen flag_raw = type_raw
    replace flag_raw = flag_raw + "*" if sanctioned
    replace flag_raw = flag_raw + uchar(8224) if developing ///
        & inlist(type_raw, "EE", "IE")

    gen flag_cr = type_cr
    replace flag_cr = flag_cr + "*" if sanctioned
    replace flag_cr = flag_cr + uchar(8224) if developing ///
        & inlist(type_cr, "EE", "IE")

    gen flag_bilat = type_bilat
    replace flag_bilat = flag_bilat + "*" if sanctioned
    replace flag_bilat = flag_bilat + uchar(8224) if developing ///
        & inlist(type_bilat, "EE", "IE")
}

* ---- Step E: Write Table 3 to Excel ----
quietly {
    putexcel set "$root/Output/Table3_country_rankings.xlsx", replace

    * Row 1: group headers
    putexcel A1 = "(1) Raw Electricity"
    putexcel D1 = "(2) Cost-Recovery"
    putexcel G1 = "(3) Bilateral"
    putexcel A1:C1, bold
    putexcel D1:F1, bold
    putexcel G1:I1, bold

    * Row 2: sub-headers
    putexcel A2 = "Country" B2 = "Price" C2 = "Type"
    putexcel D2 = "Country" E2 = "Price" F2 = "Type"
    putexcel G2 = "Country" H2 = "Price" I2 = "Type"
    putexcel A2:I2, bold

    * (1) Raw: top 25
    gsort c_j_raw
    forvalues i = 1/25 {
        local r = `i' + 2
        putexcel A`r' = country[`i']
        putexcel B`r' = c_j_raw[`i'], nformat(#0.00)
        putexcel C`r' = flag_raw[`i']
    }

    * (2) Cost-Recovery: top 25
    gsort c_j_cr
    forvalues i = 1/25 {
        local r = `i' + 2
        putexcel D`r' = country[`i']
        putexcel E`r' = c_j_cr[`i'], nformat(#0.00)
        putexcel F`r' = flag_cr[`i']
    }

    * (3) Bilateral: top 25 by delivered price to USA
    gsort p_bilat_usa
    forvalues i = 1/25 {
        local r = `i' + 2
        putexcel G`r' = country[`i']
        putexcel H`r' = p_bilat_usa[`i'], nformat(#0.00)
        putexcel I`r' = flag_bilat[`i']
    }
}
display "Table 3 saved."


* --------------------------------------------------------------------------
* TABLE A1: Country-specific calibration parameters (all 85 countries)
* --------------------------------------------------------------------------
quietly {
    putexcel set "$root/Output/TableA1_calibration_parameters.xlsx", replace

    putexcel A1 = "Country" B1 = "p_E ($/kWh)" C1 = "Theta (C)" ///
             D1 = "PUE" E1 = "Constr. ($/W)" F1 = "k_bar (MW)" ///
             G1 = "omega (%)" H1 = "c_j ($/hr)" I1 = "Cost-Rec. p_E ($/kWh)"
    putexcel A1:I1, bold

    gsort rank_cr
    forvalues i = 1/`=_N' {
        local r = `i' + 1
        putexcel A`r' = country[`i']
        putexcel B`r' = p_E[`i'], nformat(#0.000)
        putexcel C`r' = theta[`i'], nformat(#0.0)
        putexcel D`r' = pue[`i'], nformat(#0.00)
        putexcel E`r' = p_L[`i'], nformat(#0.00)
        putexcel F`r' = dc_cap_mw[`i'], nformat(#,##0)
        local om = omega[`i'] * 100
        putexcel G`r' = `om', nformat(#0.0)
        putexcel H`r' = c_j_cr[`i'], nformat(#0.00)
        putexcel I`r' = p_E_cr[`i'], nformat(#0.000)
    }
}
display "Table A1 saved."


* --------------------------------------------------------------------------
* TABLE A2: Complete country rankings (all countries, 8 columns)
* --------------------------------------------------------------------------
quietly {
    putexcel set "$root/Output/TableA2_complete_rankings.xlsx", replace

    * Row 1: group headers
    putexcel A1 = ""
    putexcel B1 = "(1) Raw Electricity"
    putexcel E1 = "(2) Cost-Recovery"
    putexcel H1 = "(3) Bilateral"
    putexcel B1:D1, bold
    putexcel E1:G1, bold
    putexcel H1, bold

    * Row 2: sub-headers
    putexcel A2 = "Country" B2 = "c_j" C2 = "Rank" D2 = "Type"
    putexcel E2 = "c_j" F2 = "Rank" G2 = "Type" H2 = "Type"
    putexcel A2:H2, bold

    * Data: sorted by cost-recovery rank
    gsort rank_cr
    forvalues i = 1/`=_N' {
        local r = `i' + 2
        putexcel A`r' = country[`i']
        putexcel B`r' = c_j_raw[`i'], nformat(#0.00)
        putexcel C`r' = rank_raw[`i']
        putexcel D`r' = flag_raw[`i']
        putexcel E`r' = c_j_cr[`i'], nformat(#0.00)
        putexcel F`r' = rank_cr[`i']
        putexcel G`r' = flag_cr[`i']
        putexcel H`r' = flag_bilat[`i']
    }
}
display "Table A2 saved."

display _newline "All tables saved to $root/Output/"

* Clean up table-only variables
capture drop type_raw type_cr type_bilat flag_raw flag_cr flag_bilat
capture drop is_inf_exp_raw is_inf_exp_bilat inf_source_bilat is_dom_inf_bilat


* ══════════════════════════════════════════════════════════════════════════════
* 14. SAVE
* ══════════════════════════════════════════════════════════════════════════════

order iso3 country rank_raw rank_cr delta_rank c_j_raw c_j_cr ///
    p_E p_E_cr pue_calc theta c_elec c_elec_cr c_hardware c_network ///
    c_construct dc_cap_mw omega k_bar bloc sanctioned ///
    is_exporter_0 export_pct_0 is_exporter_b export_pct_b ///
    inf_source P_I_best P_I_domestic imports_inf ///
    lambda_min_k lambda_star_k lambda_usa p_bilat_usa ///
    regime is_dom_train is_dom_inf welfare_train_k welfare_inf_k

gsort rank_cr
save "$out/country_results.dta", replace
export delimited "$out/country_results.csv", replace

display _newline "Results saved to $out/"
display "Done."
