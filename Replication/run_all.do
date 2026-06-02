/*==============================================================================
  run_all.do — Master replication script for the FLOPs Export paper
  "Cheap Energy Might Not Be Enough: A Trade Model of AI Compute Services"

  This script reproduces the numerical results, rankings, sensitivity analysis,
  reliability-adjusted rankings, and the Kyrgyzstan DCF from the analysis-ready
  input data in data/. It is a portable adaptation of the original 00_master.do.

  HOW TO RUN
  ----------
    1. Open Stata (version 16 or later recommended).
    2. Change to this folder, e.g.:
           cd "C:/path/to/Replication"
    3. Run:
           do run_all.do

  The script auto-detects its root from the working directory. If that is not
  convenient, hard-code the path on the "global root" line below.

  OUTPUTS
  -------
    output/   final result files (see README.md for the table/figure map)
    temp/     intermediate .dta files (regenerated each run)
==============================================================================*/

clear all
set more off
set type double
set maxvar 10000
set varabbrev off   // reproducibility: never abbreviation-match variable names
                    // (the solver renames vars to *_lam0 / *_cr then re-drops
                    //  the bare names; with varabbrev on those drops would
                    //  silently delete the renamed copies)

// ═══════════════════════════════════════════════════════════════════════════════
// PATHS  (portable — derived from the current working directory)
// ═══════════════════════════════════════════════════════════════════════════════

global root     "`c(pwd)'"
// global root  "C:/path/to/Replication"   // <- uncomment & edit to override

global data     "$root/data"
global programs "$root/code"
global temp     "$root/temp"
global output   "$root/output"

// Sanity check: confirm we are pointed at the package root
capture confirm file "$programs/_solver_program.do"
if _rc {
    di as error "──────────────────────────────────────────────────────────────"
    di as error "ERROR: could not find code/_solver_program.do under:"
    di as error "       $root"
    di as error "Fix: in Stata, cd to the Replication folder first, e.g."
    di as error {char 34}cd {char 34} + {char 34}C:/path/to/Replication{char 34}
    di as error "then run:  do run_all.do"
    di as error "Or hard-code the global root near the top of this script."
    di as error "──────────────────────────────────────────────────────────────"
    exit 601
}

// Create working directories if needed
cap mkdir "$temp"
cap mkdir "$output"

// ═══════════════════════════════════════════════════════════════════════════════
// STRUCTURAL PARAMETERS  (single source of truth)
// ═══════════════════════════════════════════════════════════════════════════════

// GPU hardware
global GPU_TDP_KW   = 0.700               // kW (700 watts)
global GPU_TDP_W    = $GPU_TDP_KW * 1000  // = 700 watts
global GPU_PRICE    = 25000               // $/GPU (H100)
global GPU_LIFE_YR  = 3                    // years
global GPU_UTIL     = 0.70                 // utilization rate
global GPU_HOURS    = $GPU_LIFE_YR * 365.25 * 24 * $GPU_UTIL
global R_HARDWARE   = $GPU_PRICE / $GPU_HOURS  // $/GPU-hr (rho)

// Networking
global ETA = 0.15                          // $/GPU-hr amortized networking cost

// PUE model: PUE = PUE_BASE + PUE_SLOPE * max(0, theta - THETA_REF)
global PUE_BASE  = 1.08
global PUE_SLOPE = 0.015
global THETA_REF = 15.0

// DC construction
global DC_LIFE_YR = 15                     // facility lifetime (years)
global H_YR = 365.25 * 24                  // hours per year

// Latency degradation
global TAU = 0.0008                        // per ms

// Sovereignty premium
global LAMBDA = 0.10                        // 10%

// Domestic latency default
global DOMESTIC_LATENCY = 5.0              // ms

// Demand calibration
global ALPHA   = 0.50                       // training share of compute demand
global Q_TOTAL = 60000000000               // 60 billion GPU-hours

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
// OPTIONAL: capture a full run log
// ═══════════════════════════════════════════════════════════════════════════════

cap log close _all
log using "$output/run_all_log.txt", replace text name(replication)

di as txt _n "Replication root: $root"

// ═══════════════════════════════════════════════════════════════════════════════
// LOAD SOLVER PROGRAM
// ═══════════════════════════════════════════════════════════════════════════════

do "$programs/_solver_program.do"

// ═══════════════════════════════════════════════════════════════════════════════
// RUN ALL SCRIPTS
// ═══════════════════════════════════════════════════════════════════════════════

local steps "01_prep_electricity 02_prep_temperature 03_prep_construction 04_calibrate_costs 05_prep_latency 06_regime_assignment 07_demand_shares 08_capacity_equilibrium 09_cost_recovery 10_inference_sourcing 11_welfare_sovereignty 12_sensitivity 13_reliability 14_kyrgyzstan_dcf 15_symmetric_lrmc 16_wacc_channel 17_bilateral_lambda 18_construction_regression 19_export_tables"

local n = 0
foreach s of local steps {
    local ++n
    di as txt _n "{hline 70}"
    di as txt "STEP `n': `s'"
    di as txt "{hline 70}"
    do "$programs/`s'.do"
}

di as txt _n "{hline 70}"
di as txt "ALL STEPS COMPLETE"
di as txt "{hline 70}"
di as txt "Temp files:   $temp"
di as txt "Output files: $output"

cap log close replication
