/*==============================================================================
  03_prep_construction.do — Load and prepare construction costs

  Reads predicted_construction_costs.csv. Uses actual_usd_per_watt if
  available (DCCI), otherwise uses predicted_usd_per_watt.
  Saves construction_costs.dta.
==============================================================================*/

clear
set type double

import delimited "$data/predicted_construction_costs.csv", ///
    varnames(1) encoding("utf-8") clear

// Use actual if available, otherwise predicted
gen double p_L = .
gen str10 cost_source = ""

// actual_usd_per_watt may be imported as string due to missing values
cap confirm string variable actual_usd_per_watt
if _rc == 0 {
    // It's a string — destring it
    destring actual_usd_per_watt, replace force
}
cap confirm string variable predicted_usd_per_watt
if _rc == 0 {
    destring predicted_usd_per_watt, replace force
}

replace p_L = actual_usd_per_watt if !missing(actual_usd_per_watt)
replace cost_source = "DCCI" if !missing(actual_usd_per_watt)

replace p_L = predicted_usd_per_watt if missing(p_L) & !missing(predicted_usd_per_watt)
replace cost_source = "predicted" if missing(cost_source) | cost_source == ""

// Drop observations where both are missing
drop if missing(p_L)

keep iso3 p_L cost_source

qui count
di as txt "  Construction costs: " r(N) " countries"

compress
save "$temp/construction_costs.dta", replace
