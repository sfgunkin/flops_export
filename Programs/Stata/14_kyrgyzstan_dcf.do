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
// SENSITIVITY SCENARIOS (Table A6)
//
// Each scenario re-runs the FULL cash-flow model above (including GPU
// depreciation and insurance on the depreciated GPU value) with parameter
// adjustments, exactly as the published generator does. The base-case
// scenario must therefore reproduce the main NPV/IRR bit-for-bit; this is
// asserted below.
// ═══════════════════════════════════════════════════════════════════════════════

di as txt _n "=== Sensitivity Analysis ==="

cap program drop dcf_run
program define dcf_run, rclass
    // Rebuilds the full 15-year DCF with adjustments; returns npv and irr.
    // NOTE: clears the dataset in memory.
    syntax , [gpuadj(real 0) elecadj(real 0) priceadj(real 0) ///
              utiladj(real 0) waccadj(real 0)]

    local n_gpus = $N_GPUS
    local constr = $CONSTRUCTION_COST

    clear
    qui set obs 16
    gen int year = _n - 1

    // ── CAPEX: construction (yr 0), 5 GPU generations, networking refresh ──
    gen double capex = cond(year == 0, `constr', 0)
    forvalues g = 0/4 {
        local gy = 1 + `g' * 3
        local gp = $GPU_PRICE * (1 - $GPU_PRICE_DECLINE)^`g' * (1 + `gpuadj')
        qui replace capex = capex + `n_gpus' * `gp' if year == `gy'
    }
    qui replace capex = capex + `n_gpus' * $NETWORKING_COST_PER_GPU ///
        if inlist(year, 1, 6, 11)

    // ── Utilization ramp (adjustment applies in every operating year) ──
    gen double util = 0
    qui replace util = 0.40 if year == 1
    qui replace util = 0.60 if year == 2
    qui replace util = $GPU_UTIL if year >= 3
    qui replace util = min(max(util + `utiladj', 0), 0.95) if year >= 1

    // ── Current-generation GPU value (insurance base) and GPU depreciation ──
    gen double gpu_val = 0
    gen double depr_gpu = 0
    forvalues g = 0/4 {
        local gy = 1 + `g' * 3
        local gp = $GPU_PRICE * (1 - $GPU_PRICE_DECLINE)^`g' * (1 + `gpuadj')
        qui replace gpu_val = `n_gpus' * `gp' * ///
            max(0, 1 - (year - `gy') / $GPU_LIFE_YR) ///
            if year >= `gy' & year < `gy' + $GPU_LIFE_YR
        qui replace depr_gpu = `n_gpus' * `gp' / $GPU_LIFE_YR ///
            if year >= `gy' & year < `gy' + $GPU_LIFE_YR
    }

    // ── OPEX, revenue, income statement ──
    gen double ep = ($P_ELEC_KWH + `elecadj') * ///
        (1 + $ELEC_ESCALATION)^(year - 1) if year >= 1
    gen double opex = $TOTAL_POWER_MW * 1000 * $H_YR * ep ///
        + $STAFF_COST_YR * 1.03^(year - 1) ///
        + `constr' * $MAINTENANCE_PCT ///
        + (`constr' + gpu_val) * $INSURANCE_PCT ///
        + $CONNECTIVITY_COST_YR if year >= 1
    qui replace opex = 0 if year == 0
    gen double revenue = `n_gpus' * $H_YR * util * ///
        ($REVENUE_PER_GPU_HR + `priceadj') if year >= 1
    qui replace revenue = 0 if year == 0
    gen double depr = `constr' / $DC_LIFE_YR + depr_gpu if year >= 1
    qui replace depr = 0 if year == 0
    gen double ebitda = revenue - opex
    gen double ebt = ebitda - depr
    gen double tax = max(0, ebt * $TAX_RATE)
    gen double ni = ebt - tax
    gen double fcf = ni + depr - capex

    // ── NPV at (WACC + waccadj) ──
    local w = $WACC + `waccadj'
    tempvar pv
    qui gen double `pv' = fcf / (1 + `w')^year
    qui sum `pv'
    return scalar npv = r(sum)

    // ── IRR via bisection (WACC-independent) ──
    local lo = -0.50
    local hi = 2.0
    forvalues it = 1/200 {
        local mid = (`lo' + `hi') / 2
        tempvar pvt
        qui gen double `pvt' = fcf / (1 + `mid')^year
        qui sum `pvt'
        if r(sum) > 0 {
            local lo = `mid'
        }
        else {
            local hi = `mid'
        }
        drop `pvt'
    }
    return scalar irr = `mid'
end

// Scenario grid (labels use the typographic minus U+2212, as in the paper)
local minus = uchar(8722)
local n_sens = 11
local slbl1  "Base case"
local sopt1  ""
local slbl2  "GPU price `minus'20%"
local sopt2  "gpuadj(-0.20)"
local slbl3  "GPU price +20%"
local sopt3  "gpuadj(0.20)"
local slbl4  "Electricity +50%"
local sopt4  "elecadj(0.019)"
local slbl5  "Electricity `minus'25%"
local sopt5  "elecadj(-0.0095)"
local slbl6  "Revenue +5%"
local sopt6  "priceadj(0.08)"
local slbl7  "Revenue `minus'5%"
local sopt7  "priceadj(-0.08)"
local slbl8  "Utilization 80%"
local sopt8  "utiladj(0.10)"
local slbl9  "Utilization 60%"
local sopt9  "utiladj(-0.10)"
local slbl10 "WACC 10%"
local sopt10 "waccadj(-0.026)"
local slbl11 "WACC 16%"
local sopt11 "waccadj(0.034)"

tempfile sens_results
postfile senshandle str40 scenario double(npv irr) using `sens_results'

forvalues sc = 1/`n_sens' {
    dcf_run, `sopt`sc''
    local npv_s = r(npv)
    local irr_s = r(irr)
    post senshandle ("`slbl`sc''") (`npv_s') (`irr_s')
    di as txt "  `slbl`sc'': NPV=$" %12.0fc `npv_s' "  IRR=" %5.1f `irr_s'*100 "%"
    if `sc' == 1 {
        // The base scenario must replicate the main DCF above exactly
        if abs(`npv_s' - `npv') > 1 {
            di as error "ERROR: sensitivity base case NPV (`npv_s') does not" ///
                " match main DCF NPV (`npv')"
            exit 9
        }
    }
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
