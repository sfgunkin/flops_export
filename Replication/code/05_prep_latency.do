/*==============================================================================
  05_prep_latency.do — Load and symmetrize latency data

  Reads country_pair_latency.csv, symmetrizes (if (A,B) exists but not (B,A),
  copies A→B latency to B→A), saves latency_symmetric.dta.
==============================================================================*/

clear
set type double

import delimited "$data/country_pair_latency.csv", ///
    varnames(1) encoding("utf-8") clear

keep iso3_from iso3_to avg_ms
rename avg_ms latency_ms

qui count
local n_raw = r(N)
di as txt "  Raw latency pairs: `n_raw'"

// ─── Symmetrize ──────────────────────────────────────────────────────────────
// For each (A, B) pair, also ensure (B, A) exists with the same latency
// if it doesn't already have its own measurement.

rename iso3_from from
rename iso3_to   to

tempfile forward
save `forward'

// Create reverse pairs
rename from _to
rename to   from
rename _to  to

tempfile reverse
save `reverse'

// Anti-join: keep reverse pairs not already in forward
use `forward', clear
merge 1:1 from to using `reverse', keep(using) nogen

// Append to forward
append using `forward'

qui count
local n_sym = r(N)
di as txt "  Symmetric latency pairs: `n_sym'"

rename from iso3_from
rename to   iso3_to

compress
save "$temp/latency_symmetric.dta", replace
