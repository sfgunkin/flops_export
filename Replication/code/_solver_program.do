/*==============================================================================
  _solver_program.do — Reusable capacity-constrained equilibrium solver

  Defines `solve_equilibrium` (called directly by 12) and the thin wrapper
  `solve_tagged` (used by 08 and 09 to run the solver and suffix-tag its outputs).

  Input dataset (in memory): one obs per country, sorted by cost ascending.
    Required variables: iso3 (str), c_j (double), k_bar_j (double),
                        omega (double), is_sanctioned (byte)

  Globals used: $ALPHA, $Q_TOTAL

  Returns via r():
    r(p_T)          — market-clearing training price
    r(n_exporters)   — number of active exporters
    r(hhi_T)         — Herfindahl-Hirschman Index for training
    r(Q_TX)          — total exported training demand (GPU-hours)

  Also creates variables in dataset:
    exporter_share   — share of training exports (0 if not exporting)
    shadow_value     — mu_j = p_T - c_j for capacity-constrained exporters
    is_exporter      — 1 if country exports training
==============================================================================*/

cap program drop solve_equilibrium
program define solve_equilibrium, rclass
    version 17
    syntax , LAMbda(real)

    // Ensure sorted by c_j
    sort c_j

    // Initialize
    local p_T = c_j[1]
    local converged = 0
    local N = _N

    // Iterative solver: find p_T such that supply = demand
    forvalues iter = 1/30 {
        // Compute total training export demand at current p_T
        // Countries import training if their cost > (1 + lambda) * p_T
        local Q_TX = 0
        forvalues i = 1/`N' {
            local c_k = c_j[`i']
            local om  = omega[`i']
            if `c_k' > (1 + `lambda') * `p_T' {
                local Q_TX = `Q_TX' + $ALPHA * `om' * $Q_TOTAL
            }
        }

        // Walk up supply stack until cumulative capacity >= Q_TX
        local cum_cap = 0
        local found = 0
        local p_T_new = `p_T'
        forvalues i = 1/`N' {
            if is_sanctioned[`i'] == 1 {
                continue
            }
            local k_j = k_bar_j[`i']
            local cum_cap = `cum_cap' + `k_j' * $ALPHA
            if `cum_cap' >= `Q_TX' & `Q_TX' > 0 {
                local p_T_new = c_j[`i']
                local found = 1
                continue, break
            }
        }

        // Check convergence
        if `found' == 1 & abs(`p_T_new' - `p_T') < 0.0001 {
            local p_T = `p_T_new'
            local converged = 1
            continue, break
        }
        if `found' == 1 {
            local p_T = `p_T_new'
        }
    }

    // Compute exporter shares, shadow values
    // Drop by EXACT name only: with varabbrev on (Stata default), a bare
    // "cap drop shadow_value" would abbreviation-match and silently delete a
    // previously-renamed "shadow_value_lam0" left by an earlier solver call.
    local _va = c(varabbrev)
    set varabbrev off
    cap drop exporter_share shadow_value is_exporter
    set varabbrev `_va'
    gen double exporter_share = 0
    gen double shadow_value = 0
    gen byte   is_exporter = 0

    local remaining = `Q_TX'
    local n_exp = 0
    forvalues i = 1/`N' {
        if is_sanctioned[`i'] == 1 {
            continue
        }
        if c_j[`i'] > `p_T' {
            continue, break
        }
        local k_j = k_bar_j[`i']
        local ca = min(`k_j' * $ALPHA, `remaining')
        if `ca' > 0 {
            qui replace exporter_share = `ca' in `i'
            qui replace is_exporter = 1 in `i'
            local remaining = `remaining' - `ca'
            local n_exp = `n_exp' + 1
        }
        if `remaining' <= 0 {
            continue, break
        }
    }

    // Normalize shares and compute HHI
    qui sum exporter_share
    local total_exp = r(sum)
    if `total_exp' > 0 {
        qui replace exporter_share = exporter_share / `total_exp'
    }

    // HHI
    tempvar share_sq
    qui gen double `share_sq' = exporter_share^2
    qui sum `share_sq'
    local hhi_T = r(sum)

    // Shadow values: mu_j = p_T - c_j for capacity-constrained exporters
    forvalues i = 1/`N' {
        if is_sanctioned[`i'] == 1 {
            continue
        }
        if c_j[`i'] < `p_T' & is_exporter[`i'] == 1 {
            // Check if capacity-constrained (allocated ~= capacity)
            local allocated = exporter_share[`i'] * `total_exp'
            local k_j = k_bar_j[`i']
            if `allocated' >= `k_j' * $ALPHA * 0.99 {
                qui replace shadow_value = `p_T' - c_j[`i'] in `i'
            }
        }
    }

    // Return results
    return scalar p_T = `p_T'
    return scalar n_exporters = `n_exp'
    return scalar hhi_T = `hhi_T'
    return scalar Q_TX = `Q_TX'
    return scalar converged = `converged'

    di as txt "  p_T = $" %9.4f `p_T' "/hr, " ///
              `n_exp' " exporters, HHI_T = " %6.4f `hhi_T'
end


/*------------------------------------------------------------------------------
  solve_tagged — run solve_equilibrium and tag its three output variables with
  a caller-supplied suffix in one step.

  Replaces the repeated "solve_equilibrium / rename exporter_share .../ rename
  shadow_value .../ rename is_exporter ..." boilerplate in 08 and 09. Forwards
  the solver's r() scalars unchanged.

      solve_tagged, lambda(0)       suffix(_lam0)
      solve_tagged, lambda($LAMBDA) suffix(_sov)

  Produces: exporter_share`suffix', shadow_value`suffix', is_exporter`suffix'.
  The drop of any pre-existing same-suffix vars is exact-name only (varabbrev
  is forced off locally) so it can never abbreviation-match a different suffix.
------------------------------------------------------------------------------*/
cap program drop solve_tagged
program define solve_tagged, rclass
    version 17
    syntax , LAMbda(real) SUFfix(name)

    sort c_j
    solve_equilibrium, lambda(`lambda')

    // Forward the solver's return scalars unchanged
    return scalar p_T         = r(p_T)
    return scalar n_exporters = r(n_exporters)
    return scalar hhi_T       = r(hhi_T)
    return scalar Q_TX        = r(Q_TX)
    return scalar converged   = r(converged)

    // Tag the three output variables with `suffix' (exact-name drop only)
    local _va = c(varabbrev)
    set varabbrev off
    cap drop exporter_share`suffix' shadow_value`suffix' is_exporter`suffix'
    set varabbrev `_va'
    rename exporter_share exporter_share`suffix'
    rename shadow_value   shadow_value`suffix'
    rename is_exporter    is_exporter`suffix'
end
