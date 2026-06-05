# DDH upload metadata (form-ready)

Field-by-field metadata for depositing the processed calibration inputs in the
World Bank **Development Data Hub (DDH)**. Each block below maps onto the DDH
submission form: a **Collection / Dataset** level and, for each file, a
**Resource** level with a variable-level data dictionary. Values marked
`[confirm]` are administrative fields only the depositor can set.

General provenance, sources, URLs, access dates, and licenses are in
`DDH_metadata.md` (this file is the form-entry companion).

---

## COLLECTION-LEVEL METADATA

| Field | Value |
|---|---|
| **Collection title** | AI Compute Trade Model — Processed Calibration Inputs |
| **Description / Abstract** | Analysis-ready, country-level processed inputs used to calibrate the trade model in *Cheap Energy Might Not Be Enough: A Trade Model of AI Compute Services* (Lokshin, 2026). The collection provides a stable, citable starting point for the paper's Stata replication pipeline: four CSV resources covering electricity prices, peak/annual temperature, data-center construction costs, and bilateral network latency. The Python scripts that build these files from raw sources, and a full Data Availability Statement, are included in the paper's replication package. |
| **Collection type** | Tabular / Statistical (derived data) |
| **Author / Creator** | Michael Lokshin (World Bank) |
| **Contact** | Michael Lokshin — `[confirm WB email / UPI]` |
| **Publisher** | World Bank |
| **Geographic coverage** | Global (country level, ISO-3166 alpha-3) |
| **Time coverage** | 2023–2025 (varies by resource; see each) |
| **Language** | English |
| **Access classification** | Public Use `[confirm with DDH curator]` |
| **License** | Mixed by resource (see each); collection released under Creative Commons Attribution 4.0 (CC BY 4.0) except where an underlying proprietary source requires a more restrictive note. |
| **Topics / Tags** | data centers; artificial intelligence; compute; electricity prices; cloud computing; trade in services; network latency; construction costs |
| **Related research** | Lokshin, M. (2026). *Cheap Energy Might Not Be Enough: A Trade Model of AI Compute Services.* (working paper; replication package available) |
| **Version** | 1.0 |
| **Reference date** | 2026-02 (data assembled) |
| **Citation (collection)** | Lokshin, M. (2026). *AI Compute Trade Model — Processed Calibration Inputs* [data set]. World Bank Development Data Hub. `[DOI to be minted]` |

---

## RESOURCE 1 — `country_temperatures.csv`

| Field | Value |
|---|---|
| **Resource title** | Country-level annual and peak temperature (ERA5-derived) |
| **Description** | Annual-mean and warmest-month ("summer peak") 2-metre air temperature by country, area-weighted (cos-latitude) over populated 1° grid cells. Used to parameterize data-center cooling/PUE. |
| **File format** | CSV (UTF-8) |
| **Records** | 175 countries/territories |
| **Variables** | 5 |
| **Unit of observation** | Country (ISO3) |
| **Geographic coverage** | Global |
| **Time coverage** | ERA5 monthly means, 2020–2024 (averaged) |
| **Source** | ECMWF Copernicus Climate Change Service (C3S), ERA5; boundaries: Natural Earth 1:110m |
| **Source URL** | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means |
| **Access date** | February 2026 |
| **Methodology** | `process_temperature.py`: average ERA5 t2m over 2020–2024, take warmest-month mean per cell, downsample to 1°, spatial-join cell centroids to Natural Earth countries, compute cos-latitude weighted means. |
| **License** | Copernicus Licence (free reuse and redistribution with attribution); derived product released CC BY 4.0. |
| **Access classification** | Public Use |
| **Citation** | Hersbach, H., et al. (2023). *ERA5 monthly averaged data on single levels from 1940 to present.* C3S Climate Data Store. DOI: 10.24381/cds.f17050d7. |

**Data dictionary**

| Variable | Label | Type | Units | Definition |
|---|---|---|---|---|
| `iso3` | Country code | string | — | ISO-3166 alpha-3 |
| `country` | Country name | string | — | Natural Earth country name |
| `temp_annual_C` | Annual mean temperature | numeric | °C | Area-weighted annual mean 2-m temperature, 2020–2024 |
| `temp_summer_peak_C` | Peak-month temperature | numeric | °C | Area-weighted warmest-month mean 2-m temperature |
| `n_grid_cells` | Grid-cell count | integer | count | Number of 1° grid cells averaged for the country |

---

## RESOURCE 2 — `country_pair_latency.csv`

| Field | Value |
|---|---|
| **Resource title** | Bilateral network latency, country-pair averages (WonderNetwork-derived) |
| **Description** | Ordered country-pair round-trip-time (RTT) statistics aggregated from server-to-server ping measurements. Used to parameterize the inference latency cost. Contains aggregated statistics only; the raw ping table is proprietary and not included. |
| **File format** | CSV (UTF-8) |
| **Records** | 7,749 ordered country pairs |
| **Variables** | 10 |
| **Unit of observation** | Ordered country pair (origin → destination) |
| **Geographic coverage** | Global (countries with measured servers) |
| **Time coverage** | 2026 measurement snapshot |
| **Source** | WonderNetwork, *Global Ping Statistics* |
| **Source URL** | https://wondernetwork.com/pings |
| **Access date** | February 2026 |
| **Methodology** | `process_latency.py`: map each WonderNetwork server to a country, stream the raw ping table, filter implausible values (≤0 or >2000 ms), aggregate RTT by ordered country pair (mean/median/min/p95/max + count). |
| **License** | Aggregated/derived statistics released for replication; underlying raw measurements are proprietary to WonderNetwork (not redistributed). `[confirm aggregate redistribution terms with provider if required]` |
| **Access classification** | Public Use (aggregated) `[confirm]` |
| **Citation** | WonderNetwork. *Global Ping Statistics* [data set]. https://wondernetwork.com/pings |

**Data dictionary**

| Variable | Label | Type | Units | Definition |
|---|---|---|---|---|
| `iso3_from` | Origin code | string | — | ISO3 of measuring (origin) server's country |
| `iso3_to` | Destination code | string | — | ISO3 of target (destination) server's country |
| `country_from` | Origin country | string | — | Origin country name |
| `country_to` | Destination country | string | — | Destination country name |
| `avg_ms` | Mean RTT | numeric | milliseconds | Mean round-trip time over valid pings |
| `median_ms` | Median RTT | numeric | milliseconds | Median round-trip time |
| `min_ms` | Minimum RTT | numeric | milliseconds | Minimum round-trip time |
| `p95_ms` | 95th-percentile RTT | numeric | milliseconds | 95th percentile round-trip time |
| `max_ms` | Maximum RTT | numeric | milliseconds | Maximum round-trip time |
| `n_pings` | Measurement count | integer | count | Number of valid pings for the pair |

---

## RESOURCE 3 — `predicted_construction_costs.csv`

| Field | Value |
|---|---|
| **Resource title** | Data-center construction cost per watt, observed and predicted |
| **Description** | Per-country data-center construction cost (US$ per watt of IT load): observed values for markets in the Turner & Townsend index, and out-of-sample predictions from a log-linear regression for the remaining countries. |
| **File format** | CSV (UTF-8) |
| **Records** | 197 countries |
| **Variables** | 8 |
| **Unit of observation** | Country (ISO3) |
| **Geographic coverage** | Global |
| **Time coverage** | DCCI 2025; World Bank covariates 2023 |
| **Source** | Turner & Townsend *Data Centre Cost Index 2025*; World Bank World Development Indicators; seismic-hazard flag |
| **Source URL** | https://www.turnerandtownsend.com/en/perspectives/data-centre-cost-index/ ; https://databank.worldbank.org/source/world-development-indicators |
| **Access date** | February 2026 |
| **Methodology** | `predict_construction_costs.py`: OLS of ln($/W) on ln(GDP per capita), ln(population), urban share, seismic flag, and region dummies, trained on 37 observed markets; Duan smearing applied for level prediction. Reproduces the shipped file byte-for-byte. |
| **License** | Derived dataset; World Bank inputs CC BY 4.0; Turner & Townsend figures proprietary (transcribed for observed markets). |
| **Access classification** | Public Use |
| **Citation** | Authors' calculation from Turner & Townsend (2025), *Data Centre Cost Index 2025*, and World Bank, *World Development Indicators*. |

**Data dictionary**

| Variable | Label | Type | Units | Definition |
|---|---|---|---|---|
| `iso3` | Country code | string | — | ISO-3166 alpha-3 |
| `country` | Country name | string | — | World Bank country name |
| `region` | World Bank region | string | — | WB region classification |
| `gdp_pcap_ppp` | GDP per capita, PPP | numeric | current intl $ | WDI NY.GDP.PCAP.PP.CD, 2023 |
| `population` | Population, total | integer | persons | WDI SP.POP.TOTL, 2023 |
| `predicted_usd_per_watt` | Predicted construction cost | numeric | US$/W | Regression-predicted cost per watt of IT load |
| `actual_usd_per_watt` | Observed construction cost | numeric | US$/W | DCCI observed cost where available (blank otherwise) |
| `source` | Value source | string | — | `DCCI` (observed) or `predicted` |

---

## RESOURCE 4 — `country_electricity_prices.csv`

| Field | Value |
|---|---|
| **Resource title** | Industrial electricity prices by country (merged) |
| **Description** | Country-level industrial electricity price (USD and EUR per kWh), on a large-industrial, tax-excluded basis, merged from Eurostat (Europe), EIA (United States), and a compiled set of non-European/non-EIA countries. Per-row provenance is recorded in the `source` column. |
| **File format** | CSV (UTF-8) |
| **Records** | 62 countries |
| **Variables** | 5 |
| **Unit of observation** | Country (ISO3) |
| **Geographic coverage** | Global (priced countries) |
| **Time coverage** | Eurostat 2024 H2; EIA 2024; compiled non-European 2024–2025 |
| **Source** | Eurostat `nrg_pc_205`; U.S. Energy Information Administration; authors' compilation from GlobalPetrolPrices, national regulators, and the IEA |
| **Source URL** | https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/ ; https://www.eia.gov/electricity/data.php ; https://www.globalpetrolprices.com/electricity_prices/ |
| **Access date** | February 2026 |
| **Methodology** | Eurostat large-industrial band (tax-excluded, EUR) and EIA industrial retail prices cleaned and converted to USD; merged with a manually compiled set of non-European prices (rows tagged `research`); see `preprocessing/README.md`. |
| **License** | Eurostat: free reuse with acknowledgement (Commission Decision 2011/833/EU); EIA: U.S. Government work (public domain); GlobalPetrolPrices: proprietary (cited per row, not redistributed in bulk). |
| **Access classification** | Public Use |
| **Citation** | Eurostat, *Electricity prices for non-household consumers* [nrg_pc_205]; U.S. EIA, *Electricity data*; authors' compilation. |

**Data dictionary**

| Variable | Label | Type | Units | Definition |
|---|---|---|---|---|
| `iso3` | Country code | string | — | ISO-3166 alpha-3 |
| `price_eur_kwh` | Electricity price (EUR) | numeric | EUR/kWh | Industrial electricity price, tax-excluded |
| `price_usd_kwh` | Electricity price (USD) | numeric | US$/kWh | Industrial electricity price, tax-excluded |
| `consumption_band` | Consumption band / basis | string | — | Eurostat band, `national_industrial`, or `research` |
| `source` | Value source | string | — | Provider/basis for the row (e.g., Eurostat, EIA, GlobalPetrolPrices) |

---

## Administrative checklist (depositor to complete in DDH)

- [ ] Confirm **contact** (WB email / UPI) for the collection.
- [ ] Confirm **access classification** for each resource (default Public Use; the latency aggregate may need curator sign-off given the proprietary raw source).
- [ ] Confirm **WonderNetwork** aggregate-redistribution terms (Resource 2) before publication.
- [ ] Select the DDH **collection/program** the deposit belongs to.
- [ ] After the DOI is minted, add the collection citation to the replication-package README and to `DDH_metadata.md`.
