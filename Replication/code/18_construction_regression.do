/*==============================================================================
  18_construction_regression.do — Construction cost OLS (Table A7)

  Reimplements predict_construction_costs.py's OLS:
    ln($/W) = a + b1·ln(GDP_pcap) + b2·ln(pop) + b3·urban_share
              + b4·seismic_high + region dummies

  Estimated on the 52 Turner & Townsend DCCI 2025 markets (averaged to country),
  merged with WB GDP/cap (PPP), population, urban share, seismic zone, region.
  Exports coefficients/SEs to output/tableA7_construction_regression.csv.
==============================================================================*/

clear
set type double

// ── DCCI observed costs (city-level) → map to ISO3 (ASCII-safe via strpos) ────
import delimited "$data/dcci_2025_construction_costs.csv", varnames(1) ///
    encoding("utf-8") clear
gen str3 iso3 = ""
replace iso3 = "JPN" if strpos(market,"Tokyo") | strpos(market,"Osaka")
replace iso3 = "SGP" if strpos(market,"Singapore")
replace iso3 = "CHE" if strpos(market,"Zurich")
replace iso3 = "USA" if strpos(market,"Silicon") | strpos(market,"New Jersey") | ///
    strpos(market,"Chicago") | strpos(market,"North Virginia") | strpos(market,"Portland") | ///
    strpos(market,"Atlanta") | strpos(market,"Phoenix") | strpos(market,"Columbus") | ///
    strpos(market,"Dallas") | strpos(market,"Charlotte")
replace iso3 = "NOR" if strpos(market,"Oslo")
replace iso3 = "NZL" if strpos(market,"Auckland")
replace iso3 = "SWE" if strpos(market,"Stockholm")
replace iso3 = "FIN" if strpos(market,"Helsinki")
replace iso3 = "DNK" if strpos(market,"Copenhagen")
replace iso3 = "GBR" if strpos(market,"London") | strpos(market,"Cardiff")
replace iso3 = "AUT" if strpos(market,"Vienna")
replace iso3 = "DEU" if strpos(market,"Frankfurt") | strpos(market,"Berlin")
replace iso3 = "MYS" if strpos(market,"Kuala")
replace iso3 = "SAU" if strpos(market,"Saudi")
replace iso3 = "IDN" if strpos(market,"Jakarta")
replace iso3 = "FRA" if strpos(market,"Paris") | strpos(market,"Bordeaux")
replace iso3 = "NLD" if strpos(market,"Amsterdam")
replace iso3 = "BRA" if strpos(market,"Paulo")
replace iso3 = "AUS" if strpos(market,"Sydney") | strpos(market,"Melbourne")
replace iso3 = "NGA" if strpos(market,"Lagos")
replace iso3 = "MEX" if strpos(market,"taro")
replace iso3 = "ZAF" if strpos(market,"Cape Town") | strpos(market,"Johannesburg")
replace iso3 = "PRT" if strpos(market,"Lisbon")
replace iso3 = "KOR" if strpos(market,"Seoul")
replace iso3 = "IRL" if strpos(market,"Dublin")
replace iso3 = "ESP" if strpos(market,"Madrid")
replace iso3 = "URY" if strpos(market,"Montevideo")
replace iso3 = "ITA" if strpos(market,"Milan")
replace iso3 = "KEN" if strpos(market,"Nairobi")
replace iso3 = "CAN" if strpos(market,"Toronto")
replace iso3 = "ARE" if strpos(market,"UAE")
replace iso3 = "POL" if strpos(market,"Warsaw")
replace iso3 = "CHL" if strpos(market,"Santiago")
replace iso3 = "GRC" if strpos(market,"Athens")
replace iso3 = "COL" if strpos(market,"Bog")
replace iso3 = "IND" if strpos(market,"Mumbai")
replace iso3 = "CHN" if strpos(market,"Shanghai")

count if iso3 == ""
if r(N) > 0 {
    di as error "  WARNING: `r(N)' unmapped DCCI market(s)"
    list market if iso3 == "", noobs
}

collapse (mean) usd_per_watt, by(iso3)
rename usd_per_watt cost
tempfile dcci
save `dcci'

// ── Merge WB covariates ───────────────────────────────────────────────────────
import delimited "$data/wb_gdp_per_capita_ppp_2023.csv", varnames(1) encoding("utf-8") clear
keep iso3 gdp_pcap_ppp_2023
rename gdp_pcap_ppp_2023 gdp_pcap
tempfile gdp
save `gdp'

import delimited "$data/wb_population_2023.csv", varnames(1) encoding("utf-8") clear
keep iso3 population_2023
rename population_2023 pop
tempfile pop
save `pop'

import delimited "$data/wb_urban_share_2023.csv", varnames(1) encoding("utf-8") clear
keep iso3 urban_share_pct
gen double urban_share = urban_share_pct / 100
keep iso3 urban_share
tempfile urb
save `urb'

import delimited "$data/seismic_zones.csv", varnames(1) encoding("utf-8") clear
keep iso3 seismic_high
tempfile seis
save `seis'

import delimited "$data/wb_country_regions.csv", varnames(1) encoding("utf-8") clear
keep iso3 region
tempfile reg
save `reg'

use `dcci', clear
merge 1:1 iso3 using `gdp', keep(master match) nogen
merge 1:1 iso3 using `pop', keep(master match) nogen
merge 1:1 iso3 using `urb', keep(master match) nogen
merge 1:1 iso3 using `seis', keep(master match) nogen
merge 1:1 iso3 using `reg',  keep(master match) nogen

replace urban_share = 0.5 if missing(urban_share)
replace seismic_high = 0 if missing(seismic_high)
drop if missing(gdp_pcap) | missing(pop) | missing(region)

gen double ln_cost     = ln(cost)
gen double ln_gdp_pcap = ln(gdp_pcap)
gen double ln_pop      = ln(pop)
encode region, gen(region_id)

// Reference category = most common region in the sample (mirrors Python)
qui levelsof region_id, local(rids)
local refreg .
local refn 0
foreach r of local rids {
    qui count if region_id == `r'
    if r(N) > `refn' {
        local refn = r(N)
        local refreg = `r'
    }
}

di as txt _n "=== Table A7: construction cost regression  ln($/W) ==="
regress ln_cost ln_gdp_pcap ln_pop urban_share seismic_high ib`refreg'.region_id

// ── Export coefficients / SEs ─────────────────────────────────────────────────
preserve
clear
local nvars = 5
matrix b = e(b)'
matrix V = e(V)
local rn : rownames b
local k = rowsof(b)
set obs `k'
gen str32 variable = ""
gen double coef = .
gen double se = .
local i = 1
foreach name of local rn {
    qui replace variable = "`name'" in `i'
    qui replace coef = b[`i',1] in `i'
    qui replace se = sqrt(V[`i',`i']) in `i'
    local ++i
}
gen double tstat = coef / se
export delimited using "$output/tableA7_construction_regression.csv", replace
restore

di as txt "  Saved: tableA7_construction_regression.csv  (R2 = " %5.3f e(r2) ", N = " e(N) ")"
