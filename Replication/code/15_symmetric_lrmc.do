/*==============================================================================
  15_symmetric_lrmc.do — Symmetric LRMC cost-recovery (Table 3/A2 col (2))

  Reimplements work/lrmc_symmetric/build_symmetric_lrmc.py in Stata.

  Symmetrically corrects electricity-price distortions on BOTH sides:
    - 13 developing subsidized tariffs  -> IMF-based LRMC (v32 values, unchanged)
    - OECD/high-income observed tariffs -> + carbon-price adder (EMBER grid CI x
                                            2024 ETS price) + documented
                                            cross-subsidy add-back
    - everyone else                     -> observed price unchanged

  Then recomputes c_j (eq. 1) and ranks. Reproduces the published col (2)
  top-5: Kyrgyzstan, Ethiopia, Kosovo, Canada, Tajikistan.
  Saves symmetric_lrmc.dta.

  Constants transcribed from build_symmetric_lrmc.py (2024 annual averages).
==============================================================================*/

clear
set type double

// ─── Calibration primitives ──────────────────────────────────────────────────
import delimited "$data/calibration_results_v3.csv", varnames(1) ///
    encoding("utf-8") clear
keep iso3 country pue p_e_usd_kwh theta_summer_c p_l_usd_per_w
rename p_e_usd_kwh p_E_obs
rename p_l_usd_per_w p_L
rename theta_summer_c theta
tempfile cal
save `cal'

// ══════════════════════════════════════════════════════════════════════════════
// CONSTANT TABLE 1: v32 subsidy adjustment (13 developing countries)
// ══════════════════════════════════════════════════════════════════════════════
clear
input str3 iso3 double p_E_v32
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
end
tempfile v32
save `v32'

// ══════════════════════════════════════════════════════════════════════════════
// CONSTANT TABLE 2: symmetric-LRMC scope (43 OECD/HI countries) with
//   EMBER 2024 grid carbon intensity (gCO2/kWh) and 2024 carbon price (USD/tCO2)
//   carbon price already resolved per regime (EU ETS 70.94, UK 47.32, CAN 58.48,
//   USA 3.81 weighted, KOR 0 (<$10), NZL 39.5, SGP 18.6, others 0).
//   Excludes ARE/SAU/QAT (handled by v32 table above).
// ══════════════════════════════════════════════════════════════════════════════
clear
input str3 iso3 double grid_ci double carbon_price
"AUT" 100 70.94
"BEL" 160 70.94
"BGR" 380 70.94
"HRV" 170 70.94
"CYP" 600 70.94
"CZE" 430 70.94
"DNK" 135 70.94
"EST" 560 70.94
"FIN"  65 70.94
"FRA"  50 70.94
"DEU" 380 70.94
"GRC" 370 70.94
"HUN" 230 70.94
"IRL" 300 70.94
"ITA" 260 70.94
"LVA" 200 70.94
"LTU" 150 70.94
"LUX"  70 70.94
"MLT" 380 70.94
"NLD" 340 70.94
"POL" 660 70.94
"PRT" 120 70.94
"ROU" 250 70.94
"SVK" 120 70.94
"SVN" 200 70.94
"ESP" 160 70.94
"SWE"  40 70.94
"NOR"  20 70.94
"ISL"  35 70.94
"CHE"  40 70.94
"GBR" 200 47.32
"CAN" 130 58.48
"USA" 370  3.81
"KOR" 430  0.00
"JPN" 450  0.00
"AUS" 530  0.00
"NZL" 110 39.50
"ISR" 520  0.00
"CHL" 330  0.00
"MEX" 400  0.00
"SGP" 400 18.60
"TUR" 420  0.00
"COL" 150  0.00
end
gen double carbon_adder = (grid_ci / 1000000) * carbon_price
tempfile carbon
save `carbon'

// ══════════════════════════════════════════════════════════════════════════════
// CONSTANT TABLE 3: cross-subsidy add-backs (USD/kWh); others = 0
// ══════════════════════════════════════════════════════════════════════════════
clear
input str3 iso3 double cross_sub
"DEU" 0.038
"FRA" 0.015
"ESP" 0.010
"ITA" 0.010
"NLD" 0.010
"BEL" 0.010
"USA" 0.015
"KOR" 0.020
"JPN" 0.000
end
tempfile xsub
save `xsub'

// ─── Assemble symmetric p_E ──────────────────────────────────────────────────
use `cal', clear
merge 1:1 iso3 using `v32',    keep(master match) nogen
merge 1:1 iso3 using `carbon', keep(master match) nogen
merge 1:1 iso3 using `xsub',   keep(master match) nogen

replace carbon_adder = 0 if missing(carbon_adder)
replace cross_sub    = 0 if missing(cross_sub)

// Treatment: v32-adjusted (13) takes precedence; then symmetric-LRMC scope
//   (countries that have a carbon_price row); else keep observed.
gen str20 treatment = "keep_observed"
replace treatment = "apply_symmetric_lrmc" if !missing(carbon_price)
replace treatment = "keep_v32_adjusted"    if !missing(p_E_v32)

gen double p_E_sym = p_E_obs
replace p_E_sym = p_E_v32                          if treatment == "keep_v32_adjusted"
replace p_E_sym = p_E_obs + carbon_adder + cross_sub if treatment == "apply_symmetric_lrmc"

// ─── Recompute c_j (eq. 1) under symmetric p_E ───────────────────────────────
// PUE(theta) = PUE_BASE + PUE_SLOPE*max(0,theta-THETA_REF); shared globals.
gen double pue_sym = $PUE_BASE + $PUE_SLOPE * max(0, theta - $THETA_REF)
gen double c_elec  = pue_sym * $GAMMA * p_E_sym
gen double c_const = (p_L * $GPU_TDP_KW * 1000) / ($DC_LIFE_YR * $H_YR)
gen double c_j     = c_elec + $R_HARDWARE + c_const

gsort c_j
gen int rank_symmetric = _n

di as txt _n "=== Symmetric LRMC: top-10 cost ranking ==="
di as txt "  (expected top-5: KGZ, ETH, XKX, CAN, TJK)"
forvalues i = 1/10 {
    di as txt "  " %2.0f rank_symmetric[`i'] ". " iso3[`i'] " (" country[`i'] ")" ///
        "  c_j = $" %6.4f c_j[`i'] "  p_E = $" %6.4f p_E_sym[`i']
}

count if treatment == "keep_v32_adjusted"
local n_v32 = r(N)
count if treatment == "apply_symmetric_lrmc"
local n_sym = r(N)
di as txt _n "  Adjusted: `n_v32' v32 + `n_sym' symmetric = " `n_v32' + `n_sym' " countries"

// ─── Equilibrium under symmetric costs (reuse solver machinery) ──────────────
// Bring in k_bar and omega from the main pipeline temp files.
merge 1:1 iso3 using "$temp/demand_shares.dta", keepusing(omega) keep(master match) nogen
preserve
import delimited "$data/grid_capacity_estimates.csv", varnames(1) encoding("utf-8") clear
keep iso3 k_bar_gpu_hours
gen double k_bar_j = k_bar_gpu_hours * $K_BAR_SCALE
keep iso3 k_bar_j
tempfile kbar
save `kbar'
restore
merge 1:1 iso3 using `kbar', keep(master match) nogen

gen byte is_sanctioned = 0
foreach iso of global SANCTIONED {
    qui replace is_sanctioned = 1 if iso3 == "`iso'"
}

replace omega = 0 if missing(omega)

// Solver clears on the DELIVERED cost, which includes the networking term ETA
// (mirrors step 08: c_j = c_j_total + ETA). c_j here is c_j_total (no ETA), so
// add ETA just for the equilibrium; the ranking is unchanged (ETA is uniform).
tempvar c_j_total_sym
gen double `c_j_total_sym' = c_j
replace c_j = c_j + $ETA
sort c_j
solve_equilibrium, lambda(0)
replace c_j = `c_j_total_sym'
local p_T_sym = r(p_T)
local hhi_sym = r(hhi_T)
di as txt _n "  Symmetric-LRMC training equilibrium: p_T = $" %6.3f `p_T_sym' ///
    "/hr, HHI_T = " %6.4f `hhi_sym'
global p_T_symmetric = `p_T_sym'
global hhi_T_symmetric = `hhi_sym'

// ─── Save ────────────────────────────────────────────────────────────────────
keep iso3 country p_E_obs p_E_sym treatment carbon_adder cross_sub ///
     pue_sym c_elec c_const c_j rank_symmetric
order iso3 country rank_symmetric c_j p_E_obs p_E_sym treatment
compress
save "$temp/symmetric_lrmc.dta", replace
di as txt "  Saved: symmetric_lrmc.dta"
