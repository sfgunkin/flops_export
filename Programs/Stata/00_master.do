/*==============================================================================
  00_master.do — Master script for FLOPs Export Paper replication

  Sets global parameters, creates directories, and runs all analysis scripts.
  All parameters are defined here as globals (single source of truth).
==============================================================================*/

clear all
set more off
set type double
set maxvar 10000

// ═══════════════════════════════════════════════════════════════════════════════
// PATHS
// ═══════════════════════════════════════════════════════════════════════════════

global root     "F:/onedrive/__documents/papers/FLOPsExport"
global data     "$root/Data"
global programs "$root/Programs/Stata"
global temp     "$programs/temp"
global output   "$programs/output"

// Create directories if needed
cap mkdir "$temp"
cap mkdir "$output"

// ═══════════════════════════════════════════════════════════════════════════════
// STRUCTURAL PARAMETERS
// ═══════════════════════════════════════════════════════════════════════════════

// GPU hardware
global GPU_TDP_KW   = 0.700          // kW (700 watts)
global GPU_TDP_W    = $GPU_TDP_KW * 1000  // = 700 watts
global GPU_PRICE    = 25000          // $/GPU (H100)
global GPU_LIFE_YR  = 3             // years
global GPU_UTIL     = 0.70          // utilization rate
global GPU_HOURS    = $GPU_LIFE_YR * 365.25 * 24 * $GPU_UTIL
global R_HARDWARE   = $GPU_PRICE / $GPU_HOURS  // $/GPU-hr (rho)

// Networking
global ETA = 0.15                   // $/GPU-hr amortized networking cost

// PUE model: PUE = PUE_BASE + PUE_SLOPE * max(0, theta - THETA_REF)
global PUE_BASE  = 1.08
global PUE_SLOPE = 0.015
global THETA_REF = 15.0

// DC construction
global DC_LIFE_YR = 15              // facility lifetime (years)
global H_YR = 365.25 * 24           // hours per year

// Latency degradation
global TAU = 0.0008                 // per ms

// Sovereignty premium
global LAMBDA = 0.10                // 10%

// Domestic latency default
global DOMESTIC_LATENCY = 5.0       // ms

// Demand calibration
global ALPHA   = 0.50               // training share of compute demand
global Q_TOTAL = 60000000000        // 60 billion GPU-hours

// Grid capacity scale correction (kWh→GWh unit error in source CSV)
global K_BAR_SCALE = 1000

// GAMMA (= GPU_TDP_KW, used in cost formula)
global GAMMA = $GPU_TDP_KW

// Sanctioned countries
global SANCTIONED "IRN"

// ═══════════════════════════════════════════════════════════════════════════════
// COST-RECOVERY ADJUSTMENT PRICES ($/kWh)
// 13 countries with subsidized electricity — replaced with LRMC estimates
// ═══════════════════════════════════════════════════════════════════════════════

// These are stored as a paired list: iso3 code and adjusted price
global SUBSIDY_ISO "IRN TKM DZA EGY UZB QAT SAU ARE RUS KAZ NGA ZAF ETH"
global SUBSIDY_PRC "0.085 0.070 0.065 0.080 0.090 0.100 0.100 0.095 0.065 0.085 0.080 0.095 0.050"

// ═══════════════════════════════════════════════════════════════════════════════
// DCF PARAMETERS (Kyrgyzstan data center)
// ═══════════════════════════════════════════════════════════════════════════════

global IT_CAPACITY_MW   = 40
global PUE_KGZ          = 1.08
global TOTAL_POWER_MW   = $IT_CAPACITY_MW * $PUE_KGZ
global N_GPUS           = floor($IT_CAPACITY_MW * 1000 / $GPU_TDP_KW)
global P_ELEC_KWH       = 0.038
global P_CONSTRUCTION_W = 7.83
global CONSTRUCTION_COST = $IT_CAPACITY_MW * 1000000 * $P_CONSTRUCTION_W
global STAFF_COUNT      = 50
global AVG_SALARY_YR    = 12000
global STAFF_COST_YR    = $STAFF_COUNT * $AVG_SALARY_YR
global MAINTENANCE_PCT  = 0.02
global INSURANCE_PCT    = 0.005
global BANDWIDTH_GBPS   = 100
global CONNECTIVITY_COST_YR = 2400000
global REVENUE_PER_GPU_HR  = 2.00
global NETWORKING_COST_PER_GPU = 2000
global NETWORKING_LIFE  = 5
global GPU_PRICE_DECLINE = 0.10
global ELEC_ESCALATION  = 0.02
global WACC             = 0.126
global TAX_RATE         = 0.10

// ═══════════════════════════════════════════════════════════════════════════════
// LOAD SOLVER PROGRAM
// ═══════════════════════════════════════════════════════════════════════════════

do "$programs/_solver_program.do"

// ═══════════════════════════════════════════════════════════════════════════════
// RUN ALL SCRIPTS
// ═══════════════════════════════════════════════════════════════════════════════

di as txt _n "{'='*70}"
di as txt "STEP 1: Prepare electricity prices"
di as txt "{'='*70}"
do "$programs/01_prep_electricity.do"

di as txt _n "{'='*70}"
di as txt "STEP 2: Prepare temperatures"
di as txt "{'='*70}"
do "$programs/02_prep_temperature.do"

di as txt _n "{'='*70}"
di as txt "STEP 3: Prepare construction costs"
di as txt "{'='*70}"
do "$programs/03_prep_construction.do"

di as txt _n "{'='*70}"
di as txt "STEP 4: Calibrate costs (c_j)"
di as txt "{'='*70}"
do "$programs/04_calibrate_costs.do"

di as txt _n "{'='*70}"
di as txt "STEP 5: Prepare latency data"
di as txt "{'='*70}"
do "$programs/05_prep_latency.do"

di as txt _n "{'='*70}"
di as txt "STEP 6: Regime assignment"
di as txt "{'='*70}"
do "$programs/06_regime_assignment.do"

di as txt _n "{'='*70}"
di as txt "STEP 7: Demand shares (omega_k)"
di as txt "{'='*70}"
do "$programs/07_demand_shares.do"

di as txt _n "{'='*70}"
di as txt "STEP 8: Capacity-constrained equilibrium"
di as txt "{'='*70}"
do "$programs/08_capacity_equilibrium.do"

di as txt _n "{'='*70}"
di as txt "STEP 9: Cost-recovery adjustment"
di as txt "{'='*70}"
do "$programs/09_cost_recovery.do"

di as txt _n "{'='*70}"
di as txt "STEP 10: Inference sourcing (cost-recovery)"
di as txt "{'='*70}"
do "$programs/10_inference_sourcing.do"

di as txt _n "{'='*70}"
di as txt "STEP 11: Welfare and sovereignty"
di as txt "{'='*70}"
do "$programs/11_welfare_sovereignty.do"

di as txt _n "{'='*70}"
di as txt "STEP 12: Sensitivity analysis"
di as txt "{'='*70}"
do "$programs/12_sensitivity.do"

di as txt _n "{'='*70}"
di as txt "STEP 13: Reliability-adjusted rankings"
di as txt "{'='*70}"
do "$programs/13_reliability.do"

di as txt _n "{'='*70}"
di as txt "STEP 14: Kyrgyzstan DCF model"
di as txt "{'='*70}"
do "$programs/14_kyrgyzstan_dcf.do"

di as txt _n "{'='*70}"
di as txt "ALL STEPS COMPLETE"
di as txt "{'='*70}"
di as txt "Temp files:   $temp"
di as txt "Output files: $output"
