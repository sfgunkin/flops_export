/*==============================================================================
  13_reliability.do — Reliability-adjusted cost rankings

  Computes c_j / xi_j where xi_j is the reliability index (governance,
  grid quality, sanctions). Compares ranking to unadjusted baseline,
  reports Spearman rank correlation and top-10 changes.
  Saves reliability_rankings.dta.
==============================================================================*/

clear
set type double

// ─── Load reliability index ──────────────────────────────────────────────────
import delimited "$data/reliability_index.csv", ///
    varnames(1) encoding("utf-8") clear

keep iso3 xi_reliability governance grid_quality sanctions_adj
rename xi_reliability xi_j

tempfile reliability
save `reliability'

// ─── Load cost-recovery adjusted costs ───────────────────────────────────────
use "$temp/cost_recovery.dta", clear
keep iso3 country c_j

merge 1:1 iso3 using `reliability', keep(match) nogen

qui count
local N = _N

// ─── Compute reliability-adjusted cost ───────────────────────────────────────
// c_j_xi = c_j / xi_j  (higher xi = more reliable = lower adjusted cost)
gen double c_j_xi = c_j / xi_j

// ─── Rank both ───────────────────────────────────────────────────────────────
// Baseline rank (cost-recovery, no xi)
egen int rank_baseline = rank(c_j)

// Reliability-adjusted rank
egen int rank_xi = rank(c_j_xi)

// ─── Top 5 ───────────────────────────────────────────────────────────────────
di as txt _n "=== Reliability-Adjusted Rankings ==="
di as txt ""
di as txt "Top 10 (reliability-adjusted vs baseline):"
di as txt "{hline 75}"
di as txt %4s "Rank" " " %5s "ISO3" " " %-24s "Country" " " ///
          %8s "c_j/xi" " " %8s "c_j" " " %5s "xi" " " %6s "Base"
di as txt "{hline 75}"

// Sort by xi rank for display
gsort rank_xi
forvalues i = 1/10 {
    di as txt %4.0f rank_xi[`i'] " " %5s iso3[`i'] " " ///
        %-24s country[`i'] " $" %7.3f c_j_xi[`i'] " $" %7.3f c_j[`i'] ///
        " " %5.2f xi_j[`i'] " " %4.0f rank_baseline[`i']
}

// ─── Spearman rank correlation ───────────────────────────────────────────────
gen double d_sq = (rank_baseline - rank_xi)^2
qui sum d_sq
local sum_d_sq = r(sum)
local spearman = 1 - 6 * `sum_d_sq' / (`N' * (`N'^2 - 1))
drop d_sq

di as txt _n "Spearman rank correlation (baseline vs xi-adjusted): " ///
    %6.4f `spearman'

// ─── Top-10 changes ─────────────────────────────────────────────────────────
// Count how many baseline top-10 fall out of xi top-10
gen byte in_base_top10 = (rank_baseline <= 10)
gen byte in_xi_top10   = (rank_xi <= 10)

qui count if in_base_top10 == 1 & in_xi_top10 == 0
local n_dropped = r(N)
di as txt "Countries in baseline top-10 that fall out of xi top-10: `n_dropped'"

qui count if in_base_top10 == 0 & in_xi_top10 == 1
local n_entered = r(N)
di as txt "Countries entering xi top-10 from outside baseline top-10: `n_entered'"

// Show the movers
if `n_dropped' > 0 {
    di as txt _n "  Dropped from top-10:"
    forvalues i = 1/`N' {
        if in_base_top10[`i'] == 1 & in_xi_top10[`i'] == 0 {
            di as txt "    " iso3[`i'] " (" country[`i'] "): " ///
                "base rank " rank_baseline[`i'] " -> xi rank " rank_xi[`i'] ///
                " (xi=" %4.2f xi_j[`i'] ")"
        }
    }
}

if `n_entered' > 0 {
    di as txt _n "  Entered top-10:"
    forvalues i = 1/`N' {
        if in_base_top10[`i'] == 0 & in_xi_top10[`i'] == 1 {
            di as txt "    " iso3[`i'] " (" country[`i'] "): " ///
                "base rank " rank_baseline[`i'] " -> xi rank " rank_xi[`i'] ///
                " (xi=" %4.2f xi_j[`i'] ")"
        }
    }
}

drop in_base_top10 in_xi_top10

// ─── Save ────────────────────────────────────────────────────────────────────
order iso3 country c_j xi_j c_j_xi rank_baseline rank_xi ///
      governance grid_quality sanctions_adj

compress
save "$output/reliability_rankings.dta", replace

di as txt _n "  Spearman rho = " %6.4f `spearman'
di as txt "  Saved: reliability_rankings.dta"
