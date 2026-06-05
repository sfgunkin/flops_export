Subject: Re: Reproducibility verification — raw vs. processed inputs

Dear [Data Editor],

Thank you for the clarification and for pointing me to the guidance note. We will
proceed with Option 1: archiving the processed inputs in a stable repository (the
Development Data Hub) so that verification can start from the Stata component.

This is also the more robust route for two of the inputs specifically:

- The country-pair latency file is derived from WonderNetwork's proprietary
  "Global Ping Statistics." We are not permitted to redistribute the raw ping
  table, so the package ships only the aggregated country-pair averages.
  Archiving that aggregated, derived dataset in the DDH lets verification begin
  from a stable, citable source without redistributing the proprietary raw data.

- The temperature file is derived from the ERA5 reanalysis (~110 MB of raw
  NetCDF). ERA5 is openly licensed, but the size makes the processed,
  country-level file the practical archival unit.

We will archive the processed inputs prepared upstream of the Stata pipeline:

  1. country_temperatures.csv          (from ERA5)
  2. country_pair_latency.csv          (from WonderNetwork, aggregated)
  3. predicted_construction_costs.csv  (from Turner & Townsend DCCI + World Bank WDI)
  4. country_electricity_prices.csv    (Eurostat + EIA + compiled non-European prices)

Files 1 and 2 are the ones whose raw sources are not in the package (size /
proprietary); files 3 and 4 are included for completeness and remain fully
reproducible from raw inputs already shipped with the package. We have prepared a
metadata sheet (source, URL, access date, citation, license, and a variable-level
data dictionary) for each, ready to accompany the DDH deposit.

For transparency, the replication package already includes the Python
preprocessing scripts that build these files from their raw sources
(`Replication/preprocessing/`), together with a full Data Availability Statement
(README §6), so the complete raw-to-intermediate process is documented even
though verification will start from the archived intermediates.

A couple of procedural questions so we set this up the way you need:

- Do you require the DDH deposit (and its DOI/citation) to be finalized before
  you begin Stata verification, or can verification proceed in parallel while the
  deposit is processed?
- Should the package README cite the DDH dataset(s) by DOI once minted, and is
  there a preferred citation format you would like us to use?

We can initiate the DDH deposit right away. Please let us know if you would like
all four processed inputs archived as a single collection or only the two whose
raw sources are not in the package.

Best regards,
Michael Lokshin
