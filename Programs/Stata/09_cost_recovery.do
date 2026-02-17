/*==============================================================================
  09_cost_recovery.do — Apply subsidy adjustments, recompute costs and
                         re-run capacity-constrained equilibrium

  Replaces subsidized electricity prices for 13 countries with cost-reflective
  LRMC estimates (from SUBSIDY_ADJ globals), recomputes c_j, rebuilds the
  supply stack, and re-runs the iterative solver.
  Saves cost_recovery.dta.
==============================================================================*/

clear
set type double

// ─── Load capacity equilibrium data ──────────────────────────────────────────
use "$temp/capacity_equilibrium.dta", clear

// Keep the calibration primitives we need
merge 1:1 iso3 using "$temp/calibration_results.dta", ///
    keepusing(p_E pue theta_summer) keep(match) nogen

// ─── Apply cost-recovery adjustments ─────────────────────────────────────────
// Parse the paired SUBSIDY_ISO / SUBSIDY_PRC globals
gen double p_E_adj = p_E
gen byte   is_adjusted = 0
gen double c_j_orig = c_j
gen str40  adj_note = ""

local n_sub : word count $SUBSIDY_ISO
forvalues s = 1/`n_sub' {
    local iso : word `s' of $SUBSIDY_ISO
    local prc : word `s' of $SUBSIDY_PRC

    qui count if iso3 == "`iso'"
    if r(N) > 0 {
        // Compute the electricity cost delta
        // delta_elec = PUE * GAMMA * (p_E_adj - p_E_orig)
        qui replace p_E_adj = `prc' if iso3 == "`iso'"
        qui replace is_adjusted = 1 if iso3 == "`iso'"
        qui replace adj_note = "LRMC: `prc' $/kWh" if iso3 == "`iso'"
    }
}

// Recompute c_j with adjusted electricity prices
gen double delta_elec = pue * $GAMMA * (p_E_adj - p_E)
gen double c_j_adj = c_j + delta_elec
replace c_j = c_j_adj

// ─── Display adjustments ────────────────────────────────────────────────────
di as txt _n "Cost-recovery adjustments applied:"
di as txt "{hline 70}"

preserve
keep if is_adjusted == 1
sort iso3
forvalues i = 1/`=_N' {
    di as txt "  " iso3[`i'] " (" country[`i'] "): " ///
        "p_E " %6.3f p_E[`i'] " -> " %6.3f p_E_adj[`i'] ///
        "  c_j " %7.4f c_j_orig[`i'] " -> " %7.4f c_j[`i']
}
restore

qui count if is_adjusted == 1
di as txt _n "  Adjusted " r(N) " countries"

// ─── Rank under adjusted costs ───────────────────────────────────────────────
gsort c_j
gen int adj_rank = _n

di as txt _n "Top 5 (cost-recovery adjusted):"
forvalues i = 1/5 {
    local flag = ""
    if is_adjusted[`i'] == 1 local flag " *"
    di as txt "  " adj_rank[`i'] ". " iso3[`i'] " (" country[`i'] ")" ///
        " $" %7.4f c_j[`i'] "`flag'"
}

// ─── Re-run capacity equilibrium on adjusted costs ───────────────────────────
// Reset solver variables
cap drop exporter_share_lam0 shadow_value_lam0 is_exporter_lam0
cap drop exporter_share_sov shadow_value_sov is_exporter_sov
cap drop p_T_lambda0 p_T_sovereign lambda_star

di as txt _n "=== Re-computing equilibrium (cost-recovery, lambda=0) ==="

sort c_j
solve_equilibrium, lambda(0)

local p_T_cr     = r(p_T)
local n_exp_cr   = r(n_exporters)
local hhi_T_cr   = r(hhi_T)

gen double p_T_costrecovery = `p_T_cr'
gen double lambda_star_cr = c_j / `p_T_cr' - 1
rename exporter_share exporter_share_cr
rename shadow_value   shadow_value_cr
rename is_exporter    is_exporter_cr

di as txt _n "=== Re-computing equilibrium (cost-recovery, lambda=$LAMBDA) ==="

cap drop exporter_share shadow_value is_exporter
sort c_j
solve_equilibrium, lambda($LAMBDA)

local p_T_cr_sov   = r(p_T)
local n_exp_cr_sov = r(n_exporters)
local hhi_T_cr_sov = r(hhi_T)

rename exporter_share exporter_share_cr_sov
rename shadow_value   shadow_value_cr_sov
rename is_exporter    is_exporter_cr_sov

// ─── Summary ─────────────────────────────────────────────────────────────────
di as txt _n "=== Cost-Recovery Equilibrium Summary ==="
di as txt "  lambda=0:     p_T = $" %7.3f `p_T_cr' "/hr, " ///
    `n_exp_cr' " exporters, HHI = " %6.4f `hhi_T_cr'
di as txt "  lambda=" %4.2f $LAMBDA ": p_T = $" %7.3f `p_T_cr_sov' "/hr, " ///
    `n_exp_cr_sov' " exporters, HHI = " %6.4f `hhi_T_cr_sov'

// Verify top-5 ranking
gsort c_j
di as txt _n "  Top-5 ranking (should be KGZ, CAN, ETH, XKX, TJK):"
forvalues i = 1/5 {
    di as txt "    " `i' ". " iso3[`i']
}

// ─── Save ────────────────────────────────────────────────────────────────────
order iso3 country c_j c_j_orig c_j_adj adj_rank omega k_bar_j ///
      is_sanctioned is_adjusted p_E p_E_adj ///
      p_T_costrecovery lambda_star_cr ///
      exporter_share_cr shadow_value_cr is_exporter_cr ///
      exporter_share_cr_sov shadow_value_cr_sov is_exporter_cr_sov

compress
save "$temp/cost_recovery.dta", replace

// Store for downstream
global p_T_cr     = `p_T_cr'
global p_T_cr_sov = `p_T_cr_sov'
global hhi_T_cr   = `hhi_T_cr'
global hhi_T_cr_sov = `hhi_T_cr_sov'

di as txt "  Saved: cost_recovery.dta"
