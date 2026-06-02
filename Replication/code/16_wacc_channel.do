/*==============================================================================
  16_wacc_channel.do — Host-country WACC channel (Table 3 col (4))

  Reimplements the WACC channel from add_calibration_v33.py.

  Hardware amortization is re-derived at each country's income-group weighted
  average cost of capital using a capital-recovery factor (annuity), instead of
  the common 8% baseline. Built on the symmetric-LRMC electricity cost (col (2)
  is "CR + host WACC").

    WACC bands (WB FY2025):  HIC 8%, UMIC 12%, LMIC 15%, LIC 18%
    CRF(r,N) = r / (1 - (1+r)^-N)
    rho_hw(iso) = GPU_PRICE * CRF(wacc, GPU_LIFE) / (H_YR * GPU_UTIL)
    c_j_wacc = c_elec(symmetric) + rho_hw(iso) + c_construction

  Reproduces the paper's figures: $1.58/hr at 8% (HIC), $1.87/hr at 18% (LIC),
  a $0.29 gap. Saves wacc_channel.dta.
==============================================================================*/

clear
set type double

// ── Income-group map (WB FY2025 bands), transcribed from INCOME_GROUP ─────────
input str3 iso3 str4 income_group
"AUS" "HIC"
"AUT" "HIC"
"BEL" "HIC"
"CAN" "HIC"
"CHE" "HIC"
"CHL" "HIC"
"CYP" "HIC"
"CZE" "HIC"
"DEU" "HIC"
"DNK" "HIC"
"ESP" "HIC"
"EST" "HIC"
"FIN" "HIC"
"FRA" "HIC"
"GBR" "HIC"
"GRC" "HIC"
"GRL" "HIC"
"HRV" "HIC"
"HUN" "HIC"
"IRL" "HIC"
"ISL" "HIC"
"ISR" "HIC"
"ITA" "HIC"
"JPN" "HIC"
"KOR" "HIC"
"LTU" "HIC"
"LUX" "HIC"
"LVA" "HIC"
"MLT" "HIC"
"NLD" "HIC"
"NOR" "HIC"
"NZL" "HIC"
"POL" "HIC"
"PRT" "HIC"
"ROU" "HIC"
"SGP" "HIC"
"SVK" "HIC"
"SVN" "HIC"
"SWE" "HIC"
"USA" "HIC"
"ARE" "HIC"
"QAT" "HIC"
"SAU" "HIC"
"ALB" "UMIC"
"ARG" "UMIC"
"ARM" "UMIC"
"AZE" "UMIC"
"BGR" "UMIC"
"BIH" "UMIC"
"BLR" "UMIC"
"BRA" "UMIC"
"CHN" "UMIC"
"COL" "UMIC"
"DZA" "UMIC"
"GEO" "UMIC"
"IDN" "UMIC"
"IRN" "UMIC"
"KAZ" "UMIC"
"MDA" "UMIC"
"MEX" "UMIC"
"MKD" "UMIC"
"MNE" "UMIC"
"MYS" "UMIC"
"RUS" "UMIC"
"SRB" "UMIC"
"THA" "UMIC"
"TKM" "UMIC"
"TUR" "UMIC"
"UKR" "UMIC"
"XKX" "UMIC"
"ZAF" "UMIC"
"EGY" "LMIC"
"GHA" "LMIC"
"IND" "LMIC"
"KEN" "LMIC"
"KGZ" "LMIC"
"MAR" "LMIC"
"NGA" "LMIC"
"PAK" "LMIC"
"PHL" "LMIC"
"SEN" "LMIC"
"TJK" "LMIC"
"UZB" "LMIC"
"VNM" "LMIC"
"ETH" "LIC"
end
tempfile incgrp
save `incgrp'

// ── Symmetric-LRMC cost components (electricity + construction) ───────────────
use "$temp/symmetric_lrmc.dta", clear
keep iso3 country c_elec c_const c_j
rename c_j c_j_symmetric
merge 1:1 iso3 using `incgrp', keep(master match) nogen
replace income_group = "HIC" if missing(income_group)

// ── WACC band + capital-recovery-factor hardware amortization ─────────────────
gen double wacc = .
replace wacc = 0.08 if income_group == "HIC"
replace wacc = 0.12 if income_group == "UMIC"
replace wacc = 0.15 if income_group == "LMIC"
replace wacc = 0.18 if income_group == "LIC"

// CRF(r,N) = r / (1 - (1+r)^-N);  rho = GPU_PRICE * CRF / (H_YR * GPU_UTIL)
gen double crf      = wacc / (1 - (1 + wacc)^(-$GPU_LIFE_YR))
gen double rho_wacc = $GPU_PRICE * crf / ($H_YR * $GPU_UTIL)

// c_j under WACC = symmetric electricity + WACC-amortized hardware + construction
gen double c_j_wacc = c_elec + rho_wacc + c_const

gsort c_j_wacc
gen int rank_wacc = _n

// ── Headline checks: $1.58/hr @8%, $1.87/hr @18%, $0.29 gap ───────────────────
qui sum rho_wacc if income_group == "HIC"
local rho_hic = r(mean)
qui sum rho_wacc if income_group == "LIC"
local rho_lic = r(mean)
di as txt _n "=== WACC channel: hardware amortization by income group ==="
di as txt "  HIC (8%):  rho_hw = $" %5.3f `rho_hic' "/hr"
di as txt "  LIC (18%): rho_hw = $" %5.3f `rho_lic' "/hr"
di as txt "  Gap = $" %5.3f `rho_lic' - `rho_hic' "/hr  (paper: ~$0.29)"

di as txt _n "  Top-10 under CR + host WACC (col 4):"
forvalues i = 1/10 {
    di as txt "  " %2.0f rank_wacc[`i'] ". " iso3[`i'] " (" country[`i'] ")" ///
        "  c_j = $" %6.4f c_j_wacc[`i'] "  [" income_group[`i'] "]"
}

compress
save "$temp/wacc_channel.dta", replace
di as txt "  Saved: wacc_channel.dta"
