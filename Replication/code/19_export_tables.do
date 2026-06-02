/*==============================================================================
  19_export_tables.do — Export every paper table to output/ as CSV

  Assembles the paper's tables from the pipeline's intermediate datasets:
    Table 1  regime taxonomy            (static/definitional)
    Table 2  model parameters           (from run_all.do globals)
    Table 3  rankings, key specs        (raw / symmetric-LRMC / bilateral / WACC)
    Table A1 calibration parameters     (all 85 countries)
    Table A2 rankings, all countries
    Table A3 sensitivity                (step 12)
    Table A4 facility specification     (static DCF inputs)
    Table A5 DCF cash flow              (step 14)
    Table A6 DCF return sensitivity     (step 14)
    Table A7 construction regression    (step 18, exported there)
    Table A8 workload classification    (static)

  Files: output/table{1,2,3,A1,A2,A4,A8}_*.csv  plus the .dta-derived A3/A5/A6.
==============================================================================*/

set type double

// ══════════════════════════════════════════════════════════════════════════════
// Table 1 — Regime taxonomy (definitional)
// ══════════════════════════════════════════════════════════════════════════════
clear
input str4 code str40 training str40 inference
"EE" "Exporter" "Exporter"
"IE" "Importer" "Exporter (hub)"
"ID" "Importer" "Domestic"
"DD" "Domestic" "Domestic"
"II" "Importer" "Importer"
end
export delimited using "$output/table1_regime_taxonomy.csv", replace

// ══════════════════════════════════════════════════════════════════════════════
// Table 2 — Model parameters (from globals)
// ══════════════════════════════════════════════════════════════════════════════
clear
input str28 parameter str12 symbol str16 value str30 source
"GPU power draw"          "gamma"   "0.700 kW"      "NVIDIA H100"
"GPU price"               "P_GPU"   "$25,000"       "Street price 2024"
"GPU lifetime"            "L"       "3 years"       "Barroso et al. 2018"
"Utilization rate"        "beta"    "0.70"          "Industry"
"Networking cost"         "eta"     "$0.15/hr"      "Assumption"
"PUE base"                "phi"     "1.08"          "Google 2024"
"PUE slope"               "delta"   "0.015/C"       "Calibration"
"PUE ref temp"            "thetabar" "15 C"         "Free-cooling threshold"
"DC lifetime"             "D"       "15 years"      "Industry"
"Latency degradation"     "tau"     "0.0008/ms"     "Deloitte 2025"
"Training share"          "alpha"   "0.50"          "Deloitte 2025"
"Total demand"            "Q"       "60B GPU-hr"    "Calibration"
"Geo premium weight"      "w1"      "0.05"          "Calibration"
"Reg premium weight"      "w2"      "0.025"         "Calibration"
"Uniform premium"         "lambda"  "0.10"          "Robustness"
end
export delimited using "$output/table2_model_parameters.csv", replace

// ══════════════════════════════════════════════════════════════════════════════
// Table A4 — Kyrgyzstan facility specification (static DCF inputs)
// ══════════════════════════════════════════════════════════════════════════════
clear
set obs 10
gen str28 parameter = ""
gen str20 value = ""
replace parameter = "IT capacity"            in 1
replace value     = "40 MW"                  in 1
replace parameter = "PUE"                    in 2
replace value     = "1.08"                   in 2
replace parameter = "Number of GPUs"         in 3
replace value     = "57,142"                 in 3
replace parameter = "Electricity price"      in 4
replace value     = "$0.038/kWh"             in 4
replace parameter = "Construction cost"      in 5
replace value     = "$7.83/W"                in 5
replace parameter = "Staff"                  in 6
replace value     = "50 @ $12,000/yr"        in 6
replace parameter = "Revenue per GPU-hr"     in 7
replace value     = "$2.00"                  in 7
replace parameter = "WACC"                   in 8
replace value     = "12.6%"                  in 8
replace parameter = "Tax rate"               in 9
replace value     = "10%"                    in 9
replace parameter = "Connectivity"           in 10
replace value     = "$2.4M/yr (100 Gbps)"    in 10
export delimited using "$output/tableA4_facility_spec.csv", replace

// ══════════════════════════════════════════════════════════════════════════════
// Table A8 — Workload classification (definitional)
// ══════════════════════════════════════════════════════════════════════════════
clear
input str22 workload str26 example str18 latency str14 offshorable str16 treatment
"Model training"      "GPT-class pretraining"   "None"        "Yes"      "Training (T)"
"Fine-tuning"         "Domain adaptation"       "None"        "Yes"      "Training (T)"
"Batch inference"     "Bulk embeddings"         "Seconds"     "Yes"      "Training (T)"
"Interactive chat"    "Chatbot response"        "<300 ms"     "Regional" "Inference (I)"
"Real-time agents"    "Autonomous decisions"    "<100 ms"     "Local"    "Inference (I)"
"Edge inference"      "On-device models"        "<10 ms"      "No"       "Inference (I)"
end
export delimited using "$output/tableA8_workload_classification.csv", replace

// ══════════════════════════════════════════════════════════════════════════════
// Table A1 — Country-specific calibration parameters (all 85)
// ══════════════════════════════════════════════════════════════════════════════
import delimited "$data/calibration_results_v3.csv", varnames(1) encoding("utf-8") clear
keep iso3 country p_e_usd_kwh theta_summer_c pue c_j_construction c_j_total
rename p_e_usd_kwh p_E
rename theta_summer_c theta
rename c_j_construction c_construction
merge 1:1 iso3 using "$temp/demand_shares.dta", keepusing(omega) keep(master match) nogen
preserve
import delimited "$data/grid_capacity_estimates.csv", varnames(1) encoding("utf-8") clear
keep iso3 k_bar_gpu_hours
tempfile kb
save `kb'
restore
merge 1:1 iso3 using `kb', keep(master match) nogen
gen double omega_pct = omega * 100
gsort c_j_total
order iso3 country p_E theta pue c_construction k_bar_gpu_hours omega_pct c_j_total
export delimited using "$output/tableA1_calibration_parameters.csv", replace

// ══════════════════════════════════════════════════════════════════════════════
// Table 3 / A2 — Country rankings under alternative specs
//   (1) Raw electricity | (2) Symmetric LRMC | (3) Bilateral | (4) CR+WACC
// ══════════════════════════════════════════════════════════════════════════════
// Raw (observed-price) ranking from calibration
import delimited "$data/calibration_results_v3.csv", varnames(1) encoding("utf-8") clear
keep iso3 country c_j_total
rename c_j_total c_j_raw
gsort c_j_raw
gen int rank_raw = _n
tempfile raw
save `raw'

use "$temp/symmetric_lrmc.dta", clear
keep iso3 c_j rank_symmetric
rename c_j c_j_symmetric
tempfile sym
save `sym'

use "$temp/wacc_channel.dta", clear
keep iso3 c_j_wacc rank_wacc income_group
tempfile wacc
save `wacc'

use "$temp/bilateral_lambda.dta", clear
keep iso3 regime_bilat best_train_src imports_train
tempfile bilat
save `bilat'

use `raw', clear
merge 1:1 iso3 using `sym',   keep(master match) nogen
merge 1:1 iso3 using `wacc',  keep(master match) nogen
merge 1:1 iso3 using `bilat', keep(master match) nogen
gsort rank_symmetric
order iso3 country c_j_raw rank_raw c_j_symmetric rank_symmetric ///
      c_j_wacc rank_wacc income_group regime_bilat best_train_src

// Table A2: all countries
export delimited using "$output/tableA2_rankings_all.csv", replace
// Table 3: top 25 (paper shows a 25-country excerpt)
preserve
keep if rank_symmetric <= 25
export delimited using "$output/table3_rankings_top25.csv", replace
restore

// ══════════════════════════════════════════════════════════════════════════════
// Tables A3 / A5 / A6 — from saved .dta results
// ══════════════════════════════════════════════════════════════════════════════
use "$output/sensitivity_results.dta", clear
export delimited using "$output/tableA3_sensitivity.csv", replace

use "$output/kyrgyzstan_dcf.dta", clear
export delimited using "$output/tableA5_dcf_cashflow.csv", replace

use "$output/kyrgyzstan_dcf_sensitivity.dta", clear
export delimited using "$output/tableA6_dcf_sensitivity.csv", replace

di as txt _n "{hline 70}"
di as txt "Exported paper tables to: $output"
di as txt "  table1_regime_taxonomy.csv         (Table 1)"
di as txt "  table2_model_parameters.csv        (Table 2)"
di as txt "  table3_rankings_top25.csv          (Table 3)"
di as txt "  tableA1_calibration_parameters.csv (Table A1)"
di as txt "  tableA2_rankings_all.csv           (Table A2)"
di as txt "  tableA3_sensitivity.csv            (Table A3)"
di as txt "  tableA4_facility_spec.csv          (Table A4)"
di as txt "  tableA5_dcf_cashflow.csv           (Table A5)"
di as txt "  tableA6_dcf_sensitivity.csv        (Table A6)"
di as txt "  tableA7_construction_regression.csv(Table A7)"
di as txt "  tableA8_workload_classification.csv(Table A8)"
di as txt "{hline 70}"
