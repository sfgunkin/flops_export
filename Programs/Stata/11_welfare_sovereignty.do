/*==============================================================================
  11_welfare_sovereignty.do — Welfare cost of sovereignty and counterfactuals

  Computes:
    - Welfare cost of full sovereignty (omega-weighted excess cost)
    - Lambda* for each country under cost-recovery
    - Counterfactuals: 10% vs 20% sovereignty premium
  Uses cost-recovery adjusted costs.
  Saves welfare_sovereignty.dta.
==============================================================================*/

clear
set type double

// ─── Load cost-recovery costs and inference sourcing ─────────────────────────
use "$temp/cost_recovery.dta", clear
keep iso3 country c_j omega is_sanctioned

merge 1:1 iso3 using "$temp/inference_sourcing.dta", ///
    keepusing(P_I_domestic best_inf_cost best_inf_source) ///
    keep(match) nogen

qui count
local N = _N

// ─── Lambda* for each country ────────────────────────────────────────────────
// lambda* = c_k / min_foreign_c_j - 1
// Under cost-recovery adjusted costs

// Find min foreign cost (excluding sanctioned)
qui sum c_j if is_sanctioned == 0
local min_foreign = r(min)

gen double lambda_star = c_j / `min_foreign' - 1

// ─── Welfare cost of full sovereignty ────────────────────────────────────────
// Training welfare loss: omega_k * max(0, c_k - min_foreign_train)
// where min_foreign_train = min c_j over non-sanctioned j != k

// For training: best foreign = global cheapest (latency irrelevant)
// For inference: use the inference sourcing results

// Training welfare
gen double welfare_train = omega * max(0, c_j - `min_foreign')

// Inference welfare: excess of domestic inference over best foreign inference
gen double welfare_inf = omega * max(0, P_I_domestic - best_inf_cost)

// Aggregate
qui sum welfare_train
local total_w_train = r(sum)
qui sum welfare_inf
local total_w_inf = r(sum)
local total_welfare = `total_w_train' + `total_w_inf'

// Weighted average cost for normalization
gen double omega_cost = omega * c_j
qui sum omega_cost
local weighted_avg = r(sum)
drop omega_cost

local welfare_pct = `total_welfare' / `weighted_avg' * 100

di as txt _n "=== Welfare Cost of Full Sovereignty ==="
di as txt "  Training welfare loss:  $" %8.4f `total_w_train' "/hr (weighted)"
di as txt "  Inference welfare loss: $" %8.4f `total_w_inf' "/hr (weighted)"
di as txt "  Total welfare loss:     $" %8.4f `total_welfare' "/hr (weighted)"
di as txt "  Weighted avg cost:      $" %8.4f `weighted_avg' "/hr"
di as txt "  Welfare as % of avg:    " %5.1f `welfare_pct' "%"

// ─── Counterfactuals: 10% vs 20% sovereignty ────────────────────────────────
// Count countries that would be domestic under different lambda thresholds
qui count if c_j <= 1.10 * `min_foreign'
local n_dom_10 = r(N)

qui count if c_j <= 1.20 * `min_foreign'
local n_dom_20 = r(N)

local extra_dom = `n_dom_20' - `n_dom_10'

// Export share = omega of countries NOT domestic
gen byte dom_10 = (c_j <= 1.10 * `min_foreign')
gen byte dom_20 = (c_j <= 1.20 * `min_foreign')

gen double omega_export_10 = omega * (1 - dom_10)
gen double omega_export_20 = omega * (1 - dom_20)

qui sum omega_export_10
local export_share_10 = r(sum)
qui sum omega_export_20
local export_share_20 = r(sum)

di as txt _n "=== Sovereignty Counterfactuals ==="
di as txt "  lambda = 10%: `n_dom_10' domestic, export share = " ///
    %5.1f `export_share_10'*100 "%"
di as txt "  lambda = 20%: `n_dom_20' domestic, export share = " ///
    %5.1f `export_share_20'*100 "%"
di as txt "  Additional domestic at 20% vs 10%: `extra_dom'"

// ─── Lambda* distribution ────────────────────────────────────────────────────
di as txt _n "Lambda* distribution (cost-recovery):"
qui sum lambda_star, detail
di as txt "  Min:    " %6.3f r(min)
di as txt "  Median: " %6.3f r(p50)
di as txt "  Mean:   " %6.3f r(mean)
di as txt "  Max:    " %6.3f r(max)

// Countries with lambda* < 0.10 (would be domestic under 10% sovereignty)
qui count if lambda_star <= 0.10
di as txt "  Countries with lambda* <= 10%: " r(N)

// ─── Clean and save ──────────────────────────────────────────────────────────
drop dom_10 dom_20 omega_export_10 omega_export_20

order iso3 country c_j omega lambda_star ///
      welfare_train welfare_inf ///
      P_I_domestic best_inf_cost best_inf_source

compress
save "$temp/welfare_sovereignty.dta", replace

// Store results
global welfare_pct = `welfare_pct'
global welfare_total = `total_welfare'
global n_dom_10 = `n_dom_10'
global n_dom_20 = `n_dom_20'

di as txt "  Saved: welfare_sovereignty.dta"
