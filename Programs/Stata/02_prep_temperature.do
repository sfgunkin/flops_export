/*==============================================================================
  02_prep_temperature.do — Load country temperatures

  Reads country_temperatures.csv, keeps iso3, country name, and summer peak
  temperature, saves temperatures.dta.
==============================================================================*/

clear
set type double

import delimited "$data/country_temperatures.csv", ///
    varnames(1) encoding("utf-8") clear

keep iso3 country temp_summer_peak_c
rename temp_summer_peak_c theta_summer

qui count
di as txt "  Temperatures: " r(N) " countries"

compress
save "$temp/temperatures.dta", replace
