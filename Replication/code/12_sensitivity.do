/*==============================================================================
  12_sensitivity.do — Sensitivity analysis: 6 parameter scenarios

  Runs 6 scenarios (baseline + 5 perturbations), for each:
    - Recomputes c_j with parameter overrides
    - Rebuilds supply stack, solves equilibrium
    - Computes Spearman rank correlation vs baseline
  Saves sensitivity_results.dta.
==============================================================================*/

clear
set type double

// ─── Load calibration data ───────────────────────────────────────────────────
use "$temp/calibration_results.dta", clear
keep iso3 country p_E theta_summer pue c_j_total c_constr

// Merge omega and k_bar
merge 1:1 iso3 using "$temp/demand_shares.dta", ///
    keepusing(omega capacity_mw) keep(match) nogen

tempfile kbar
preserve
import delimited "$data/grid_capacity_estimates.csv", ///
    varnames(1) encoding("utf-8") clear
keep iso3 k_bar_gpu_hours
gen double k_bar_j = k_bar_gpu_hours * $K_BAR_SCALE
keep iso3 k_bar_j
save `kbar'
restore

merge 1:1 iso3 using `kbar', keep(match) nogen

// Sanction flag
gen byte is_sanctioned = 0
foreach iso of global SANCTIONED {
    qui replace is_sanctioned = 1 if iso3 == "`iso'"
}

qui count
local N = _N
di as txt "  Sensitivity analysis: `N' countries"

// ─── Define scenarios ────────────────────────────────────────────────────────
// Each scenario modifies one parameter relative to cost-recovery baseline
// Format: label, p_E_delta, gpu_price, pue_cap (. = no change)

local n_scen = 6
local lab1 "Baseline calibration"
local dpe1 = 0
local gprc1 = .
local pcap1 = .

local lab2 "Electricity price +$0.01/kWh"
local dpe2 = 0.01
local gprc2 = .
local pcap2 = .

local lab3 "Electricity price -$0.01/kWh"
local dpe3 = -0.01
local gprc3 = .
local pcap3 = .

local lab4 "GPU hardware cost +20% ($30,000)"
local dpe4 = 0
local gprc4 = 30000
local pcap4 = .

local lab5 "GPU hardware cost -20% ($20,000)"
local dpe5 = 0
local gprc5 = 20000
local pcap5 = .

local lab6 "Cooling efficiency cap (PUE<=1.20)"
local dpe6 = 0
local gprc6 = .
local pcap6 = 1.20

// ─── Run scenarios ───────────────────────────────────────────────────────────
// We need to store baseline ranking for Spearman correlation

tempfile scenario_summary
postfile sumhandle int scenario str60 label ///
    double(p_T n_exporters hhi_T rank_corr) ///
    str3(top1 top2 top3 top4 top5) ///
    byte top5_unchanged ///
    using `scenario_summary'

// Store baseline ranks (will be filled in scenario 1)
tempvar base_rank
gen int `base_rank' = .

forvalues s = 1/`n_scen' {
    di as txt _n "--- Scenario `s': `lab`s'' ---"

    // Recompute costs
    local gp = $GPU_PRICE
    if `gprc`s'' != . local gp = `gprc`s''

    local gu = $GPU_UTIL
    local rho = `gp' / ($GPU_LIFE_YR * $H_YR * `gu')

    tempvar c_j_s
    gen double `c_j_s' = .

    forvalues i = 1/`N' {
        local pe = p_E[`i']
        // Apply subsidy adjustment
        local iso_i = iso3[`i']
        local n_sub : word count $SUBSIDY_ISO
        forvalues ss = 1/`n_sub' {
            local siso : word `ss' of $SUBSIDY_ISO
            local sprc : word `ss' of $SUBSIDY_PRC
            if "`iso_i'" == "`siso'" {
                local pe = `sprc'
            }
        }
        local pe = `pe' + `dpe`s''

        local th = theta_summer[`i']
        local pue_i = $PUE_BASE + $PUE_SLOPE * max(0, `th' - $THETA_REF)
        if `pcap`s'' != . {
            local pue_i = min(`pue_i', `pcap`s'')
        }

        local c_elec = `pue_i' * $GAMMA * `pe'
        local c_con = c_constr[`i']
        local c_tot = `c_elec' + `rho' + $ETA + `c_con'

        qui replace `c_j_s' = `c_tot' in `i'
    }

    // Rank
    tempvar rank_s
    egen int `rank_s' = rank(`c_j_s')

    // Top 5
    tempvar sorted_order
    egen int `sorted_order' = rank(`c_j_s')

    local top_1 ""
    local top_2 ""
    local top_3 ""
    local top_4 ""
    local top_5 ""
    forvalues i = 1/`N' {
        if `sorted_order'[`i'] == 1 local top_1 = iso3[`i']
        if `sorted_order'[`i'] == 2 local top_2 = iso3[`i']
        if `sorted_order'[`i'] == 3 local top_3 = iso3[`i']
        if `sorted_order'[`i'] == 4 local top_4 = iso3[`i']
        if `sorted_order'[`i'] == 5 local top_5 = iso3[`i']
    }

    // Run equilibrium solver (need to temporarily replace c_j)
    preserve
    replace c_j_total = `c_j_s'
    gen double c_j = `c_j_s'

    sort c_j
    solve_equilibrium, lambda(0)

    local pT_s = r(p_T)
    local nexp_s = r(n_exporters)
    local hhi_s = r(hhi_T)
    restore

    // Spearman rank correlation
    if `s' == 1 {
        // Store baseline ranking
        replace `base_rank' = `rank_s'
    }

    // Compute Spearman rho
    tempvar d_sq
    gen double `d_sq' = (`rank_s' - `base_rank')^2
    qui sum `d_sq'
    local sum_d_sq = r(sum)
    local n_r = `N'
    local spearman = 1 - 6 * `sum_d_sq' / (`n_r' * (`n_r'^2 - 1))
    drop `d_sq'

    // Top 5 unchanged?
    if `s' == 1 {
        local base_top1 "`top_1'"
        local base_top2 "`top_2'"
        local base_top3 "`top_3'"
        local base_top4 "`top_4'"
        local base_top5 "`top_5'"
    }

    local t5_same = ("`top_1'" == "`base_top1'" & ///
                     "`top_2'" == "`base_top2'" & ///
                     "`top_3'" == "`base_top3'" & ///
                     "`top_4'" == "`base_top4'" & ///
                     "`top_5'" == "`base_top5'")

    post sumhandle (`s') ("`lab`s''") ///
        (`pT_s') (`nexp_s') (`hhi_s') (`spearman') ///
        ("`top_1'") ("`top_2'") ("`top_3'") ("`top_4'") ("`top_5'") ///
        (`t5_same')

    di as txt "  p_T=$" %7.3f `pT_s' ", n_exp=`nexp_s', " ///
        "HHI=" %6.4f `hhi_s' ", rho=" %6.4f `spearman' ///
        ", top5=" cond(`t5_same', "same", "CHANGED")

    drop `c_j_s' `rank_s' `sorted_order'
}

postclose sumhandle

// ─── Display summary table ───────────────────────────────────────────────────
use `scenario_summary', clear

di as txt _n "=== Sensitivity Analysis Summary ==="
di as txt "{hline 80}"
di as txt %-40s "Scenario" " " %7s "p_T" " " %4s "N" " " ///
          %6s "HHI" " " %6s "rho" " " %5s "Top5"
di as txt "{hline 80}"

forvalues i = 1/`=_N' {
    di as txt %-40s label[`i'] " $" %6.3f p_T[`i'] " " ///
        %4.0f n_exporters[`i'] " " %6.4f hhi_T[`i'] " " ///
        %6.4f rank_corr[`i'] " " ///
        cond(top5_unchanged[`i'], "same", "CHANGED")
}

compress
save "$output/sensitivity_results.dta", replace

di as txt _n "  Saved: sensitivity_results.dta"
