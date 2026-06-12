// Validation driver: run only steps 14 + 19 against the Replication package
// (step 19 is self-contained on data/ CSVs; step 14 needs only globals).
clear all
set more off
set type double
set maxvar 10000
set varabbrev off

global root     "F:/OneDrive/__Documents/Papers/_Submitted/FLOPsExport/Replication"
global data     "$root/data"
global programs "$root/code"
global temp     "$root/temp"
global output   "$root/output"
cap mkdir "$temp"
cap mkdir "$output"

// Structural parameters (identical to run_all.do)
global GPU_TDP_KW   = 0.700
global GPU_TDP_W    = $GPU_TDP_KW * 1000
global GPU_PRICE    = 25000
global GPU_LIFE_YR  = 3
global GPU_UTIL     = 0.70
global GPU_HOURS    = $GPU_LIFE_YR * 365.25 * 24 * $GPU_UTIL
global R_HARDWARE   = $GPU_PRICE / $GPU_HOURS
global ETA = 0.15
global PUE_BASE  = 1.08
global PUE_SLOPE = 0.015
global THETA_REF = 15.0
global DC_LIFE_YR = 15
global H_YR = 365.25 * 24
global TAU = 0.0008
global LAMBDA = 0.10
global DOMESTIC_LATENCY = 5.0
global ALPHA   = 0.50
global Q_TOTAL = 60000000000
global K_BAR_SCALE = 1000
global GAMMA = $GPU_TDP_KW
global SANCTIONED "IRN"
global SUBSIDY_ISO "IRN TKM DZA EGY UZB QAT SAU ARE RUS KAZ NGA ZAF ETH"
global SUBSIDY_PRC "0.085 0.070 0.065 0.080 0.090 0.100 0.100 0.095 0.065 0.085 0.080 0.095 0.050"

// DCF parameters
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

di as txt "STEP 14"
do "$programs/14_kyrgyzstan_dcf.do"
di as txt "STEP 19"
do "$programs/19_export_tables.do"
di as txt "VALIDATION DRIVER COMPLETE"
