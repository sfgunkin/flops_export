# Development Data Hub (DDH) archival metadata

**Study:** *Cheap Energy Might Not Be Enough: A Trade Model of AI Compute Services* (Lokshin, 2026)

**Purpose of this archive.** These four CSVs are the analysis-ready *processed
inputs* prepared upstream of the Stata replication pipeline. Archiving them in a
stable repository gives the pipeline a citable starting point, so reproducibility
verification can begin from the Stata component. The preprocessing scripts that
build them from raw sources are included in the replication package
(`Replication/preprocessing/`) for transparency; full source/URL/access-date/
license provenance is in the package README's Data Availability Statement (§6).

Two of these files (`country_temperatures.csv`, `country_pair_latency.csv`) are
the reason this archive is needed: their raw sources are not redistributed in the
package — ERA5 because of size (~110 MB), and the WonderNetwork ping table
because it is proprietary (redistribution not permitted). The other two
(`predicted_construction_costs.csv`, `country_electricity_prices.csv`) are also
included for completeness; their raw inputs are already shipped in the package
and they remain reproducible from it.

Suggested DDH collection title: *AI Compute Trade Model — Processed Calibration
Inputs*. Geographic coverage: global (country level, ISO3). Reference period:
2023–2025 (see per-dataset notes). License: see each dataset.

---

## 1. `country_temperatures.csv`  (175 rows)

- **Description:** Country-level annual-mean and warmest-month ("summer peak")
  2-metre air temperature, area-weighted (cos-latitude) over populated grid cells.
- **Built by:** `preprocessing/process_temperature.py`
- **Raw source:** ECMWF Copernicus Climate Change Service (C3S), ERA5 monthly
  averaged 2-m temperature (2020–2024). Country boundaries: Natural Earth 1:110m.
- **Source URL:** https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means
- **Access date:** February 2026
- **Citation:** Hersbach, H., et al. (2023). *ERA5 monthly averaged data on single
  levels from 1940 to present.* C3S Climate Data Store. DOI: 10.24381/cds.f17050d7.
- **License:** Copernicus Licence (free reuse and redistribution with attribution).
- **Variables:**
  | column | type | description |
  |---|---|---|
  | `iso3` | str | ISO-3166 alpha-3 country code |
  | `country` | str | country name (Natural Earth) |
  | `temp_annual_C` | float | annual mean 2-m temperature (°C) |
  | `temp_summer_peak_C` | float | warmest-month mean 2-m temperature (°C) |
  | `n_grid_cells` | int | number of 1° grid cells averaged for the country |

## 2. `country_pair_latency.csv`  (7,749 rows)

- **Description:** Bilateral (ordered country-pair) network round-trip-time
  statistics aggregated from server-to-server ping measurements.
- **Built by:** `preprocessing/process_latency.py`
- **Raw source:** WonderNetwork, *Global Ping Statistics* (server directory +
  raw ping table). The raw ping table is **proprietary and not redistributed**;
  this archive contains only the **aggregated** country-pair averages.
- **Source URL:** https://wondernetwork.com/pings
- **Access date:** February 2026
- **Citation:** WonderNetwork. *Global Ping Statistics* [data set]. https://wondernetwork.com/pings
- **License:** Derived/aggregated statistics released with the replication
  package; underlying raw measurements are proprietary to WonderNetwork (not
  redistributed). Confirm aggregate redistribution terms with the provider before
  publication if required.
- **Variables:**
  | column | type | description |
  |---|---|---|
  | `iso3_from`, `iso3_to` | str | origin / destination ISO3 |
  | `country_from`, `country_to` | str | origin / destination names |
  | `avg_ms`, `median_ms`, `min_ms`, `p95_ms`, `max_ms` | float | RTT statistics (ms) |
  | `n_pings` | int | number of valid measurements for the pair |

## 3. `predicted_construction_costs.csv`  (197 rows)

- **Description:** Per-country data-centre construction cost (US$/watt of IT load),
  predicted from a log-linear regression on observed markets; `source` flags
  observed (DCCI) vs predicted rows.
- **Built by:** `preprocessing/predict_construction_costs.py` (reproduces this
  file byte-for-byte from inputs already in the package).
- **Raw source:** Turner & Townsend *Data Centre Cost Index 2025* + World Bank
  World Development Indicators (GDP per capita PPP, population, urban share) +
  seismic-hazard flag.
- **Source URL:** https://www.turnerandtownsend.com/en/perspectives/data-centre-cost-index/ ; https://databank.worldbank.org/source/world-development-indicators
- **Access date:** February 2026
- **Citation:** Authors' calculation from Turner & Townsend (2025) and World Bank WDI.
- **License:** Derived dataset; World Bank inputs CC BY 4.0, DCCI figures proprietary (transcribed).
- **Variables:**
  | column | type | description |
  |---|---|---|
  | `iso3`, `country`, `region` | str | country identifiers and World Bank region |
  | `gdp_pcap_ppp` | float | GDP per capita, PPP (WDI, 2023) |
  | `population` | int | population, total (WDI, 2023) |
  | `predicted_usd_per_watt` | float | predicted construction cost (US$/W) |
  | `actual_usd_per_watt` | float | observed DCCI cost where available (else blank) |
  | `source` | str | `DCCI` (observed) or `predicted` |

## 4. `country_electricity_prices.csv`  (62 rows)

- **Description:** Country-level industrial electricity price (USD and EUR per
  kWh, tax-excluded large-industrial basis), merged from three streams.
- **Built by:** Eurostat + EIA cleaning (`Programs/process_electricity.py`)
  merged with a manual non-European compilation; the merged master is shipped
  (see package README §6 / `preprocessing/README.md`).
- **Raw source:** (i) Eurostat `nrg_pc_205`; (ii) U.S. EIA electricity data;
  (iii) authors' compilation for ~20 non-European countries from
  GlobalPetrolPrices, national regulators, and the IEA (per-row `source` column).
- **Source URL:** https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/ ; https://www.eia.gov/electricity/data.php ; https://www.globalpetrolprices.com/electricity_prices/
- **Access date:** February 2026 (Eurostat ref. 2024 H2; EIA ref. 2024; GlobalPetrolPrices 2024–2025)
- **Citation:** Eurostat *nrg_pc_205*; U.S. EIA electricity data; authors' compilation.
- **License:** Eurostat free reuse (Commission Decision 2011/833/EU); EIA public
  domain; GlobalPetrolPrices proprietary (cited per row).
- **Variables:**
  | column | type | description |
  |---|---|---|
  | `iso3` | str | ISO3 country code |
  | `price_eur_kwh`, `price_usd_kwh` | float | industrial electricity price (EUR / USD per kWh) |
  | `consumption_band` | str | Eurostat band used, or `research`/`national_industrial` |
  | `source` | str | provider/basis for the row |
