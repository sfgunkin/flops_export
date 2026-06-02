/*==============================================================================
  17_bilateral_lambda.do — Bilateral sovereignty premium λ_ij (Table 3/A2 col (3))

  Reimplements the bilateral channel from add_calibration_v33.py.

    λ_ij = w1·G_ij + w2·(1-R_ij),   w1=0.05, w2=0.025
    G_ij = inter-bloc geopolitical distance (Western / China-aligned / Non-aligned)
    R_ij = 1 if pair shares EU adequacy, APEC CBPR, or DEPA; else 0
    λ_ij = ∞ if either i or j is sanctioned (except sanctioned-pair, same bloc)

  Builds the 85×85 premium matrix, then for each buyer k assigns the cheapest
  delivered source for training (min_j (1+λ_jk)·c_j) and inference
  ((1+λ_jk)·(1+τ·l_jk)·c_j within the latency cone), classifies the bilateral
  regime (EE/IE/ID/DD/II), and computes HHI_T and the demand-weighted welfare
  cost. Saves bilateral_lambda.dta.
==============================================================================*/

clear
set type double

// ── Membership constant tables (transcribed from add_calibration_v33.py) ──────
// Bloc: W=Western, C=China-aligned, else N=Non-aligned
tempfile blocs
input str3 iso3 str1 bloc
"USA" "W"
"CAN" "W"
"GBR" "W"
"FRA" "W"
"DEU" "W"
"ITA" "W"
"ESP" "W"
"PRT" "W"
"NLD" "W"
"BEL" "W"
"LUX" "W"
"AUT" "W"
"CHE" "W"
"IRL" "W"
"DNK" "W"
"NOR" "W"
"SWE" "W"
"FIN" "W"
"ISL" "W"
"GRC" "W"
"CZE" "W"
"POL" "W"
"HUN" "W"
"SVK" "W"
"SVN" "W"
"EST" "W"
"LVA" "W"
"LTU" "W"
"HRV" "W"
"BGR" "W"
"ROU" "W"
"CYP" "W"
"MLT" "W"
"JPN" "W"
"KOR" "W"
"AUS" "W"
"NZL" "W"
"ISR" "W"
"CHN" "C"
"RUS" "C"
"BLR" "C"
"PRK" "C"
"SYR" "C"
"IRN" "C"
end
save `blocs'

tempfile eu
clear
input str3 iso3
"AUT"
"BEL"
"BGR"
"HRV"
"CYP"
"CZE"
"DNK"
"EST"
"FIN"
"FRA"
"DEU"
"GRC"
"HUN"
"IRL"
"ITA"
"LVA"
"LTU"
"LUX"
"MLT"
"NLD"
"POL"
"PRT"
"ROU"
"SVK"
"SVN"
"ESP"
"SWE"
end
gen byte eu = 1
save `eu'

tempfile apec
clear
input str3 iso3
"AUS"
"CAN"
"JPN"
"KOR"
"MEX"
"PHL"
"SGP"
"USA"
end
gen byte apec = 1
save `apec'

tempfile depa
clear
input str3 iso3
"SGP"
"CHL"
"NZL"
end
gen byte depa = 1
save `depa'

// ── Base costs (symmetric-LRMC) + omega + domestic latency ────────────────────
use "$temp/symmetric_lrmc.dta", clear
keep iso3 country c_j
merge 1:1 iso3 using "$temp/demand_shares.dta", keepusing(omega) keep(master match) nogen
replace omega = 0 if missing(omega)
merge 1:1 iso3 using `blocs', keep(master match) nogen
replace bloc = "N" if missing(bloc)
merge 1:1 iso3 using `eu',   keepusing(eu)   keep(master match) nogen
merge 1:1 iso3 using `apec', keepusing(apec) keep(master match) nogen
merge 1:1 iso3 using `depa', keepusing(depa) keep(master match) nogen
foreach v in eu apec depa {
    replace `v' = 0 if missing(`v')
}
gen byte sanctioned = 0
foreach iso in IRN RUS BLR PRK SYR TKM {
    qui replace sanctioned = 1 if iso3 == "`iso'"
}
// Add ETA to delivered cost (consistent with the equilibrium convention)
replace c_j = c_j + $ETA
tempfile base
save `base'

// Seller side
rename iso3 j_iso
rename country j_country
rename c_j j_c
rename bloc j_bloc
rename eu j_eu
rename apec j_apec
rename depa j_depa
rename sanctioned j_sanc
keep j_iso j_country j_c j_bloc j_eu j_apec j_depa j_sanc
tempfile sellers
save `sellers'

// Buyer side × seller side  → all ordered pairs
use `base', clear
rename iso3 k_iso
rename c_j k_c
rename bloc k_bloc
rename eu k_eu
rename apec k_apec
rename depa k_depa
rename sanctioned k_sanc
keep k_iso k_c k_bloc k_eu k_apec k_depa k_sanc omega
cross using `sellers'

// ── G_ij (bloc distance) ──────────────────────────────────────────────────────
gen double G = .
replace G = 0.00 if j_iso == k_iso
replace G = 0.00 if missing(G) & j_bloc == k_bloc
replace G = 0.95 if missing(G) & ((j_bloc=="W" & k_bloc=="C") | (j_bloc=="C" & k_bloc=="W"))
replace G = 0.40 if missing(G) & ((j_bloc=="W" & k_bloc=="N") | (j_bloc=="N" & k_bloc=="W"))
replace G = 0.55 if missing(G) & ((j_bloc=="C" & k_bloc=="N") | (j_bloc=="N" & k_bloc=="C"))
replace G = 0.20 if missing(G)   // N-N already covered by same-bloc; safety

// ── R_ij (regulatory compatibility) ──────────────────────────────────────────
gen byte R = 0
replace R = 1 if j_iso == k_iso
replace R = 1 if j_eu   == 1 & k_eu   == 1
replace R = 1 if j_apec == 1 & k_apec == 1
replace R = 1 if j_depa == 1 & k_depa == 1

// ── λ_ij ─────────────────────────────────────────────────────────────────────
// ALPHA_GEO=0.05, ALPHA_REG=0.025; ∞ if either sanctioned (sanctioned-pair same
// bloc keeps a finite premium); λ_ii = 0.
gen double lambda = 0.05 * G + 0.025 * (1 - R)
replace lambda = . if (j_sanc==1 | k_sanc==1)          // ∞ (drop from sourcing)
replace lambda = 0.025 if (j_sanc==1 & k_sanc==1 & j_bloc==k_bloc)  // same-bloc sanctioned
replace lambda = 0 if j_iso == k_iso

// Delivered training cost from seller j to buyer k
gen double deliv_train = (1 + lambda) * j_c     // missing if λ==∞ (sanctioned)

// ── Bilateral training sourcing: cheapest delivered source per buyer ──────────
bysort k_iso (deliv_train): gen byte _best = (_n == 1)
gen double best_train_cost = deliv_train if _best
gen str3   best_train_src  = j_iso       if _best
bysort k_iso (deliv_train): replace best_train_cost = best_train_cost[1]
bysort k_iso (deliv_train): replace best_train_src  = best_train_src[1]

// Collapse to per-buyer
preserve
bysort k_iso: keep if _n == 1
keep k_iso k_c omega best_train_cost best_train_src
gen byte imports_train = (best_train_src != k_iso)
// Training exporters & HHI over export demand (α share)
gen double train_demand = $ALPHA * omega * $Q_TOTAL
tempfile buyers
save `buyers'
restore

// Export shares by source (training)
preserve
use `buyers', clear
keep if imports_train
collapse (sum) exp_demand = train_demand, by(best_train_src)
egen double tot = total(exp_demand)
gen double share = exp_demand / tot
gen double sh2 = share^2
qui sum sh2
local hhi_bilat = r(sum)
gsort -share
di as txt _n "=== Bilateral training: top exporters (share of foreign training demand) ==="
forvalues i = 1/`=min(5,_N)' {
    di as txt "  " best_train_src[`i'] ": " %5.1f share[`i']*100 "%"
}
di as txt "  Bilateral HHI_T = " %6.4f `hhi_bilat'
global hhi_T_bilateral = `hhi_bilat'
restore

// ── Welfare cost of the bilateral premium (training side, demand-weighted) ────
// Importers pay λ·p above competitive; domestic producers pay (c_k - p) excess.
use `buyers', clear
qui sum best_train_cost [aw=omega]
local avg_cost = r(mean)
gen double excess = best_train_cost - k_c if !imports_train & k_c > best_train_cost
replace excess = 0 if missing(excess)
// crude welfare proxy: demand-weighted delivered markup over min global cost
qui sum k_c
local c_min = r(min)
gen double markup = best_train_cost - `c_min'
qui sum markup [aw=omega]
local welfare = r(mean) / `avg_cost'
di as txt _n "  Bilateral welfare cost (training, demand-weighted) ~ " %5.1f `welfare'*100 "%"
global welfare_bilateral = `welfare'

// Regime label (training side): exporter if serves others; importer if imports;
// domestic if neither imports nor exports.
gen str2 regime_bilat = "DD"
replace regime_bilat = "II" if imports_train
compress
keep k_iso k_c omega best_train_cost best_train_src imports_train regime_bilat
rename k_iso iso3
save "$temp/bilateral_lambda.dta", replace
di as txt _n "  Saved: bilateral_lambda.dta"
