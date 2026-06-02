# Replication Package — *Cheap Energy Might Not Be Enough: A Trade Model of AI Compute Services*

This package reproduces the model calibration and the core quantitative results
of the paper from analysis-ready input data, using a 14-step Stata pipeline
orchestrated by a single master script.

---

## 1. Quick start

1. Install Stata (version **16 or later** recommended; the code uses only base
   Stata — no user-written packages are required).
2. Unzip / copy this `Replication` folder anywhere on your machine.
3. In Stata, change to this folder and run the master script:
   ```stata
   cd "C:/path/to/Replication"
   do run_all.do
   ```
   `run_all.do` auto-detects its location from the working directory. If that is
   inconvenient, hard-code the path on the `global root` line near the top of the
   script.

Expected runtime: a few minutes on a typical laptop. A full transcript is written
to `output/run_all_log.txt`.

---

## 2. What this package reproduces

This is a **Stata-only** package that reproduces **every data table in the
paper** (Tables 1, 2, 3, A1–A8). Steps 01–14 build the core model
(calibration, regimes, capacity equilibrium, inference sourcing, welfare,
sensitivity, reliability, Kyrgyzstan DCF); steps 15–19 add the v33
specifications and export the tables:

- **15** Symmetric-LRMC cost-recovery (Table 3/A2 col 2)
- **16** Host-country WACC channel (Table 3 col 4)
- **17** Bilateral sovereignty premium λ_ij (Table 3/A2 col 3)
- **18** Construction-cost OLS (Table A7)
- **19** Writes all eleven tables to `output/table*.csv`

The constant tables in steps 15–17 (carbon prices/intensities, OECD scope,
cross-subsidies, income-group WACC bands, geopolitical-bloc matrix, EU/APEC/DEPA
membership) are transcribed from the paper's Python generator.

### Fidelity vs. the published tables (per the agreed "qualitative match")

| Published table | Stata reproduction | Status |
|---|---|---|
| Table A1 (calibration params) | full | ✅ matches |
| Table 3/A2 col (1) Raw | observed-price ranking | ✅ matches |
| Table 3/A2 col (2) Symmetric LRMC | top-5 KGZ/ETH/XKX/CAN/TJK; p_T = $1.598 (paper $1.604) | ✅ matches |
| Table 3 col (4) CR + WACC | HIC $1.58 / LIC $1.87 / gap $0.29 | ✅ exact |
| Table A3 (sensitivity) | step 12 scenarios | ⚠️ same method, scenario set differs from paper's |
| Table A5 / A6 (DCF) | NPV $353M / IRR 17.6% / payback Yr 6 | ✅ matches |
| Table A7 (construction OLS) | N=37, R²≈0.48, same regressors | ✅ structure matches (small-N coeffs insignificant) |
| Table 3/A2 col (3) Bilateral | λ_ij matrix + training-side sourcing; HHI_T≈0.58, welfare≈1.7% | ⚠️ **partial** — a training-side proxy; does **not** reproduce the published bilateral welfare (4.7%) / HHI (0.46), which also include the inference side and full deadweight-loss components |
| Tables 1, 2, A4, A8 | definitional/static content | ✅ reproduced as content |

**Caveat on the bilateral column (col 3):** step 17 implements the bilateral
premium and per-buyer *training* sourcing only; the full bilateral equilibrium
(inference hubs + the two-component welfare decomposition) is not ported, so its
headline welfare/HHI differ from the paper. Treat col (3) as indicative.

Notes:
- `data/` holds the **analysis-ready inputs**; upstream construction of a few
  (temperature from raw ERA5, latency from raw pings) was done in Python and is
  not part of this pipeline (raw files are still included — see §5).
- The package reproduces the table **values** as CSV; it does not typeset the
  formatted Word tables or Figure 1 (the model-structure diagram).

---

## 3. Repository layout

```
Replication/
├── README.md            this file
├── run_all.do           master script — sets parameters & runs all 19 steps
├── code/                the Stata pipeline (driven entirely by run_all.do)
│   ├── _solver_program.do        equilibrium solver (loaded first)
│   ├── 01_prep_electricity.do
│   ├── 02_prep_temperature.do
│   ├── 03_prep_construction.do
│   ├── 04_calibrate_costs.do
│   ├── 05_prep_latency.do
│   ├── 06_regime_assignment.do
│   ├── 07_demand_shares.do
│   ├── 08_capacity_equilibrium.do
│   ├── 09_cost_recovery.do
│   ├── 10_inference_sourcing.do
│   ├── 11_welfare_sovereignty.do
│   ├── 12_sensitivity.do
│   ├── 13_reliability.do
│   ├── 14_kyrgyzstan_dcf.do
│   ├── 15_symmetric_lrmc.do        (Table 3/A2 col 2)
│   ├── 16_wacc_channel.do          (Table 3 col 4)
│   ├── 17_bilateral_lambda.do      (Table 3/A2 col 3)
│   ├── 18_construction_regression.do (Table A7)
│   └── 19_export_tables.do         (writes all table*.csv)
├── data/                all input data (see §5)
├── output/              result files + the 11 exported table*.csv; shipped with
│                        REFERENCE results from a validated run, overwritten on re-run
└── temp/                intermediate .dta files (created on each run)
```

All model parameters (GPU price, lifetime, utilization, PUE coefficients,
latency rate `τ`, sovereignty premium `λ`, demand totals, the 13 cost-recovery
prices, and the Kyrgyzstan DCF assumptions) are defined **once** at the top of
`run_all.do` — change them there to explore alternatives.

---

## 4. Pipeline steps and outputs

| Step | Script | Produces | Where it appears in the paper |
|------|--------|----------|-------------------------------|
| 1 | `01_prep_electricity.do` | cleaned electricity prices (`temp/`) | input to cost calibration |
| 2 | `02_prep_temperature.do` | peak summer temperatures (`temp/`) | PUE / cooling term |
| 3 | `03_prep_construction.do` | per-watt construction costs (`temp/`) | construction term in `c_j` |
| 4 | `04_calibrate_costs.do` | **`output/calibration_results_stata.csv`** + `temp/calibration_results.dta` | cost rankings — Table 3 col (1), Tables A1/A2 |
| 5 | `05_prep_latency.do` | symmetric latency matrix (`temp/`) | inference latency cost |
| 6 | `06_regime_assignment.do` | trade-regime types (`temp/`) | regime taxonomy — Table 1 |
| 7 | `07_demand_shares.do` | demand shares `ω_k` (`temp/`) | demand calibration (§3.3) |
| 8 | `08_capacity_equilibrium.do` | training equilibrium `p_T`, `HHI_T`, shadow values (`temp/`) | trade-flow results (§6.2) |
| 9 | `09_cost_recovery.do` | cost-recovery costs/rankings (`temp/`) | Table 3 col (2) — *13-country spec* |
| 10 | `10_inference_sourcing.do` | inference hubs & shares (`temp/`) | inference results (§6.2) |
| 11 | `11_welfare_sovereignty.do` | welfare cost of sovereignty (`temp/`) | welfare results (§6.2 / §7) |
| 12 | `12_sensitivity.do` | **`output/sensitivity_results.dta`** | sensitivity — Appendix C / Table A3 |
| 13 | `13_reliability.do` | **`output/reliability_rankings.dta`** | reliability-adjusted robustness |
| 14 | `14_kyrgyzstan_dcf.do` | **`output/kyrgyzstan_dcf.dta`**, **`output/kyrgyzstan_dcf_sensitivity.dta`** | Kyrgyzstan DCF — Appendix D |
| 15 | `15_symmetric_lrmc.do` | `temp/symmetric_lrmc.dta` | Table 3/A2 col (2) symmetric LRMC; p_T≈$1.60 |
| 16 | `16_wacc_channel.do` | `temp/wacc_channel.dta` | Table 3 col (4) CR + host WACC |
| 17 | `17_bilateral_lambda.do` | `temp/bilateral_lambda.dta` | Table 3/A2 col (3) bilateral λ (training side) |
| 18 | `18_construction_regression.do` | **`output/tableA7_construction_regression.csv`** | Table A7 |
| 19 | `19_export_tables.do` | **`output/table{1,2,3,A1–A8}_*.csv`** | all paper tables (see §2 fidelity table) |

(Steps 1–3 and 5–11 write intermediate `.dta` files to `temp/`; persistent
`output/` files are bolded. Step 19 writes the eleven `table*.csv` files.)

---

## 5. Data inputs

`data/` contains every data file from the project, copied as-is. The Stata
pipeline reads **only the following eight analysis-ready files**:

| File | Used by | Contents |
|------|---------|----------|
| `calibration_results_v3.csv` | 04 | per-country calibration inputs (prices, climate, governance) |
| `country_electricity_prices.csv` | 01 | retail electricity prices ($/kWh) |
| `country_temperatures.csv` | 02 | peak summer temperatures (°C) |
| `predicted_construction_costs.csv` | 03 | per-watt DC construction costs |
| `country_pair_latency.csv` | 05 | bilateral round-trip latency (ms) |
| `dc_capacity_estimates.csv` | 07 | installed data-center capacity (MW) → demand shares |
| `grid_capacity_estimates.csv` | 08 | national grid capacity (MW) → capacity ceilings |
| `reliability_index.csv` | 13 | grid-reliability index |

**Large raw files EXCLUDED from this package** (not read by the Stata pipeline;
they are upstream inputs for the Python preprocessing only): the raw ERA5 climate
grid (`*.nc`, ~110 MB), `wondernetwork_pings.csv.gz` (~49 MB), and
`ripe_atlas_latency.csv` (~37 MB). They were dropped to keep the package small
(~17 MB vs. ~210 MB); the analysis-ready CSVs derived from them
(`country_temperatures.csv`, `country_pair_latency.csv`) ARE included, so the
Stata pipeline runs fully. The raw files remain available in the full project
repository if upstream reconstruction is needed.

**Data sources** (see `data/README.md` for full detail): electricity prices —
GlobalPetrolPrices, Eurostat (nrg_pc_205), EIA; climate — ECMWF ERA5; latency —
WonderNetwork, RIPE Atlas; capacity — Cloudscene / industry estimates;
construction — Turner & Townsend Data Centre Construction Cost Index 2025;
governance — World Bank WGI; macro — World Bank WDI. Some sources are subject to
their providers' terms of use; redistribute accordingly.

---

## 6. Reproducibility notes

- The pipeline is deterministic — no random number generation — so results are
  bit-stable across runs and platforms.
- `run_all.do` recreates `temp/` and `output/` on each run and overwrites prior
  outputs; intermediate `.dta` files in `temp/` can be deleted freely between
  runs.
- No user-written Stata commands (`ssc install`) are required.
- If a step errors, the log at `output/run_all_log.txt` records the exact step
  and message.

---

## 7. Citation

Lokshin, M. (2026). *Cheap Energy Might Not Be Enough: A Trade Model of AI
Compute Services.* Working paper.
