Subject: Re: Reproducibility verification — raw vs. processed inputs

Dear [Data Editor],

Thank you for the clarification and for pointing me to the guidance note.

Rather than depositing the processed inputs in a separate repository, we have
included the intermediate (analysis-ready) datasets directly in the replication
package itself. Since the package is archived in the World Bank Reproducible
Research Repository, these datasets are preserved in a stable, citable location,
and verification can proceed from the Stata pipeline using the bundled
intermediates. The datasets are small, so there is no size obstacle to shipping
them with the package.

The four intermediate datasets are in `Replication/intermediate_datasets/`, each
accompanied by metadata and a variable-level data dictionary (the same files are
also in `Replication/data/`, where the pipeline reads them; the copies are
byte-identical):

  1. country_temperatures.csv          (from ERA5)
  2. country_pair_latency.csv          (from WonderNetwork, aggregated)
  3. predicted_construction_costs.csv  (from Turner & Townsend DCCI + World Bank WDI)
  4. country_electricity_prices.csv    (Eurostat + EIA + compiled non-European prices)

Two of these (files 1 and 2) are provided as intermediates rather than rebuilt
from raw because their raw sources cannot be redistributed with the package:

- The country-pair latency file is derived from WonderNetwork's proprietary
  "Global Ping Statistics." We are not permitted to redistribute the raw ping
  table, so the package ships only the aggregated country-pair averages.

- The temperature file is derived from the ERA5 reanalysis (~110 MB of raw
  NetCDF). ERA5 is openly licensed, but the size makes the processed,
  country-level file the practical unit to include.

Files 3 and 4 are included on the same footing for consistency, but their raw
inputs are already shipped in the package and they remain fully reproducible from
it (e.g., `predict_construction_costs.py` regenerates file 3 byte-for-byte).

For full transparency, the package also includes the Python preprocessing scripts
that build these files from their raw sources (`Replication/preprocessing/`) and a
complete Data Availability Statement (README §6) giving source, URL, access date,
citation, and license for every input. So the entire raw-to-intermediate process
is documented, even though verification begins from the bundled intermediates.

Please let us know if this arrangement works for your verification, or if you
would prefer the intermediate datasets handled differently.

Best regards,
Michael Lokshin
