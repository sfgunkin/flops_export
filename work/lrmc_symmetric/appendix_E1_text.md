# Appendix E.1 — Symmetric LRMC Construction

## Motivation

The cost-recovery specification in the published version of this paper (v32) adjusts
electricity prices *downward* for thirteen developing countries whose observed tariffs
reflect explicit fossil-fuel subsidies (IMF 2025), replacing subsidised tariffs with
estimated long-run marginal cost (LRMC) of the dominant generation technology at
opportunity-cost fuel prices. No symmetric correction was applied to OECD and high-income
tariffs, which also embed distortions: emissions externalities not priced at the retail
meter, industrial cross-subsidies financed by residential and commercial rate classes,
and remaining regulated-access privileges for incumbents.

The asymmetry biases the cross-country cost spread in favour of OECD economies. In this
revision we construct a *symmetric* LRMC specification that corrects distortions on both
sides: developing-country tariffs adjusted upward to LRMC (as in v32), and OECD/high-income
tariffs adjusted upward by (i) an applicable carbon-price adder reflecting the social cost
of carbon priced through ETS instruments, and (ii) a documented cross-subsidy add-back
where industrial rate classes pay below the cost of service.

## Scope

Of the 85 calibrated countries:

| Treatment | Count | Description |
|---|---:|---|
| `keep_v32_adjusted` | 13 | IMF-based LRMC replacement retained from v32: Iran, Turkmenistan, Algeria, Egypt, Qatar, Saudi Arabia, UAE, Russia, Kazakhstan, Nigeria, South Africa, Ethiopia, Uzbekistan |
| `apply_symmetric_lrmc` | 43 | OECD (37 in sample), EU non-OECD (Bulgaria, Croatia, Cyprus, Malta, Romania), high-income non-OECD (Singapore); observed tariff + carbon adder + cross-subsidy add-back |
| `keep_observed` | 29 | Middle-income developing economies whose observed industrial tariffs already approximate LRMC |

Three countries (Qatar, Saudi Arabia, UAE) appear in both the v32 subsidy set and the
high-income non-OECD set. The IMF treatment dominates for these — no layering of
OECD-style adjustments.

## Carbon-price adder

For each country in `apply_symmetric_lrmc`, the adder is computed as

    carbon_adder = (grid_CI × carbon_price) / 10⁶

where `grid_CI` is the 2024 grid carbon intensity in gCO₂/kWh (EMBER Yearly Electricity
Data 2025 release) and `carbon_price` is the 2024 annual-average settlement or auction
price under the applicable ETS or carbon-tax regime in USD/tCO₂.

Applicable 2024 carbon-price regimes (annual averages, converted at 2024 average FX):

| Regime | Price (USD/tCO₂) | Coverage |
|---|---:|---|
| EU ETS | 70.94 | EU27 + Norway, Iceland, Switzerland (linked) |
| UK ETS | 47.32 | United Kingdom |
| Canadian federal backstop | 58.48 | Canada |
| California CCA + RGGI (weighted) | 3.81 | United States (effective national average) |
| NZ ETS | 39.50 | New Zealand |
| Singapore carbon tax | 18.60 | Singapore |
| Other (Japan, Australia, Israel, Chile, Mexico, Turkey, Colombia, Korea K-ETS) | 0 | Nominal instruments below $10/tCO₂ effective set to zero per protocol |

## Cross-subsidy add-back

Only well-documented, quantified cross-subsidies above $0.005/kWh are included. All other
countries receive a zero add-back on this margin.

| Country | Add-back (USD/kWh) | Source |
|---|---:|---|
| Germany | 0.038 | EEG renewables-surcharge exemption + grid-fee exemption for energy-intensive industry (Agora Energiewende, BDEW) |
| France | 0.015 | Post-ARENH regulated nuclear access (CRE) |
| Spain, Italy, Netherlands, Belgium | 0.010 | Eurostat nrg_pc_205, IB6 band subsidies column |
| United States | 0.015 | Industrial–residential rate differential in excess of cost-of-service (Borenstein 2012; Davis and Hausman 2016) |
| Korea | 0.020 | KEPCO industrial tariffs below cost-of-service (OECD Energy Policy Review) |

## Methodological choices

Three choices warrant note. First, the carbon adder uses 2024 annual-average *prices*, not
the social cost of carbon; using SCC values (USD 190/tCO₂ per EPA 2023) would widen the
OECD adjustment further. Second, we use existing-asset variable cost rather than
replacement-cost capital for OECD nuclear and hydro; a replacement-cost treatment would
raise Norwegian and French LRMCs materially. Third, for Qatar, Saudi Arabia, and UAE, the
IMF-based subsidy adjustment already dominates any OECD-style layering and is retained.

## Largest deltas

The ten largest `|p_E_symmetric − p_E_v32|` changes are in Poland, Germany, Cyprus, USA,
France, Netherlands, Malta, Korea, Spain, and Italy. Poland's +$0.047/kWh carbon adder
(coal-heavy grid × EU ETS) is the largest single-country change from the asymmetric v32
baseline.

## Effect on the headline ranking

Under symmetric LRMC, the top-five cost-recovery producers are Kyrgyzstan, Ethiopia,
Kosovo, Canada, and China (compared with Kyrgyzstan, Canada, Ethiopia, Kosovo, and
Tajikistan under v32). Canada drops from rank 2 to rank 4 on a small ($0.008/kWh) carbon
adder. Poland falls 21 positions, Germany 10, USA 10, France 12. Norway, Finland, and
Sweden move by one or two positions (clean grids, small carbon adders).

The qualitative conclusion is strengthened, not overturned: the countries with cheap,
clean electricity — developing-country hydro (Kyrgyzstan, Ethiopia, Tajikistan) and
Nordic low-carbon grids — retain their cost advantage once both sides of the
distortion are corrected.
