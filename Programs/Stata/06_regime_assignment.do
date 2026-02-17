/*==============================================================================
  06_regime_assignment.do — Assign 4-way trade regimes ± sovereignty

  For each demand center k, finds:
    - Best training source: min c_j across all j (latency irrelevant)
    - Best inference source: min (1 + tau * l_jk) * c_j
  Assigns regime: full domestic, full import, or hybrid.
  Repeats with sovereignty premium lambda.
  Saves regime_assignment.dta.
==============================================================================*/

clear
set type double

// ─── Load calibration results and latency ────────────────────────────────────
use "$temp/calibration_results.dta", clear

// Get list of countries that have latency data
preserve
use "$temp/latency_symmetric.dta", clear
keep iso3_from
rename iso3_from iso3
duplicates drop
tempfile latency_countries
save `latency_countries'
restore

// Keep calibration countries that also have latency data
merge 1:1 iso3 using `latency_countries', keep(match) nogen

qui count
local N = r(N)
di as txt "  Countries with cost + latency data: `N'"

// Store costs in a temporary dataset for lookup
keep iso3 country c_j_total
tempfile costs
save `costs'

// ─── Build all-pairs regime assignment ───────────────────────────────────────
// For each k (demand center), find best training and inference source

// We'll work country by country and build results
tempfile results
postfile handle str3 iso3_k str40 country_k ///
    double(c_k P_T_domestic P_I_domestic) ///
    str3(best_train_source best_inf_source) ///
    double(best_train_cost best_inf_cost) ///
    str50(regime regime_with_sovereignty) ///
    using `results'

// Load latency for lookup
preserve
use "$temp/latency_symmetric.dta", clear
tempfile latency_all
save `latency_all'
restore

use `costs', clear
local N = _N

// Store all iso3 and costs in locals for nested loops
forvalues i = 1/`N' {
    local iso_`i' = iso3[`i']
    local cost_`i' = c_j_total[`i']
    local name_`i' = country[`i']
}

// For each demand center k
forvalues k = 1/`N' {
    local iso_k = "`iso_`k''"
    local c_k = `cost_`k''
    local name_k = "`name_`k''"

    // Domestic latency
    preserve
    use `latency_all', clear
    qui keep if iso3_from == "`iso_k'" & iso3_to == "`iso_k'"
    if _N > 0 {
        local l_kk = latency_ms[1]
    }
    else {
        local l_kk = $DOMESTIC_LATENCY
    }
    restore

    // Domestic costs
    local P_T_dom = `c_k'
    local P_I_dom = (1 + $TAU * `l_kk') * `c_k'

    // Best training source (min c_j)
    local best_train_j = "`iso_k'"
    local best_train_c = `c_k'

    forvalues j = 1/`N' {
        if `j' == `k' continue
        if `cost_`j'' < `best_train_c' {
            local best_train_c = `cost_`j''
            local best_train_j = "`iso_`j''"
        }
    }

    // Best inference source (min delivered cost)
    local best_inf_j = "`iso_k'"
    local best_inf_c = `P_I_dom'

    forvalues j = 1/`N' {
        if `j' == `k' continue
        local iso_j = "`iso_`j''"

        // Look up latency j→k
        preserve
        use `latency_all', clear
        qui keep if iso3_from == "`iso_j'" & iso3_to == "`iso_k'"
        local has_lat = _N
        if `has_lat' > 0 {
            local l_jk = latency_ms[1]
        }
        restore

        if `has_lat' > 0 {
            local del_cost = (1 + $TAU * `l_jk') * `cost_`j''
            if `del_cost' < `best_inf_c' {
                local best_inf_c = `del_cost'
                local best_inf_j = "`iso_j'"
            }
        }
    }

    // Assign regime (pure cost)
    local dom_train = ("`best_train_j'" == "`iso_k'")
    local dom_inf   = ("`best_inf_j'" == "`iso_k'")

    if `dom_train' & `dom_inf' {
        local regime "full domestic"
    }
    else if !`dom_train' & !`dom_inf' {
        local regime "full import"
    }
    else if !`dom_train' & `dom_inf' {
        local regime "import training + build inference"
    }
    else {
        local regime "build training + import inference"
    }

    // With sovereignty premium
    // Best foreign training cost
    local best_foreign_train = .
    forvalues j = 1/`N' {
        if `j' == `k' continue
        if `cost_`j'' < `best_foreign_train' | missing(`best_foreign_train') {
            local best_foreign_train = `cost_`j''
        }
    }

    // Best foreign inference cost
    local best_foreign_inf = .
    forvalues j = 1/`N' {
        if `j' == `k' continue
        local iso_j = "`iso_`j''"

        preserve
        use `latency_all', clear
        qui keep if iso3_from == "`iso_j'" & iso3_to == "`iso_k'"
        local has_lat = _N
        if `has_lat' > 0 {
            local l_jk = latency_ms[1]
        }
        restore

        if `has_lat' > 0 {
            local del = (1 + $TAU * `l_jk') * `cost_`j''
            if `del' < `best_foreign_inf' | missing(`best_foreign_inf') {
                local best_foreign_inf = `del'
            }
        }
    }

    local sov_dom_train = (`c_k' <= (1 + $LAMBDA) * `best_foreign_train')
    if missing(`best_foreign_inf') {
        local sov_dom_inf = 1
    }
    else {
        local sov_dom_inf = (`P_I_dom' <= (1 + $LAMBDA) * `best_foreign_inf')
    }

    if `sov_dom_train' & `sov_dom_inf' {
        local regime_sov "full domestic"
    }
    else if !`sov_dom_train' & !`sov_dom_inf' {
        local regime_sov "full import"
    }
    else if !`sov_dom_train' & `sov_dom_inf' {
        local regime_sov "import training + build inference"
    }
    else {
        local regime_sov "build training + import inference"
    }

    post handle ("`iso_k'") ("`name_k'") ///
        (`c_k') (`P_T_dom') (`P_I_dom') ///
        ("`best_train_j'") ("`best_inf_j'") ///
        (`best_train_c') (`best_inf_c') ///
        ("`regime'") ("`regime_sov'")
}

postclose handle

// ─── Load results and summarize ──────────────────────────────────────────────
use `results', clear

// Regime distribution (pure cost)
di as txt _n "Regime distribution (pure cost):"
tab regime

di as txt _n "Regime distribution (with sovereignty premium):"
tab regime_with_sovereignty

// Training hubs
di as txt _n "Top training sources:"
preserve
keep if best_train_source != iso3_k
contract best_train_source, freq(n_served)
gsort -n_served
list in 1/5, noobs
restore

// Inference hubs
di as txt _n "Top inference sources:"
preserve
keep if best_inf_source != iso3_k
contract best_inf_source, freq(n_served)
gsort -n_served
list in 1/10, noobs
restore

compress
save "$temp/regime_assignment.dta", replace

di as txt "  Saved: regime_assignment.dta (" _N " countries)"
