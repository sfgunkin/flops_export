/*==============================================================================
  14_kyrgyzstan_dcf.do — 15-year DCF model for a data center in Kyrgyzstan

  Parameters from 00_master.do globals. Produces year-by-year cash flows,
  computes NPV, IRR (via bisection), payback period.
  Runs sensitivity scenarios.
  Saves kyrgyzstan_dcf.dta and kyrgyzstan_dcf_sensitivity.dta.
==============================================================================*/

clear
set type double

// ─── Derived parameters ─────────────────────────────────────────────────────
local n_gpus       = $N_GPUS
local constr_cost  = $CONSTRUCTION_COST
local total_power  = $TOTAL_POWER_MW
local staff_cost   = $STAFF_COST_YR

di as txt "=== Kyrgyzstan DCF Model ==="
di as txt "  IT capacity: $IT_CAPACITY_MW MW"
di as txt "  GPUs: `n_gpus'"
di as txt "  Construction cost: $" %12.0fc `constr_cost'

// ─── GPU refresh schedule ────────────────────────────────────────────────────
// Refreshes at years 1, 4, 7, 10, 13 (5 generations, 3-year life each)
// GPU price declines 10% each generation

// Networking refresh: years 1, 6, 11

// ─── Build year-by-year dataset ──────────────────────────────────────────────
clear
set obs 16  // Year 0 (construction) through Year 15

gen int year = _n - 1

// ── CAPEX ──
gen double capex_construction = 0
replace capex_construction = $CONSTRUCTION_COST if year == 0

// GPU purchases (5 generations)
gen double capex_gpu = 0
local gpu_prices ""
forvalues gen = 0/4 {
    local yr = 1 + `gen' * 3  // years 1, 4, 7, 10, 13
    local gp = $GPU_PRICE * (1 - $GPU_PRICE_DECLINE)^`gen'
    local cost = `n_gpus' * `gp'
    replace capex_gpu = `cost' if year == `yr'
    // Store for depreciation
    local gpu_yr_`gen' = `yr'
    local gpu_prc_`gen' = `gp'
}

// Networking
gen double capex_networking = 0
replace capex_networking = `n_gpus' * $NETWORKING_COST_PER_GPU ///
    if inlist(year, 1, 6, 11)

gen double total_capex = capex_construction + capex_gpu + capex_networking

// ── OPEX (years 1-15 only) ──
gen double util = 0
replace util = 0.40 if year == 1
replace util = 0.60 if year == 2
replace util = $GPU_UTIL if year >= 3

gen double elec_price = $P_ELEC_KWH * (1 + $ELEC_ESCALATION)^(year - 1) ///
    if year >= 1

gen double opex_electricity = `total_power' * 1000 * $H_YR * elec_price ///
    if year >= 1
replace opex_electricity = 0 if year == 0

gen double opex_staff = `staff_cost' * (1.03)^(year - 1) if year >= 1
replace opex_staff = 0 if year == 0

gen double opex_maintenance = `constr_cost' * $MAINTENANCE_PCT if year >= 1
replace opex_maintenance = 0 if year == 0

// Insurance (on construction + depreciated GPU value)
gen double current_gpu_value = 0
forvalues gen = 0/4 {
    local yr = `gpu_yr_`gen''
    local gp = `gpu_prc_`gen''
    // GPU value = n_gpus * price * max(0, 1 - age/life) for each year in its window
    forvalues y = `yr'/`=`yr' + $GPU_LIFE_YR - 1' {
        if `y' <= 15 {
            local age = `y' - `yr'
            local val = `n_gpus' * `gp' * max(0, 1 - `age' / $GPU_LIFE_YR)
            replace current_gpu_value = `val' if year == `y'
        }
    }
}

gen double opex_insurance = (`constr_cost' + current_gpu_value) * $INSURANCE_PCT ///
    if year >= 1
replace opex_insurance = 0 if year == 0

gen double opex_connectivity = $CONNECTIVITY_COST_YR if year >= 1
replace opex_connectivity = 0 if year == 0

gen double total_opex = opex_electricity + opex_staff + opex_maintenance ///
    + opex_insurance + opex_connectivity

// ── REVENUE ──
gen double gpu_hours = `n_gpus' * $H_YR * util if year >= 1
replace gpu_hours = 0 if year == 0

gen double revenue = gpu_hours * $REVENUE_PER_GPU_HR

// ── EBITDA and Taxes ──
gen double ebitda = revenue - total_opex

// Depreciation (straight-line: construction over DC_LIFE, GPU over GPU_LIFE)
gen double depr_construction = `constr_cost' / $DC_LIFE_YR if year >= 1
replace depr_construction = 0 if year == 0

gen double depr_gpu = 0
forvalues gen = 0/4 {
    local yr = `gpu_yr_`gen''
    local gp = `gpu_prc_`gen''
    forvalues y = `yr'/`=`yr' + $GPU_LIFE_YR - 1' {
        if `y' <= 15 {
            replace depr_gpu = `n_gpus' * `gp' / $GPU_LIFE_YR if year == `y'
        }
    }
}

gen double depreciation = depr_construction + depr_gpu

gen double ebt = ebitda - depreciation
gen double tax = max(0, ebt * $TAX_RATE)
gen double net_income = ebt - tax

// ── FREE CASH FLOW ──
gen double fcf = net_income + depreciation - total_capex

// ── Cumulative (undiscounted) ──
gen double cum_cf = sum(fcf)

// ─── NPV ─────────────────────────────────────────────────────────────────────
gen double discount_factor = (1 + $WACC)^(-year)
gen double pv_fcf = fcf * discount_factor
qui sum pv_fcf
local npv = r(sum)

// ─── IRR (bisection) ─────────────────────────────────────────────────────────
local irr_lo = -0.50
local irr_hi = 2.0

forvalues iter = 1/200 {
    local irr_mid = (`irr_lo' + `irr_hi') / 2

    // Compute NPV at irr_mid
    tempvar pv_test
    gen double `pv_test' = fcf / (1 + `irr_mid')^year
    qui sum `pv_test'
    local npv_test = r(sum)
    drop `pv_test'

    if `npv_test' > 0 {
        local irr_lo = `irr_mid'
    }
    else {
        local irr_hi = `irr_mid'
    }
}
local irr = `irr_mid'

// ─── Payback period ──────────────────────────────────────────────────────────
local payback = .
forvalues i = 1/16 {
    if cum_cf[`i'] > 0 & year[`i'] >= 1 {
        local payback = year[`i']
        continue, break
    }
}

// ─── Totals ──────────────────────────────────────────────────────────────────
qui sum revenue
local total_revenue = r(sum)
qui sum total_capex
local total_capex_all = r(sum)
qui sum total_opex
local total_opex_all = r(sum)
qui sum net_income
local total_profit = r(sum)
qui sum opex_electricity
local total_elec = r(sum)

di as txt _n "=== Key Financial Metrics ==="
di as txt "  Total Revenue (15yr):  $" %12.0fc `total_revenue'
di as txt "  Total CAPEX (15yr):    $" %12.0fc `total_capex_all'
di as txt "  Total OPEX (15yr):     $" %12.0fc `total_opex_all'
di as txt "  Total Net Income:      $" %12.0fc `total_profit'
di as txt "  WACC:                  " %5.1f $WACC * 100 "%"
di as txt "  NPV:                   $" %12.0fc `npv'
di as txt "  IRR:                   " %5.1f `irr' * 100 "%"
di as txt "  Simple payback:        Year `payback'"

// ─── Year-by-year display ────────────────────────────────────────────────────
di as txt _n "Year-by-year cash flows ($M):"
di as txt "{hline 80}"
di as txt %4s "Year" " " %8s "CAPEX" " " %8s "Revenue" " " %8s "OPEX" " " ///
          %8s "EBITDA" " " %8s "Tax" " " %8s "FCF" " " %8s "Cum CF"
di as txt "{hline 80}"

forvalues i = 1/16 {
    di as txt %4.0f year[`i'] " " ///
        %8.1f total_capex[`i']/1e6 " " ///
        %8.1f revenue[`i']/1e6 " " ///
        %8.1f total_opex[`i']/1e6 " " ///
        %8.1f ebitda[`i']/1e6 " " ///
        %8.1f tax[`i']/1e6 " " ///
        %8.1f fcf[`i']/1e6 " " ///
        %8.1f cum_cf[`i']/1e6
}

// ─── Save base case ──────────────────────────────────────────────────────────
compress
save "$output/kyrgyzstan_dcf.dta", replace

// ═══════════════════════════════════════════════════════════════════════════════
// SENSITIVITY SCENARIOS
// ═══════════════════════════════════════════════════════════════════════════════

di as txt _n "=== Sensitivity Analysis ==="

// Scenario runner: for each scenario, recompute all cash flows and find NPV/IRR
// Parameters: wacc_adj, price_adj, elec_adj, gpu_adj, util_adj

tempfile sens_results
postfile senshandle str40 scenario double(npv irr) using `sens_results'

// Define scenarios
local n_sens = 11
local slbl1  "Base case"
local swacc1 = 0
local sprc1  = 0
local selec1 = 0
local sgpu1  = 0
local sutil1 = 0

local slbl2  "GPU price -20%"
local swacc2 = 0
local sprc2  = 0
local selec2 = 0
local sgpu2  = -0.20
local sutil2 = 0

local slbl3  "GPU price +20%"
local swacc3 = 0
local sprc3  = 0
local selec3 = 0
local sgpu3  = 0.20
local sutil3 = 0

local slbl4  "Electricity +50%"
local swacc4 = 0
local sprc4  = 0
local selec4 = 0.019
local sgpu4  = 0
local sutil4 = 0

local slbl5  "Electricity -25%"
local swacc5 = 0
local sprc5  = 0
local selec5 = -0.0095
local sgpu5  = 0
local sutil5 = 0

local slbl6  "Revenue price +5%"
local swacc6 = 0
local sprc6  = 0.08
local selec6 = 0
local sgpu6  = 0
local sutil6 = 0

local slbl7  "Revenue price -5%"
local swacc7 = 0
local sprc7  = -0.08
local selec7 = 0
local sgpu7  = 0
local sutil7 = 0

local slbl8  "Utilization 80%"
local swacc8 = 0
local sprc8  = 0
local selec8 = 0
local sgpu8  = 0
local sutil8 = 0.10

local slbl9  "Utilization 60%"
local swacc9 = 0
local sprc9  = 0
local selec9 = 0
local sgpu9  = 0
local sutil9 = -0.10

local slbl10  "WACC 10%"
local swacc10 = -0.026
local sprc10  = 0
local selec10 = 0
local sgpu10  = 0
local sutil10 = 0

local slbl11  "WACC 16%"
local swacc11 = 0.034
local sprc11  = 0
local selec11 = 0
local sgpu11  = 0
local sutil11 = 0

forvalues sc = 1/`n_sens' {
    local w = $WACC + `swacc`sc''

    // Compute FCF stream
    local npv_s = 0
    local irr_cfs ""

    forvalues yr = 0/15 {
        // CAPEX
        local cx = 0
        if `yr' == 0 local cx = `constr_cost'

        // GPU
        forvalues gen = 0/4 {
            local gpu_yr = 1 + `gen' * 3
            if `yr' == `gpu_yr' {
                local gp = $GPU_PRICE * (1 - $GPU_PRICE_DECLINE)^`gen' * (1 + `sgpu`sc'')
                local cx = `cx' + `n_gpus' * `gp'
            }
        }

        // Networking
        if inlist(`yr', 1, 6, 11) {
            local cx = `cx' + `n_gpus' * $NETWORKING_COST_PER_GPU
        }

        // OPEX
        local ox = 0
        if `yr' >= 1 {
            local ep = ($P_ELEC_KWH + `selec`sc'') * (1 + $ELEC_ESCALATION)^(`yr' - 1)
            local ox = `total_power' * 1000 * $H_YR * `ep' ///
                     + `staff_cost' * 1.03^(`yr' - 1) ///
                     + `constr_cost' * $MAINTENANCE_PCT ///
                     + `constr_cost' * $INSURANCE_PCT ///
                     + $CONNECTIVITY_COST_YR
        }

        // Revenue
        local rev = 0
        if `yr' >= 1 {
            local u = cond(`yr' == 1, 0.40, cond(`yr' == 2, 0.60, $GPU_UTIL))
            local u = `u' + `sutil`sc''
            local u = min(max(`u', 0), 0.95)
            local rev = `n_gpus' * $H_YR * `u' * ($REVENUE_PER_GPU_HR + `sprc`sc'')
        }

        // Income
        local ebitda_s = `rev' - `ox'
        local depr_s = cond(`yr' >= 1, `constr_cost' / $DC_LIFE_YR, 0)
        local ebt_s = `ebitda_s' - `depr_s'
        local tax_s = max(0, `ebt_s' * $TAX_RATE)
        local ni_s = `ebt_s' - `tax_s'
        local cf_s = `ni_s' + `depr_s' - `cx'

        // Accumulate NPV
        local npv_s = `npv_s' + `cf_s' / (1 + `w')^`yr'

        // Store CF for IRR
        local irr_cfs "`irr_cfs' `cf_s'"
    }

    // IRR via bisection
    local lo = -0.50
    local hi = 2.0
    forvalues iter = 1/200 {
        local mid = (`lo' + `hi') / 2
        local test_npv = 0
        local yr_idx = 0
        foreach cf of local irr_cfs {
            local test_npv = `test_npv' + `cf' / (1 + `mid')^`yr_idx'
            local yr_idx = `yr_idx' + 1
        }
        if `test_npv' > 0 {
            local lo = `mid'
        }
        else {
            local hi = `mid'
        }
    }
    local irr_s = `mid'

    post senshandle ("`slbl`sc''") (`npv_s') (`irr_s')

    di as txt "  `slbl`sc'': NPV=$" %9.0fc `npv_s' " IRR=" %5.1f `irr_s'*100 "%"
}

postclose senshandle

use `sens_results', clear

di as txt _n "=== Sensitivity Summary ==="
di as txt "{hline 60}"
di as txt %-30s "Scenario" " " %12s "NPV ($M)" " " %8s "IRR"
di as txt "{hline 60}"
forvalues i = 1/`=_N' {
    di as txt %-30s scenario[`i'] " $" %10.0f npv[`i']/1e6 " " %7.1f irr[`i']*100 "%"
}

compress
save "$output/kyrgyzstan_dcf_sensitivity.dta", replace

di as txt _n "  Saved: kyrgyzstan_dcf.dta + kyrgyzstan_dcf_sensitivity.dta"
