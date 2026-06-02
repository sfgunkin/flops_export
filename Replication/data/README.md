# FLOPs Export Paper — Data Repository

Data files for the replication package. The Stata pipeline in `../code/` reads
the analysis-ready CSVs in this folder; the `raw/` subfolder holds the upstream
source extracts. **For the complete Data Availability Statement — source, URL,
access date, citation, and license for every input — see §6 of `../README.md`.**
This file is a quick directory map; the DAS is authoritative.

## Directory Structure

```
data/
├── raw/
│   ├── calibration_results_v3.csv          # Primary calibration: 85 countries
│   ├── electricity/
│   │   ├── eurostat_nrg_pc_205.csv         # Eurostat industrial electricity (band IC)
│   │   ├── eia_average_retail.csv          # EIA average retail, industrial
│   │   └── non_european_prices.csv         # Master: merged non-European prices
│   ├── climate/
│   │   └── era5_peak_summer_temp.csv       # ERA5 peak summer temperature (°C)
│   ├── construction/
│   │   ├── dcci_construction_cost_2025.csv # Turner & Townsend DCCI 2025 ($/W)
│   │   └── predicted_construction_costs.csv# Predicted costs for non-DCCI countries
│   ├── governance/
│   │   ├── wgi_rule_of_law.csv             # WGI Rule of Law percentile
│   │   └── xi_scenarios_data.csv           # G_RoL, R_grid for 85 countries
│   ├── sovereignty/
│   │   └── (hardcoded in script: blocs, EU/CBPR/DEPA, sanctions)
│   ├── latency/
│   │   └── wondernetwork_rtt.csv           # WonderNetwork bilateral RTT (ms)
│   └── capacity/
│       ├── dc_capacity_mw.csv              # Data center capacity (MW) by country
│       └── grid_capacity_estimates.csv     # Grid capacity → K_bar GPU-hours
└── output/
    └── table3_recalculated.xlsx            # Generated output (two sheets)
```

## Sources

| File | Source | Date |
|---|---|---|
| calibration_results_v3.csv | `calibrate_model_v3.py` output | 2025 |
| eurostat_nrg_pc_205.csv | Eurostat NRG_PC_205 dataset | 2024 H2 |
| eia_average_retail.csv | EIA Electric Power Monthly | 2024 |
| non_european_prices.csv | Merged: Eurostat + EIA + Climatescope | 2024-2025 |
| era5_peak_summer_temp.csv | ERA5 reanalysis, peak summer month | 2024 |
| dcci_construction_cost_2025.csv | Turner & Townsend DCCI 2025 | Jan 2025 |
| predicted_construction_costs.csv | OLS on GDP/capita | 2025 |
| wgi_rule_of_law.csv | World Bank WGI | 2023 |
| xi_scenarios_data.csv | Computed from WGI + Enterprise Surveys | 2025 |
| wondernetwork_rtt.csv | WonderNetwork global ping dataset | 2024 |
| dc_capacity_mw.csv | Synergy Research, industry reports | 2024-2025 |
| grid_capacity_estimates.csv | World Bank WDI + IEA | 2023 |

## Key Variables

- `p_E_usd_kwh`: Electricity price ($/kWh, industrial)
- `theta_summer_C`: Peak summer temperature (°C)
- `p_L_usd_per_W`: Data center construction cost ($/W IT load)
- `pue`: Power Usage Effectiveness (computed from θ)
- `G_RoL`: WGI Rule of Law percentile ∈ [0,1]
- `R_grid`: Grid reliability index ∈ [0,1]
- `capacity_mw`: Installed data center capacity (MW)
- `K_bar_gpu_hours`: Grid-constrained GPU capacity (GPU-hr/period)
- `avg_ms`: Average bilateral RTT latency (ms)
