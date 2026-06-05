# Intermediate datasets (reproducibility starting point)

This folder bundles the four **analysis-ready intermediate datasets** that bridge
the raw sources and the Stata pipeline, together with full metadata and
variable-level data dictionaries. They are small, so they are redistributed
directly in the package — the package is therefore self-contained as a
reproducibility starting point, and verification can begin from these
intermediates without retrieving the large raw sources.

| File | Built from (raw) | Generating script |
|---|---|---|
| `country_temperatures.csv` | ERA5 2-m temperature (NetCDF, ~110 MB) | `../preprocessing/process_temperature.py` |
| `country_pair_latency.csv` | WonderNetwork ping table (~49 MB, proprietary) | `../preprocessing/process_latency.py` |
| `predicted_construction_costs.csv` | Turner & Townsend DCCI 2025 + World Bank WDI | `../preprocessing/predict_construction_costs.py` |
| `country_electricity_prices.csv` | Eurostat + EIA + compiled non-European prices | merged (see `../preprocessing/README.md`) |

The large raw sources (ERA5 NetCDF, WonderNetwork ping table, RIPE Atlas) are
**not** redistributed — for size (ERA5 ~110 MB) and license (WonderNetwork raw
pings are proprietary). Their provenance — source, URL, access date, citation,
and license — is documented in the package README's Data Availability Statement
(§6) and in `DDH_metadata.md` / `DDH_upload_metadata.md` in this folder.

## Relationship to `../data/`

These files are **byte-identical copies** of the same four files in
`../data/`, which is where the Stata pipeline actually reads them. This folder is
a labeled, documented archival snapshot intended as the citable starting point;
it is not read by the pipeline. If the intermediates are ever regenerated, refresh
the copies here from `../data/` so the two stay in sync.

## Metadata

- `DDH_metadata.md` — per-dataset provenance (source, URL, access date, citation,
  license) and data dictionaries.
- `DDH_upload_metadata.md` — the same content laid out as form-ready fields for a
  Development Data Hub (DDH) deposit, should external archival also be desired.
