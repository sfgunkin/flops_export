/*==============================================================================
  10_inference_sourcing.do — Inference sourcing under cost-recovery costs

  For each demand center k, finds the cheapest inference source j that
  minimizes (1 + tau * l_jk) * c_j under the cost-recovery adjusted costs.
  Computes inference revenue shares and HHI_I.
  Saves inference_sourcing.dta.
==============================================================================*/

clear
set type double

// ─── Load cost-recovery adjusted costs ───────────────────────────────────────
use "$temp/cost_recovery.dta", clear
keep iso3 country c_j omega
qui count
local N = _N

// Store in locals
forvalues i = 1/`N' {
    local iso_`i' = iso3[`i']
    local cost_`i' = c_j[`i']
    local omega_`i' = omega[`i']
    local name_`i' = country[`i']
}

// Load latency
preserve
use "$temp/latency_symmetric.dta", clear
tempfile latency_all
save `latency_all'
restore

// ─── For each demand center k, find best inference source ────────────────────
tempfile inf_results
postfile handle str3 iso3_k str40 country_k ///
    double(c_k omega_k P_I_domestic best_inf_cost) ///
    str3 best_inf_source ///
    using `inf_results'

forvalues k = 1/`N' {
    local iso_k = "`iso_`k''"
    local c_k = `cost_`k''
    local om_k = `omega_`k''

    // Domestic latency
    preserve
    use `latency_all', clear
    qui keep if iso3_from == "`iso_k'" & iso3_to == "`iso_k'"
    if _N > 0 {
        local l_kk = latency_ms[1]
    }
    else {
        local l_kk = 0
    }
    restore

    local P_I_dom = (1 + $TAU * `l_kk') * `c_k'
    local best_inf_c = `P_I_dom'
    local best_inf_j = "`iso_k'"

    // Search all other countries
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
            if `del' < `best_inf_c' {
                local best_inf_c = `del'
                local best_inf_j = "`iso_j'"
            }
        }
    }

    post handle ("`iso_k'") ("`name_`k''") ///
        (`c_k') (`om_k') (`P_I_dom') (`best_inf_c') ("`best_inf_j'")
}

postclose handle
use `inf_results', clear

// ─── Compute inference revenue shares ────────────────────────────────────────
// Revenue share = sum of omega_k for all countries k served by source j
preserve
collapse (sum) inf_share = omega_k, by(best_inf_source)
rename best_inf_source iso3

// HHI_I
gen double share_sq = inf_share^2
qui sum share_sq
local hhi_I = r(sum)
drop share_sq

gsort -inf_share
di as txt _n "Inference revenue shares (cost-recovery adjusted):"
di as txt "{hline 50}"
forvalues i = 1/10 {
    if `i' > _N continue, break
    di as txt "  " iso3[`i'] ": " %6.1f inf_share[`i']*100 "%"
}
di as txt _n "  HHI_I = " %6.4f `hhi_I'

tempfile inf_shares
save `inf_shares'
restore

// Merge shares back
merge m:1 best_inf_source using `inf_shares', ///
    keepusing(inf_share) keep(master match) nogen
rename inf_share source_total_share

// ─── KGZ inference clients ──────────────────────────────────────────────────
di as txt _n "Kyrgyzstan inference clients:"
preserve
keep if best_inf_source == "KGZ"
sort country_k
forvalues i = 1/`=_N' {
    di as txt "  " iso3_k[`i'] " (" country_k[`i'] "): omega = " ///
        %5.2f omega_k[`i']*100 "%"
}
restore

// ─── Save ────────────────────────────────────────────────────────────────────
compress
save "$temp/inference_sourcing.dta", replace

global hhi_I_cr = `hhi_I'

di as txt "  Saved: inference_sourcing.dta"
