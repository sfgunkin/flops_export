/*==============================================================================
  19_export_tables.do — Export every paper table to output/ as CSV

  Assembles the paper's tables from the pipeline's intermediate datasets and,
  for the ranking tables, from a paper-exact recomputation that transcribes
  the published generator (add_calibration_v33.py) constant-for-constant:
    Table 1  regime taxonomy            (static/definitional)
    Table 2  model parameters           (from run_all.do globals)
    Table 3  rankings, key specs        (raw / cost-recovery / bilateral / WACC)
    Table A1 calibration parameters     (all 85 countries)
    Table A2 rankings, all countries
    Table A3 sensitivity of cost-recovery rankings (rho variation)
    Table A4 facility specification     (static DCF inputs)
    Table A5 DCF cash flow              (step 14)
    Table A6 DCF return sensitivity     (step 14)
    Table A7 construction regression    (step 18, exported there)
    Table A8 workload classification    (static)

  Tables 3, A1, A2 and A3 print the exact cell strings of the published paper
  (same sorting, same units, same number formats, same regime-type letters),
  so each CSV can be compared against the corresponding paper exhibit 1:1.

  Sources for the transcribed constants (all from add_calibration_v33.py):
    SUBSIDY_ADJ (56 cost-recovery prices), INCOME_GROUP + WACC bands,
    SANCTIONED, DEVELOPING, geopolitical blocs, EU/APEC-CBPR/DEPA sets,
    bloc-distance matrix, ALPHA_GEO/ALPHA_REG, latency rule, and the
    capacity-constrained equilibrium algorithm.
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
// PAPER-EXACT RANKING TABLES (3, A1, A2, A3)
//
// Everything below mirrors add_calibration_v33.py. Cost formulas keep the same
// term order as the Python source so that floating-point results (and hence
// near-tie rankings) are bit-identical.
// ══════════════════════════════════════════════════════════════════════════════

// ─── Transcribed constant sets (membership tested via padded strpos) ─────────
// Sanctioned (6): comprehensive sanctions, excluded from export supply
local sanctioned6 "IRN RUS BLR PRK SYR TKM"
// Developing set (43): used for the dagger flag and Table A3 dev-top-15
local developing "CHN KGZ XKX MNE ETH VNM IND KEN ARE EGY DZA UZB TJK TKM ALB MKD GEO ARM MDA UKR BIH SRB IDN MYS PHL THA COL MEX BRA ARG CHL PER NGA ZAF MAR TUN SEN BGD PAK LKA MMR LAO KHM"
// Geopolitical blocs (UNGA voting, Bailey-Strezhnev-Voeten 2017)
local bloc_w "USA CAN GBR FRA DEU ITA ESP PRT NLD BEL LUX AUT CHE IRL DNK NOR SWE FIN ISL GRC CZE POL HUN SVK SVN EST LVA LTU HRV BGR ROU CYP MLT JPN KOR AUS NZL ISR TWN"
local bloc_c "CHN RUS BLR PRK SYR IRN VEN CUB NIC MMR"
// Regulatory-compatibility memberships
local eu27 "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE"
local apec_cbpr "AUS CAN JPN KOR MEX PHL SGP TWN USA"
local depa "SGP CHL NZL"
// Income groups for the WACC channel (WB FY2025); unmapped -> HIC
local g_umic "ALB ARG ARM AZE BGR BIH BLR BRA CHN COL DZA GEO IDN IRN KAZ MDA MEX MKD MNE MYS RUS SRB THA TKM TUR UKR XKX ZAF"
local g_lmic "EGY GHA IND KEN KGZ MAR NGA PAK PHL SEN TJK UZB VNM"
local g_lic  "ETH"

// Bilateral lambda weights
local ALPHA_GEO = 0.05
local ALPHA_REG = 0.025
// Latency / inference parameters
local TAU_  = 0.0008
local LBAR  = 200.0
local DOM_LAT = 5.0

// ─── SUBSIDY_ADJ: 56 cost-recovery electricity prices ($/kWh) ─────────────────
clear
input str3 iso3 double cr_pe
"IRN" 0.085
"TKM" 0.070
"DZA" 0.065
"EGY" 0.080
"UZB" 0.090
"QAT" 0.100
"SAU" 0.100
"ARE" 0.095
"RUS" 0.065
"KAZ" 0.085
"NGA" 0.080
"ZAF" 0.095
"ETH" 0.050
"AUS" 0.09000
"AUT" 0.16659
"BEL" 0.14655
"BGR" 0.18156
"CAN" 0.05260
"CHE" 0.16284
"CHL" 0.13000
"COL" 0.07500
"CYP" 0.22756
"CZE" 0.20280
"DEU" 0.22016
"DNK" 0.13888
"ESP" 0.13445
"EST" 0.16853
"FIN" 0.06171
"FRA" 0.12095
"GBR" 0.10656
"GRC" 0.19145
"HRV" 0.21776
"HUN" 0.19222
"IRL" 0.24928
"ISL" 0.09198
"ISR" 0.10800
"ITA" 0.19044
"JPN" 0.13500
"KOR" 0.14500
"LTU" 0.14464
"LUX" 0.13267
"LVA" 0.12409
"MEX" 0.09500
"MLT" 0.13746
"NLD" 0.16372
"NOR" 0.05552
"NZL" 0.09935
"POL" 0.16562
"PRT" 0.11741
"ROU" 0.17414
"SGP" 0.15244
"SVK" 0.17291
"SVN" 0.16119
"SWE" 0.07104
"TUR" 0.08600
"USA" 0.09771
end
tempfile subsidy56
save `subsidy56'

// ─── Country-level base data ──────────────────────────────────────────────────
import delimited "$data/calibration_results_v3.csv", varnames(1) encoding("utf-8") clear
keep iso3 country p_e_usd_kwh theta_summer_c pue p_l_usd_per_w c_j_total
rename p_e_usd_kwh p_E
rename theta_summer_c theta
rename p_l_usd_per_w p_L
gen long csvorder = _n   // stable tie-break, mirrors Python dict/list order

merge 1:1 iso3 using `subsidy56', keep(master match) nogen
replace cr_pe = p_E if missing(cr_pe)
gen byte is_adjusted = !missing(cr_pe) & abs(cr_pe - p_E) > 1e-12
// Re-derive the adjusted flag the way Python does (membership, not value)
gen byte in_subsidy56 = 0
foreach iso in IRN TKM DZA EGY UZB QAT SAU ARE RUS KAZ NGA ZAF ETH AUS AUT BEL BGR CAN CHE CHL COL CYP CZE DEU DNK ESP EST FIN FRA GBR GRC HRV HUN IRL ISL ISR ITA JPN KOR LTU LUX LVA MEX MLT NLD NOR NZL POL PRT ROU SGP SVK SVN SWE TUR USA {
    qui replace in_subsidy56 = 1 if iso3 == "`iso'"
}
drop is_adjusted

// DC capacity (MW) -> demand shares omega and capacity ceilings k_bar
preserve
import delimited "$data/dc_capacity_estimates.csv", varnames(1) encoding("utf-8") clear
keep iso3 capacity_mw
tempfile dccap
save `dccap'
restore
merge 1:1 iso3 using `dccap', keep(master match) nogen
replace capacity_mw = 5.0 if missing(capacity_mw)   // minimum 5 MW if no data
qui sum capacity_mw
gen double omega = capacity_mw / r(sum)
// MW -> GPU-hours/yr: cap_mw * (1000/GAMMA) * H_YR * GPU_UTIL
gen double k_bar_j = capacity_mw * (1000 / 0.700) * (365.25 * 24) * 0.70

// Membership flags
gen byte is_sanct = strpos(" `sanctioned6' ", " " + iso3 + " ") > 0
gen byte is_dev   = strpos(" `developing' ",  " " + iso3 + " ") > 0
gen str1 bloc = "N"
replace bloc = "W" if strpos(" `bloc_w' ", " " + iso3 + " ") > 0
replace bloc = "C" if strpos(" `bloc_c' ", " " + iso3 + " ") > 0
gen byte in_eu   = strpos(" `eu27' ",      " " + iso3 + " ") > 0
gen byte in_apec = strpos(" `apec_cbpr' ", " " + iso3 + " ") > 0
gen byte in_depa = strpos(" `depa' ",      " " + iso3 + " ") > 0
gen str4 income_group = "HIC"
replace income_group = "UMIC" if strpos(" `g_umic' ", " " + iso3 + " ") > 0
replace income_group = "LMIC" if strpos(" `g_lmic' ", " " + iso3 + " ") > 0
replace income_group = "LIC"  if strpos(" `g_lic' ",  " " + iso3 + " ") > 0

// ─── Cost specifications (same term order as the Python source) ──────────────
// rho = GPU_PRICE / (GPU_LIFE * H_YR * GPU_UTIL)
local rho = 25000 / (3 * (365.25 * 24) * 0.70)
local eta = 0.15
gen double constr_cost = (p_L * 0.700 * 1000) / (15 * (365.25 * 24))
gen double elec_raw = 0.700 * p_E * pue
gen double elec_cr  = 0.700 * cr_pe * pue
gen double cj_raw  = elec_raw + `rho' + constr_cost + `eta'
gen double cj_cr   = elec_cr  + `rho' + constr_cost + `eta'
// WACC channel: rho_hw(WACC_j) via capital-recovery factor CRF(r,3)
gen double wacc_j = 0.08
replace wacc_j = 0.12 if income_group == "UMIC"
replace wacc_j = 0.15 if income_group == "LMIC"
replace wacc_j = 0.18 if income_group == "LIC"
gen double crf = wacc_j / (1 - (1 + wacc_j)^(-3))
gen double rho_wacc = 25000 * crf / (8766 * 0.70)
gen double cj_wacc = elec_cr + rho_wacc + constr_cost + `eta'

// Equilibrium cost vectors (Python uses CSV c_j_total + ETA, not the
// recomputed components, for the market-clearing passes)
gen double c_eq_raw = c_j_total + `eta'
gen double c_eq_cr  = c_j_total + `eta' + pue * 0.700 * (cr_pe - p_E)

tempfile countries
save `countries'

// ─── Bilateral lambda matrix (85 x 85) ────────────────────────────────────────
use `countries', clear
keep iso3 bloc in_eu in_apec in_depa is_sanct csvorder
rename (iso3 bloc in_eu in_apec in_depa is_sanct csvorder) ///
       (j_iso j_bloc j_eu j_apec j_depa j_sanct j_order)
tempfile sellers
save `sellers'

use `countries', clear
keep iso3 bloc in_eu in_apec in_depa is_sanct
rename (iso3 bloc in_eu in_apec in_depa is_sanct) ///
       (k_iso k_bloc k_eu k_apec k_depa k_sanct)
cross using `sellers'

// G_ij from the bloc-distance matrix
gen double G_ij = .
replace G_ij = 0.00 if k_bloc == j_bloc
replace G_ij = 0.95 if (k_bloc == "W" & j_bloc == "C") | (k_bloc == "C" & j_bloc == "W")
replace G_ij = 0.40 if (k_bloc == "W" & j_bloc == "N") | (k_bloc == "N" & j_bloc == "W")
replace G_ij = 0.55 if (k_bloc == "C" & j_bloc == "N") | (k_bloc == "N" & j_bloc == "C")
replace G_ij = 0.20 if k_bloc == "N" & j_bloc == "N"
replace G_ij = 0.00 if k_iso == j_iso
// R_ij regulatory compatibility
gen byte R_ij = 0
replace R_ij = 1 if k_eu & j_eu
replace R_ij = 1 if k_apec & j_apec
replace R_ij = 1 if k_depa & j_depa
replace R_ij = 1 if k_iso == j_iso
// lambda_kj (missing = infinity)
gen double lambda_kj = `ALPHA_GEO' * G_ij + `ALPHA_REG' * (1 - R_ij)
replace lambda_kj = 0 if k_iso == j_iso
// Sanctions: either side sanctioned -> inf, EXCEPT same-bloc sanctioned pairs
replace lambda_kj = . if (k_sanct | j_sanct) & k_iso != j_iso
replace lambda_kj = `ALPHA_REG' if k_sanct & j_sanct & k_bloc == j_bloc & k_iso != j_iso
tempfile lambda_pairs
save `lambda_pairs'

// lambda_min per buyer (min over foreign sellers; all-missing -> . = inf)
use `lambda_pairs', clear
drop if k_iso == j_iso
collapse (min) lam_min = lambda_kj, by(k_iso)
rename k_iso iso3
tempfile lammin
save `lammin'

// lambda(j, USA) per seller (lambda is symmetric in its arguments)
use `lambda_pairs', clear
keep if k_iso == "USA"
keep j_iso lambda_kj
rename (j_iso lambda_kj) (iso3 lambda_usa)
tempfile lamusa
save `lamusa'

use `countries', clear
merge 1:1 iso3 using `lammin', keep(master match) nogen
merge 1:1 iso3 using `lamusa', keep(master match) nogen
gen double p_bilat_usa = cj_cr * (1 + lambda_usa)   // missing if lambda inf
save `countries', replace

// ─── Symmetric latency lookup (forward rows + missing reverse pairs) ─────────
import delimited "$data/country_pair_latency.csv", varnames(1) encoding("utf-8") clear
keep iso3_from iso3_to avg_ms
rename (iso3_from iso3_to avg_ms) (j_iso k_iso lat_ms)
tempfile lat_fwd
save `lat_fwd'
rename (j_iso k_iso) (k_iso j_iso)
merge 1:1 j_iso k_iso using `lat_fwd', keep(master) nogen   // reverse not in fwd
append using `lat_fwd'
duplicates drop j_iso k_iso, force
tempfile lat_sym
save `lat_sym'

// ─── Capacity-constrained equilibrium (mirrors solve_capacity_equilibrium) ───
cap program drop paper_equilibrium
program define paper_equilibrium, rclass
    // expects in memory: c_eq k_bar_j omega is_sanct csvorder [lam_min]
    // demand: bilateral -> import if lam_min<inf & c_k > (1+lam_min)p_T
    //         uniform   -> import if c_k > (1+lambda)p_T
    syntax , [lambda(real 0)] [bilateral]
    sort c_eq csvorder
    qui count
    local N = _N
    local p_T = .
    forvalues i = 1/`N' {
        if is_sanct[`i'] == 0 {
            local p_T = c_eq[`i']
            continue, break
        }
    }
    local Q_TX = 0
    forvalues iter = 1/30 {
        tempvar imp
        if "`bilateral'" != "" {
            qui gen double `imp' = ($ALPHA * omega * $Q_TOTAL) * ///
                (lam_min < . & c_eq > (1 + lam_min) * `p_T')
        }
        else {
            qui gen double `imp' = ($ALPHA * omega * $Q_TOTAL) * ///
                (c_eq > (1 + `lambda') * `p_T')
        }
        qui sum `imp'
        local Q_TX = r(sum)
        drop `imp'
        local cum = 0
        local found = 0
        local p_T_new = `p_T'
        forvalues i = 1/`N' {
            if is_sanct[`i'] == 1 continue
            local cum = `cum' + k_bar_j[`i']
            if `cum' >= `Q_TX' & `Q_TX' > 0 {
                local p_T_new = c_eq[`i']
                local found = 1
                continue, break
            }
        }
        if `found' & abs(`p_T_new' - `p_T') < 0.0001 {
            local p_T = `p_T_new'
            continue, break
        }
        if `found' local p_T = `p_T_new'
    }
    // capacity allocation (exporters = alloc > 0)
    cap drop alloc
    qui gen double alloc = 0
    local remaining = `Q_TX'
    forvalues i = 1/`N' {
        if is_sanct[`i'] == 1 continue
        if c_eq[`i'] > `p_T' continue, break
        local ca = min(k_bar_j[`i'], `remaining')
        if `ca' > 0 {
            qui replace alloc = `ca' in `i'
            local remaining = `remaining' - `ca'
        }
        if `remaining' <= 0 continue, break
    }
    return scalar p_T = `p_T'
    return scalar Q_TX = `Q_TX'
end

// Spec (1) raw equilibrium (lambda = 0)
use `countries', clear
gen double c_eq = c_eq_raw
paper_equilibrium, lambda(0)
local p_T_raw = r(p_T)
rename alloc alloc_raw
keep iso3 alloc_raw
tempfile eq_raw
save `eq_raw'

// Spec (2) cost-recovery equilibrium (lambda = 0)
use `countries', clear
gen double c_eq = c_eq_cr
paper_equilibrium, lambda(0)
local p_T_cr = r(p_T)
rename alloc alloc_cr
keep iso3 alloc_cr
tempfile eq_cr
save `eq_cr'

// Spec (3) bilateral equilibrium on cost-recovery costs
use `countries', clear
gen double c_eq = c_eq_cr
paper_equilibrium, bilateral
local p_T_bilat = r(p_T)
rename alloc alloc_bilat
keep iso3 alloc_bilat
tempfile eq_bilat
save `eq_bilat'

di as txt "  Equilibria: p_T raw = $" %6.4f `p_T_raw' ///
    ", CR = $" %6.4f `p_T_cr' ", bilateral CR = $" %6.4f `p_T_bilat'

use `countries', clear
merge 1:1 iso3 using `eq_raw',   keep(master match) nogen
merge 1:1 iso3 using `eq_cr',    keep(master match) nogen
merge 1:1 iso3 using `eq_bilat', keep(master match) nogen
save `countries', replace

// ─── Inference sourcing ───────────────────────────────────────────────────────
// Pair frame with latency + seller costs + lambda
use `countries', clear
keep iso3 c_eq_raw c_eq_cr is_sanct csvorder
rename (iso3 c_eq_raw c_eq_cr is_sanct csvorder) ///
       (j_iso j_c_raw j_c_cr j_sanct j_order)
tempfile inf_sellers
save `inf_sellers'

use `countries', clear
keep iso3 c_eq_raw c_eq_cr
rename (iso3 c_eq_raw c_eq_cr) (k_iso k_c_raw k_c_cr)
cross using `inf_sellers'
merge 1:1 k_iso j_iso using `lat_sym', keep(master match) nogen
merge 1:1 k_iso j_iso using `lambda_pairs', keepusing(lambda_kj) keep(master match) nogen
replace lat_ms = `DOM_LAT' if k_iso == j_iso & missing(lat_ms)
tempfile inf_pairs
save `inf_pairs'

// Simple (free-trade) inference: foreign needs lat<=LBAR, non-sanctioned seller;
// foreign wins only if delivered cost is STRICTLY below the domestic option.
foreach spec in raw cr {
    use `inf_pairs', clear
    gen double deliv = (1 + `TAU_' * lat_ms) * j_c_`spec'
    gen double dom_cost = (1 + `TAU_' * lat_ms) * k_c_`spec' if k_iso == j_iso
    gen byte eligible_f = k_iso != j_iso & j_sanct == 0 & ///
        !missing(lat_ms) & lat_ms <= `LBAR'
    gen double deliv_f = deliv if eligible_f
    // first-in-csv-order tie-break among equal foreign delivered costs
    sort k_iso deliv_f j_order
    by k_iso: gen double best_f = deliv_f[1]
    by k_iso: gen str3 best_f_src = j_iso[1] if !missing(deliv_f[1])
    keep if k_iso == j_iso
    gen str3 inf_src_`spec' = cond(!missing(best_f) & best_f < dom_cost, ///
        best_f_src, k_iso)
    keep k_iso inf_src_`spec'
    rename k_iso iso3
    tempfile infsrc_`spec'
    save `infsrc_`spec''
}

// Bilateral inference: sovereignty premium in delivered cost, no latency cone,
// eligibility = lambda finite and latency observed
use `inf_pairs', clear
gen double deliv = (1 + lambda_kj) * (1 + `TAU_' * lat_ms) * j_c_cr
gen double dom_cost = (1 + `TAU_' * lat_ms) * k_c_cr if k_iso == j_iso
gen byte eligible_f = k_iso != j_iso & !missing(lambda_kj) & !missing(lat_ms)
gen double deliv_f = deliv if eligible_f
sort k_iso deliv_f j_order
by k_iso: gen double best_f = deliv_f[1]
by k_iso: gen str3 best_f_src = j_iso[1] if !missing(deliv_f[1])
keep if k_iso == j_iso
gen str3 inf_src_bilat = cond(!missing(best_f) & best_f < dom_cost, ///
    best_f_src, k_iso)
keep k_iso inf_src_bilat
rename k_iso iso3
tempfile infsrc_bilat
save `infsrc_bilat'

use `countries', clear
merge 1:1 iso3 using `infsrc_raw',   keep(master match) nogen
merge 1:1 iso3 using `infsrc_cr',    keep(master match) nogen
merge 1:1 iso3 using `infsrc_bilat', keep(master match) nogen

// Inference-exporter sets (countries that serve at least one foreign buyer)
foreach spec in raw cr bilat {
    preserve
    keep iso3 inf_src_`spec'
    keep if inf_src_`spec' != iso3
    keep inf_src_`spec'
    duplicates drop
    rename inf_src_`spec' iso3
    gen byte inf_exp_`spec' = 1
    tempfile iexp
    save `iexp'
    restore
    merge 1:1 iso3 using `iexp', keep(master match) nogen
    replace inf_exp_`spec' = 0 if missing(inf_exp_`spec')
}

// ─── Regime-type classification (EE / IE / DD / II) ───────────────────────────
// Specs (1)-(2): sanctioned -> DD; EE if allocated training capacity;
// IE if inference exporter and not domestic-training; DD if domestic both.
foreach spec in raw cr {
    local pt = cond("`spec'" == "raw", `p_T_raw', `p_T_cr')
    gen byte dom_train_`spec' = c_eq_`spec' <= `pt'
    gen byte dom_inf_`spec'   = inf_src_`spec' == iso3
    gen str2 type_`spec' = "II"
    replace type_`spec' = "DD" if dom_train_`spec' & dom_inf_`spec'
    replace type_`spec' = "IE" if inf_exp_`spec' & !dom_train_`spec'
    replace type_`spec' = "EE" if alloc_`spec' > 0 & !missing(alloc_`spec')
    replace type_`spec' = "DD" if is_sanct
}

// Spec (3) bilateral 5-type regime -> table letters
gen double lam_star_bilat = c_eq_cr / `p_T_bilat' - 1
gen byte dom_train_bilat = (lam_min >= lam_star_bilat) | (c_eq_cr <= `p_T_bilat')
// (missing lam_min = infinite premium -> never imports -> domestic training)
gen byte dom_inf_bilat = inf_src_bilat == iso3
gen str16 regime_5 = "full importer"
replace regime_5 = "domestic"      if dom_train_bilat & dom_inf_bilat
replace regime_5 = "hybrid"        if !dom_train_bilat & dom_inf_bilat
replace regime_5 = "inference hub" if inf_exp_bilat & !dom_train_bilat
replace regime_5 = "T+I exporter"  if alloc_bilat > 0 & !missing(alloc_bilat)
replace regime_5 = "domestic"      if is_sanct
gen str2 type_bilat = "II"
replace type_bilat = "IE" if regime_5 == "inference hub"
replace type_bilat = "DD" if regime_5 == "domestic"
replace type_bilat = "EE" if alloc_bilat > 0 & !missing(alloc_bilat)
replace type_bilat = "DD" if is_sanct
gen str2 type_bilat_usa = cond(iso3 == "USA", "DD", type_bilat)

// ─── Ranks (stable sort, CSV order breaks ties — mirrors Python sorted()) ────
foreach spec in raw cr wacc {
    sort cj_`spec' csvorder
    gen int rank_`spec' = _n
}
sort csvorder
save `countries', replace

// ─── Display-name and flag helpers ────────────────────────────────────────────
cap program drop _shortname
program define _shortname
    // args: newvar style
    //   mapped3  (Table 3):  map incl. "United States of America"; >19 -> [:18]+'.'
    //   mappeda2 (Table A2): same map but WITHOUT the long-form US key
    //                        (the paper's A2 builder lacks it, so A2 prints
    //                        the truncation "United States of A.")
    //   plain    (Table A1): no map; >20 -> [:19]+'.'
    args newvar style
    gen str40 `newvar' = country
    if inlist("`style'", "mapped3", "mappeda2") {
        replace `newvar' = "UAE"            if country == "United Arab Emirates"
        replace `newvar' = "UK"             if country == "United Kingdom"
        replace `newvar' = "USA"            if country == "United States"
        replace `newvar' = "USA"            if country == "United States of America" ///
            & "`style'" == "mapped3"
        replace `newvar' = "Bosnia & Herz." if country == "Bosnia and Herzegovina"
        replace `newvar' = "N. Macedonia"   if country == "North Macedonia"
        replace `newvar' = "Czechia"        if country == "Czech Republic"
        replace `newvar' = substr(country, 1, 18) + "." ///
            if `newvar' == country & ustrlen(country) > 19
    }
    else {
        replace `newvar' = substr(country, 1, 19) + "." if ustrlen(country) > 20
    }
end

// Type flags: '*' sanctioned, dagger for developing EE/IE
cap program drop _flagtype
program define _flagtype
    args newvar typevar
    gen str6 `newvar' = `typevar'
    replace `newvar' = `newvar' + "*" if is_sanct
    replace `newvar' = `newvar' + uchar(8224) if is_dev & inlist(`typevar', "EE", "IE")
end

// ══════════════════════════════════════════════════════════════════════════════
// Table 3 — four independently sorted top-25 blocks, paper cell strings
// ══════════════════════════════════════════════════════════════════════════════
use `countries', clear
_shortname sname mapped3
_flagtype ftype_raw  type_raw
_flagtype ftype_cr   type_cr
_flagtype ftype_busa type_bilat_usa
_flagtype ftype_wacc type_cr    // spec (4) reuses the CR regime type

// (1) Raw
preserve
sort cj_raw csvorder
keep in 1/25
gen int row = _n
keep row sname cj_raw ftype_raw
gen str20 c1_country = sname
gen str10 c1_P = "$" + strtrim(string(cj_raw, "%9.2f"))
gen str8  c1_T = ftype_raw
keep row c1_*
tempfile blk1
save `blk1'
restore
// (2) Cost-recovery
preserve
sort cj_cr csvorder
keep in 1/25
gen int row = _n
gen str20 c2_country = sname
gen str10 c2_P = "$" + strtrim(string(cj_cr, "%9.2f"))
gen str8  c2_T = ftype_cr
keep row c2_*
tempfile blk2
save `blk2'
restore
// (3) Bilateral delivered price to the US buyer (finite only)
preserve
drop if missing(p_bilat_usa)
sort p_bilat_usa csvorder
keep in 1/25
gen int row = _n
gen str20 c3_country = sname
gen str10 c3_P = "$" + strtrim(string(p_bilat_usa, "%9.2f"))
gen str8  c3_T = ftype_busa
keep row c3_*
tempfile blk3
save `blk3'
restore
// (4) CR + host-country WACC
preserve
sort cj_wacc csvorder
keep in 1/25
gen int row = _n
gen str20 c4_country = sname
gen str10 c4_P = "$" + strtrim(string(cj_wacc, "%9.2f"))
gen str8  c4_T = ftype_wacc
keep row c4_*
tempfile blk4
save `blk4'
restore

use `blk1', clear
merge 1:1 row using `blk2', nogen
merge 1:1 row using `blk3', nogen
merge 1:1 row using `blk4', nogen
sort row
drop row
order c1_country c1_P c1_T c2_country c2_P c2_T c3_country c3_P c3_T ///
      c4_country c4_P c4_T
export delimited using "$output/table3_rankings_top25.csv", replace
di as txt "  Table 3 exported (4 spec blocks x top 25)"

// ══════════════════════════════════════════════════════════════════════════════
// Table A1 — country calibration parameters, sorted by cost-recovery rank
// ══════════════════════════════════════════════════════════════════════════════
use `countries', clear
_shortname a1name plain
sort rank_cr
gen str24 col_country  = a1name
gen str10 col_pE       = "$" + strtrim(string(p_E, "%9.3f"))
gen str8  col_theta    = strtrim(string(theta, "%9.1f"))
gen str8  col_pue      = strtrim(string(pue, "%9.2f"))
gen str10 col_constr   = "$" + strtrim(string(p_L, "%9.2f"))
gen str12 col_kbar     = cond(capacity_mw >= 10, ///
    strtrim(string(capacity_mw, "%15.0fc")), strtrim(string(capacity_mw, "%9.0f")))
gen str8  col_omega    = strtrim(string(omega * 100, "%9.1f"))
gen str10 col_cj       = "$" + strtrim(string(c_j_total, "%9.2f"))
gen str10 col_crpE     = "$" + strtrim(string(cr_pe, "%9.3f"))
keep col_*
order col_country col_pE col_theta col_pue col_constr col_kbar col_omega ///
      col_cj col_crpE
export delimited using "$output/tableA1_calibration_parameters.csv", replace
di as txt "  Table A1 exported (85 countries, CR-rank order)"

// ══════════════════════════════════════════════════════════════════════════════
// Table A2 — all countries, raw + cost-recovery + bilateral type
// ══════════════════════════════════════════════════════════════════════════════
use `countries', clear
_shortname sname mappeda2
sort rank_cr
gen str20 col_country = sname
gen str10 col1_cj   = "$" + strtrim(string(cj_raw, "%9.2f"))
gen str6  col1_rank = strtrim(string(rank_raw, "%9.0f"))
gen str4  col1_type = type_raw
gen str10 col2_cj   = "$" + strtrim(string(cj_cr, "%9.2f"))
gen str6  col2_rank = strtrim(string(rank_cr, "%9.0f"))
gen str4  col2_type = type_cr
gen str4  col3_type = type_bilat
keep col_country col1_* col2_* col3_type
order col_country col1_cj col1_rank col1_type col2_cj col2_rank col2_type col3_type
export delimited using "$output/tableA2_rankings_all.csv", replace
di as txt "  Table A2 exported (85 countries)"

// ══════════════════════════════════════════════════════════════════════════════
// Table A3 — sensitivity of cost-recovery rankings to hardware share (rho)
// ══════════════════════════════════════════════════════════════════════════════
use `countries', clear
keep iso3 country cr_pe pue constr_cost is_dev csvorder
local rho_base = 25000 / (3 * (365.25 * 24) * 0.70)
local scen1_rho = `rho_base'
local scen2_rho = 1.30
local scen3_rho = 1.42
local scen1_lab "Baseline (`=uchar(961)'=$1.36)"
local scen2_lab "Low hardware share (`=uchar(961)'=$1.30)"
local scen3_lab "High hardware share (`=uchar(961)'=$1.42)"
local scen1_par "`=uchar(961)'=$1.36"
local scen2_par "`=uchar(961)'=$1.30 (`=uchar(8722)'4.4%)"
local scen3_par "`=uchar(961)'=$1.42 (+4.4%)"

tempname memhold
tempfile a3rows
postfile `memhold' str60 scenario str40 param_change int dev_top15 ///
    str10 max_spread str8 spearman str120 top5 using `a3rows'

forvalues s = 1/3 {
    // c_cr = GAMMA*cr_pe*pue + rho_s + ETA + constr_cost  (Python term order)
    cap drop c_s rank_s
    gen double c_s = 0.700 * cr_pe * pue + `scen`s'_rho' + 0.15 + constr_cost
    sort c_s csvorder
    gen int rank_s = _n
    if `s' == 1 {
        cap drop rank_base
        gen int rank_base = rank_s
        tempfile base_ranks
        preserve
        keep iso3 rank_base
        save `base_ranks'
        restore
    }
    else {
        cap drop rank_base
        merge 1:1 iso3 using `base_ranks', keep(master match) nogen
        sort c_s csvorder
    }
    // dev in top 15
    qui count if rank_s <= 15 & is_dev
    local dev15 = r(N)
    // max spread (max - min) / min * 100
    qui sum c_s
    local spread = (r(max) - r(min)) / r(min) * 100
    // Spearman vs baseline (rank-difference formula, no ties by construction)
    tempvar dsq
    qui gen double `dsq' = (rank_s - rank_base)^2
    qui sum `dsq'
    qui count
    local n = r(N)
    qui sum `dsq'
    local rho_corr = 1 - 6 * r(sum) / (`n' * (`n'^2 - 1))
    // top-5 full country names
    sort rank_s
    local top5 = country[1]
    forvalues i = 2/5 {
        local top5 "`top5', `=country[`i']'"
    }
    local spread_str = strtrim(string(`spread', "%9.1f")) + "%"
    local rho_str = strtrim(string(`rho_corr', "%9.2f"))
    post `memhold' ("`scen`s'_lab'") ("`scen`s'_par'") (`dev15') ///
        ("`spread_str'") ("`rho_str'") ("`top5'")
    di as txt "  A3 scenario `s': dev15=`dev15', spread=" %4.1f `spread' ///
        "%, top5=`top5'"
}
postclose `memhold'
use `a3rows', clear
export delimited using "$output/tableA3_sensitivity.csv", replace
di as txt "  Table A3 exported (3 rho scenarios)"

// ══════════════════════════════════════════════════════════════════════════════
// Tables A5 / A6 — from step 14 results
// ══════════════════════════════════════════════════════════════════════════════
use "$output/kyrgyzstan_dcf.dta", clear
export delimited using "$output/tableA5_dcf_cashflow.csv", replace

use "$output/kyrgyzstan_dcf_sensitivity.dta", clear
// Paper cell strings: NPV in $ millions (sign after $), IRR at 1 decimal
gen str12 npv_m  = "$" + strtrim(string(npv / 1e6, "%12.0f"))
gen str8  irr_pc = strtrim(string(irr * 100, "%9.1f")) + "%"
keep scenario npv_m irr_pc
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
