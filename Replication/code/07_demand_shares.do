/*==============================================================================
  07_demand_shares.do — Compute demand shares (omega_k) and HHI

  Loads DC capacity estimates (MW), computes omega_k = MW_k / sum(MW),
  and Herfindahl-Hirschman Index for unconstrained training/inference.
  Saves demand_shares.dta.
==============================================================================*/

clear
set type double

// ─── Load DC capacity ────────────────────────────────────────────────────────
import delimited "$data/dc_capacity_estimates.csv", ///
    varnames(1) encoding("utf-8") clear

keep iso3 country capacity_mw n_datacenters source
rename source dc_source

tempfile dc_raw
save `dc_raw'

// ─── Merge with calibration set ──────────────────────────────────────────────
use "$temp/calibration_results.dta", clear
keep iso3 country c_j_total

merge 1:1 iso3 using `dc_raw', keep(master match)

// Countries without DC data: assign minimum 5 MW
replace capacity_mw = 5.0 if missing(capacity_mw)
replace dc_source = "minimum default" if missing(dc_source)
drop _merge

// ─── Compute omega ───────────────────────────────────────────────────────────
qui sum capacity_mw
local total_mw = r(sum)

gen double omega = capacity_mw / `total_mw'

// Verify omega sums to 1
qui sum omega
assert abs(r(sum) - 1) < 0.0001

// ─── Top demand centers ──────────────────────────────────────────────────────
gsort -omega
di as txt _n "Top 10 demand centers (by MW capacity share):"
di as txt "{hline 60}"
forvalues i = 1/10 {
    di as txt %5s iso3[`i'] " " %-24s country[`i'] " " ///
        %8.1f capacity_mw[`i'] " MW  omega=" %6.3f omega[`i'] ///
        " (" %5.1f omega[`i']*100 "%)"
}

// Compute cumulative share for top 5
local top5_share = 0
forvalues i = 1/5 {
    local top5_share = `top5_share' + omega[`i']
}
di as txt _n "Top 5 share: " %5.1f `top5_share'*100 "%"

// ─── HHI for demand ──────────────────────────────────────────────────────────
gen double omega_sq = omega^2
qui sum omega_sq
local hhi_demand = r(sum)
di as txt "HHI (demand concentration): " %6.4f `hhi_demand'
drop omega_sq

// ─── Save ────────────────────────────────────────────────────────────────────
order iso3 country capacity_mw omega c_j_total
compress
save "$temp/demand_shares.dta", replace

di as txt "  Saved: demand_shares.dta (" _N " countries)"
