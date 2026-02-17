/*==============================================================================
  01_prep_electricity.do — Load electricity prices + hardcoded additions

  Reads country_electricity_prices.csv, appends 25 additional countries with
  hardcoded industrial electricity prices, saves electricity_prices.dta.
==============================================================================*/

clear
set type double

// ─── Load CSV ────────────────────────────────────────────────────────────────
import delimited "$data/country_electricity_prices.csv", ///
    varnames(1) encoding("utf-8") clear

keep iso3 price_usd_kwh source
rename price_usd_kwh p_E
rename source elec_source

tempfile base
save `base'

// ─── Additional countries (industrial electricity prices) ────────────────────
// Only added if not already in the CSV
clear
input str3 iso3 double p_E str60 elec_source
"SAU" 0.053 "Climatescope/BloombergNEF 2025, industrial 2024"
"KEN" 0.088 "Climatescope/BloombergNEF 2025, industrial 2024"
"MAR" 0.108 "Climatescope/BloombergNEF 2025, industrial 2024"
"MYS" 0.099 "Climatescope/BloombergNEF 2025, industrial 2024"
"IDN" 0.067 "Climatescope/BloombergNEF 2025, industrial 2024"
"ZAF" 0.040 "Climatescope/BloombergNEF 2025, Eskom Megaflex avg"
"MEX" 0.095 "Climatescope/BloombergNEF 2025, industrial 2024"
"CHL" 0.130 "Statista/Climatescope 2025, industrial Jan 2024"
"THA" 0.108 "Climatescope/BloombergNEF 2025, industrial 2024"
"EGY" 0.038 "Climatescope/BloombergNEF 2025, industrial 2024"
"NGA" 0.042 "Climatescope/BloombergNEF 2025, weighted avg industrial"
"PAK" 0.134 "Climatescope/BloombergNEF 2025, industrial 2024"
"ARG" 0.060 "CAMMESA Argentina 2024, large industrial avg"
"COL" 0.075 "XM Colombia 2024, industrial non-regulated"
"NZL" 0.095 "MBIE New Zealand 2024, industrial avg"
"ISR" 0.108 "IEC Israel 2024, general industrial TOU"
"VNM" 0.073 "EVN Vietnam 2024, industrial peak/off-peak avg"
"PHL" 0.115 "MERALCO Philippines 2024, industrial"
"IRN" 0.005 "TAVANIR Iran 2024, heavily subsidized industrial"
"DZA" 0.033 "Sonelgaz Algeria 2024, subsidized industrial"
"QAT" 0.036 "Kahramaa Qatar 2024, industrial tariff"
"TWN" 0.094 "Taipower Taiwan 2024, industrial avg"
"ETH" 0.030 "EEU Ethiopia 2024, industrial tariff, hydro-dominated"
"GHA" 0.120 "ECG Ghana 2024, industrial tariff"
"SEN" 0.180 "Senelec Senegal 2024, industrial tariff"
end

tempfile additional
save `additional'

// ─── Merge: keep base where it exists, add new countries ─────────────────────
use `base', clear

// Anti-join: find additional countries not in base
merge 1:1 iso3 using `additional', keep(master using) nogen

// Count
qui count
di as txt "  Electricity prices: " r(N) " countries"

// Save
compress
save "$temp/electricity_prices.dta", replace
