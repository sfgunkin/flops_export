/*==============================================================================
  08_capacity_equilibrium.do — Capacity-constrained training equilibrium

  Builds supply stack from grid capacity estimates, adds ETA networking cost,
  runs the iterative solver to find market-clearing training price p_T,
  computes exporter shares and shadow values.
  Saves capacity_equilibrium.dta.
==============================================================================*/

clear
set type double

// ─── Load grid capacity (K_bar) ──────────────────────────────────────────────
import delimited "$data/grid_capacity_estimates.csv", ///
    varnames(1) encoding("utf-8") clear

keep iso3 k_bar_gpu_hours
rename k_bar_gpu_hours k_bar_raw

// Apply scale correction
gen double k_bar_j = k_bar_raw * $K_BAR_SCALE

keep iso3 k_bar_j
tempfile kbar
save `kbar'

// ─── Load demand shares and costs ────────────────────────────────────────────
use "$temp/demand_shares.dta", clear

// Add ETA (networking cost) to c_j_total for capacity model
// In the Python code: costs_dict[iso] = float(row["c_j_total"]) + ETA
gen double c_j = c_j_total + $ETA

// Merge K_bar
merge 1:1 iso3 using `kbar', keep(match) nogen

// Sanction flag
gen byte is_sanctioned = 0
foreach iso of global SANCTIONED {
    qui replace is_sanctioned = 1 if iso3 == "`iso'"
}

// ─── Run solver: lambda = 0 (pure cost minimization) ─────────────────────────
di as txt _n "=== Capacity-constrained equilibrium (lambda=0) ==="

sort c_j
solve_equilibrium, lambda(0)

local p_T_0     = r(p_T)
local n_exp_0   = r(n_exporters)
local hhi_T_0   = r(hhi_T)

// Save results
gen double p_T_lambda0 = `p_T_0'
gen double lambda_star = c_j / `p_T_0' - 1

// Save exporter details
rename exporter_share exporter_share_lam0
rename shadow_value   shadow_value_lam0
rename is_exporter    is_exporter_lam0

// ─── Run solver: lambda = LAMBDA (with sovereignty) ──────────────────────────
di as txt _n "=== Capacity-constrained equilibrium (lambda=$LAMBDA) ==="

// Rerun solver — need fresh share/shadow vars
cap drop exporter_share shadow_value is_exporter

sort c_j
solve_equilibrium, lambda($LAMBDA)

local p_T_sov   = r(p_T)
local n_exp_sov = r(n_exporters)
local hhi_T_sov = r(hhi_T)

gen double p_T_sovereign = `p_T_sov'
rename exporter_share exporter_share_sov
rename shadow_value   shadow_value_sov
rename is_exporter    is_exporter_sov

// ─── Summary ─────────────────────────────────────────────────────────────────
di as txt _n "=== Summary ==="
di as txt "  Pure cost (lambda=0):"
di as txt "    p_T = $" %9.3f `p_T_0' "/hr"
di as txt "    Exporters: `n_exp_0'"
di as txt "    HHI_T = " %6.4f `hhi_T_0'
di as txt ""
di as txt "  With sovereignty (lambda=$LAMBDA):"
di as txt "    p_T = $" %9.3f `p_T_sov' "/hr"
di as txt "    Exporters: `n_exp_sov'"
di as txt "    HHI_T = " %6.4f `hhi_T_sov'

// Display shadow values
di as txt _n "  Shadow values (mu_j = p_T - c_j, constrained exporters, lambda=0):"
gsort -shadow_value_lam0
forvalues i = 1/5 {
    if shadow_value_lam0[`i'] > 0 {
        di as txt "    " iso3[`i'] " (" country[`i'] "): mu = $" ///
            %6.3f shadow_value_lam0[`i'] "/hr"
    }
}

// ─── Save ────────────────────────────────────────────────────────────────────
order iso3 country c_j c_j_total omega k_bar_j is_sanctioned ///
      p_T_lambda0 lambda_star exporter_share_lam0 shadow_value_lam0 ///
      is_exporter_lam0 p_T_sovereign exporter_share_sov shadow_value_sov ///
      is_exporter_sov

compress
save "$temp/capacity_equilibrium.dta", replace

// Store p_T values as globals for downstream scripts
global p_T_pure = `p_T_0'
global p_T_sov  = `p_T_sov'
global hhi_T_pure = `hhi_T_0'
global hhi_T_sov  = `hhi_T_sov'

di as txt "  Saved: capacity_equilibrium.dta"
