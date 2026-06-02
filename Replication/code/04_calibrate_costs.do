/*==============================================================================
  04_calibrate_costs.do — Compute c_j for each country

  Merges electricity, temperature, and construction cost data.
  Computes:
    PUE_j   = PUE_BASE + PUE_SLOPE * max(0, theta_j - THETA_REF)
    c_elec  = PUE_j * GPU_TDP_KW * p_E_j
    c_hw    = R_HARDWARE  (rho)
    c_constr= GPU_TDP_W * p_L_j / (DC_LIFE_YR * H_YR)
    c_j     = c_elec + c_hw + c_constr

  Validates against Python output (calibration_results_v3.csv).
==============================================================================*/

clear
set type double

// ─── Merge three input datasets ──────────────────────────────────────────────
use "$temp/electricity_prices.dta", clear

merge 1:1 iso3 using "$temp/temperatures.dta", keep(match) nogen
merge 1:1 iso3 using "$temp/construction_costs.dta", keep(match) nogen

qui count
di as txt "  Calibration set: " r(N) " countries (intersection of 3 datasets)"

// ─── Compute cost components ─────────────────────────────────────────────────

// PUE
gen double pue = $PUE_BASE + $PUE_SLOPE * max(0, theta_summer - $THETA_REF)

// Electricity cost component
gen double c_elec = pue * $GPU_TDP_KW * p_E

// Hardware cost (constant across countries)
gen double c_hw = $R_HARDWARE

// Construction cost component
// p_L is $/W, GPU_TDP_W is watts, amortized over DC_LIFE_YR * H_YR hours
gen double c_constr = $GPU_TDP_W * p_L / ($DC_LIFE_YR * $H_YR)

// Total cost per GPU-hour
gen double c_j_total = c_elec + c_hw + c_constr

// ─── Rank ────────────────────────────────────────────────────────────────────
gsort c_j_total
gen int rank = _n

// ─── Display top 20 ─────────────────────────────────────────────────────────
di as txt _n "Top 20 countries by c_j:"
di as txt "{hline 80}"
di as txt %4s "Rank" " " %5s "ISO3" " " %-24s "Country" " " ///
          %8s "c_j" " " %8s "Elec" " " %8s "Constr" " " %5s "PUE" " " %7s "p_E"
di as txt "{hline 80}"

forvalues i = 1/20 {
    di as txt %4.0f rank[`i'] " " %5s iso3[`i'] " " %-24s country[`i'] " " ///
        "$" %7.4f c_j_total[`i'] " $" %7.4f c_elec[`i'] " $" %7.4f c_constr[`i'] ///
        " " %5.2f pue[`i'] " $" %6.4f p_E[`i']
}

// ─── Validate against Python output ──────────────────────────────────────────
di as txt _n "Validating against Python output..."

preserve

// Load Python results
tempfile python_results
import delimited "$data/calibration_results_v3.csv", ///
    varnames(1) encoding("utf-8") clear
keep iso3 c_j_total
rename c_j_total c_j_python
save `python_results'

restore

// Merge and compare
merge 1:1 iso3 using `python_results', keep(match) nogen

gen double abs_diff = abs(c_j_total - c_j_python)
qui sum abs_diff
local max_diff = r(max)
local mean_diff = r(mean)

di as txt "  Matched: " r(N) " countries"
di as txt "  Max absolute difference in c_j: " %12.8f `max_diff'
di as txt "  Mean absolute difference in c_j: " %12.8f `mean_diff'

if `max_diff' < 0.0001 {
    di as res "  VALIDATION PASSED: max diff < 0.0001"
}
else {
    di as err "  VALIDATION WARNING: max diff >= 0.0001"
}

drop c_j_python abs_diff

// ─── Save ────────────────────────────────────────────────────────────────────
order rank iso3 country c_j_total c_elec c_hw c_constr pue p_E theta_summer p_L cost_source
compress
save "$temp/calibration_results.dta", replace

// Also export CSV for reference
export delimited "$output/calibration_results_stata.csv", replace

di as txt "  Saved: calibration_results.dta (" r(N) " countries)"
