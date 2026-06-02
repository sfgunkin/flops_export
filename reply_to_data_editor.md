Subject: Re: Reproducibility package — "Cheap Energy Might Not Be Enough: A Trade Model of AI Compute Services"

Dear [Data Editor],

Thank you for the careful review and for confirming the package runs and is
stable across repeated runs. I have addressed both of your requests and attach
an updated package (`FLOPsExport_Replication.zip`). A summary follows.

1. COMPLETE DATA AVAILABILITY STATEMENT
---------------------------------------
The README now contains a full Data Availability Statement (Section 6,
immediately below the data-sources summary), following the Social Science Data
Editors' guidance. It documents every input dataset with the six requested
fields — filename(s), source, URL, access date, citation, and license —
organized into three groups:

  (A) Externally-sourced data used directly by the pipeline (8 datasets):
      data-centre construction cost index (Turner & Townsend), data-centre
      capacity, national grid capacity, World Bank WGI and WDI, the World Bank
      region classification, the seismic-hazard flag, and the grid-reliability
      index.
  (B) Processed inputs built from raw sources by the scripts in
      `preprocessing/` (temperature from ERA5, latency from WonderNetwork,
      predicted construction costs, and the merged electricity-price file).
  (C) Auxiliary files shipped for completeness but not read by the pipeline.

The data were assembled by the research team in February 2026 (auxiliary files
in April 2026); access dates and the underlying reference periods are recorded
per dataset.

In the interest of full transparency I have labelled explicitly those inputs
that are the authors' own compilations or estimates rather than verbatim
third-party downloads:
  - `dc_capacity_estimates.csv` — largely authors' estimates (data-centre count
    × regional average facility size), with roughly twenty countries anchored to
    published figures from Synergy Research, CBRE, Cushman & Wakefield, Arizton,
    Mordor Intelligence, and the IEA. The basis for each row is recorded in the
    file's own `source` column.
  - `seismic_zones.csv` — a binary high-/low-seismic-hazard indicator coded by
    the authors, consistent with GSHAP/USGS hazard geography (not a single
    downloaded dataset).
  - `reliability_index.csv` — an authors' constructed index combining the World
    Bank WGI governance percentile with an authors-assigned grid-quality score.
  - `country_electricity_prices.csv` — a merge of Eurostat (European countries),
    EIA (United States), and a manual compilation for about twenty
    non-European/non-EIA countries from GlobalPetrolPrices, national regulators,
    and the IEA; the per-row provenance is in the file's `source` column.

2. SCRIPTS THAT GENERATE THE PROCESSED INPUTS
---------------------------------------------
You are quite right that `country_temperatures.csv` and
`country_pair_latency.csv` are processed datasets. The generating scripts are
now included in `Replication/preprocessing/`, made path-portable and documented
(with a folder README):

  - `process_temperature.py`  — builds `country_temperatures.csv` from the raw
    ERA5 2-m temperature reanalysis (NetCDF) and Natural Earth boundaries.
  - `process_latency.py`      — builds `country_pair_latency.csv` from the raw
    WonderNetwork ping measurements and server directory.
  - `predict_construction_costs.py` — included as well for transparency; it
    regenerates `predicted_construction_costs.csv` byte-for-byte from the
    shipped inputs.

Two notes for reproducibility:
  - The temperature and latency scripts rely on large raw source files (the
    ~110 MB ERA5 NetCDF and the ~49 MB WonderNetwork ping table) that are not
    redistributed in the package; each script exits with a clear message naming
    the file and where to place it. The analysis-ready CSVs they produce are
    shipped, so the Stata pipeline runs without these raw files.
  - The electricity-price file is a merge (Eurostat + EIA + the manual
    non-European compilation) rather than the output of a single script, so it
    is documented in the DAS instead. The Eurostat/EIA cleaning logic is
    available in the full project repository.

One clarification: an earlier draft of the README mentioned RIPE Atlas as a
latency source. The latency input is in fact derived solely from WonderNetwork;
the DAS reflects this.

3. PROPRIETARY-SOURCE REDISTRIBUTION
------------------------------------
Three sources are proprietary and are handled conservatively: the Turner &
Townsend Data Centre Cost Index and the industry capacity figures are
transcribed/anchor values cited to their reports; for WonderNetwork only the
aggregated country-pair averages are shipped (the raw ping table is excluded);
and GlobalPetrolPrices values are cited per row rather than redistributed in
bulk. I am happy to adjust any of these to suit the repository's policy.

Please let me know if you would like anything presented differently or in a
particular template. Thank you again for your work in preparing the package for
the repository.

Best regards,
Michael Lokshin
