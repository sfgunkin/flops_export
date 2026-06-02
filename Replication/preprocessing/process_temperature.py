"""
process_temperature.py
=======================
Generates the analysis-ready input  data/country_temperatures.csv
from the raw ERA5 2-m temperature reanalysis (NetCDF).

What it does
------------
1. Reads the ERA5 monthly 2-m temperature grid (Kelvin) from a NetCDF file.
2. Averages the most recent full years (2020-2024) to a stable annual mean and
   computes each cell's warmest-month mean ("summer peak").
3. Down-samples the 0.25-degree grid to 1 degree for a fast spatial join.
4. Assigns grid-cell centroids to countries using Natural Earth admin-0
   boundaries and computes cos(latitude) area-weighted country averages.

Inputs (not redistributed in this package because of size; see README §"Data
inputs" and the Data Availability Statement):
  - data/raw/climate/era5_2m_temperature_monthly.nc   (ERA5, ~110 MB)
        ECMWF Copernicus Climate Data Store (CDS). The CDS delivers the file
        under an opaque hash name (e.g. 9c1731ac...e012.nc); rename it to the
        path above, or edit NC_FILE below.
  - Natural Earth 110m admin-0 country boundaries (downloaded over HTTP on
        first run; a local copy may be substituted, see NE_SOURCE below).

Output:
  - data/country_temperatures.csv
        columns: iso3, country, temp_annual_C, temp_summer_peak_C, n_grid_cells

Run from anywhere:
    python preprocessing/process_temperature.py
Paths are resolved relative to this file, so no editing is required as long as
the raw NetCDF is placed at the path above.

Dependencies: numpy, netCDF4, geopandas, shapely  (see preprocessing/README.md).
"""

from datetime import datetime, timedelta
import math
import csv
import pathlib
import numpy as np
from netCDF4 import Dataset
import geopandas as gpd
from shapely.geometry import Point

# ── Paths (portable: resolved relative to this script) ─────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]   # the Replication/ folder
DATA = ROOT / "data"
NC_FILE = DATA / "raw" / "climate" / "era5_2m_temperature_monthly.nc"

# Natural Earth boundaries: download by default; to run fully offline, point
# NE_SOURCE at a local ne_110m_admin_0_countries shapefile/zip instead.
NE_SOURCE = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"

# ── 1. Load ERA5 data ──────────────────────────────────────────────────────

print("Loading ERA5 data...")
if not NC_FILE.exists():
    raise SystemExit(
        f"ERA5 NetCDF not found at {NC_FILE}\n"
        "Download the ERA5 monthly 2-m temperature grid from the Copernicus "
        "Climate Data Store and place it there (see the module docstring)."
    )
ds = Dataset(str(NC_FILE))
lat = ds.variables["latitude"][:]    # 721 values: 90 to -90
lon = ds.variables["longitude"][:]   # 1440 values: 0 to 359.75
t2m = ds.variables["t2m"][:]         # (85, 721, 1440) in Kelvin

# Time axis
times = ds.variables["valid_time"][:]
dates = [datetime(1970, 1, 1) + timedelta(seconds=int(t)) for t in times]
months = [d.month for d in dates]
years = [d.year for d in dates]
print(f"  Grid: {len(lat)}x{len(lon)}, {len(dates)} months ({dates[0]:%Y-%m} to {dates[-1]:%Y-%m})")

# ── 2. Compute temporal summaries at each grid cell ────────────────────────

# Use most recent full years (2020-2024) for stable averages
year_mask = np.array([(2020 <= y <= 2024) for y in years])
month_arr = np.array(months)

print("Computing annual mean and summer peak...")
t2m_subset = t2m[year_mask, :, :]  # ~60 months
annual_mean_K = np.mean(t2m_subset, axis=0)  # (721, 1440)

# Summer peak: warmest monthly mean across the calendar year at each cell
monthly_means_K = np.zeros((12, len(lat), len(lon)))
for m in range(12):
    mask = year_mask & (month_arr == m + 1)
    if np.any(mask):
        monthly_means_K[m] = np.mean(t2m[mask, :, :], axis=0)

# For each grid cell, the warmest month average
summer_peak_K = np.max(monthly_means_K, axis=0)  # (721, 1440)

# Convert to Celsius
annual_mean_C = annual_mean_K - 273.15
summer_peak_C = summer_peak_K - 273.15
print(f"  Global mean: {np.mean(annual_mean_C):.1f} C")

ds.close()

# ── 3. Downsample to 1-degree grid for faster spatial join ─────────────────

# Average 4x4 blocks (0.25 -> 1 degree)
step = 4
n_lat_ds = len(lat) // step  # 180
n_lon_ds = len(lon) // step  # 360

lat_ds = np.array([np.mean(lat[i * step:(i + 1) * step]) for i in range(n_lat_ds)])
lon_ds = np.array([np.mean(lon[i * step:(i + 1) * step]) for i in range(n_lon_ds)])

annual_ds = np.zeros((n_lat_ds, n_lon_ds))
summer_ds = np.zeros((n_lat_ds, n_lon_ds))
for i in range(n_lat_ds):
    for j in range(n_lon_ds):
        annual_ds[i, j] = np.mean(annual_mean_C[i * step:(i + 1) * step, j * step:(j + 1) * step])
        summer_ds[i, j] = np.mean(summer_peak_C[i * step:(i + 1) * step, j * step:(j + 1) * step])

print(f"  Downsampled to {n_lat_ds}x{n_lon_ds} (1-degree grid)")

# ── 4. Load country boundaries ─────────────────────────────────────────────

print("Loading Natural Earth country boundaries...")
world = gpd.read_file(NE_SOURCE)
# Keep only ISO_A3 and geometry
world = world[["ISO_A3", "NAME", "geometry"]].copy()
world.columns = ["iso_a3", "name", "geometry"]
world = world[world["iso_a3"] != "-99"]  # drop unassigned
print(f"  {len(world)} countries loaded")

# ── 5. Assign grid cells to countries via spatial join ──────────────────────

print("Assigning grid cells to countries (spatial join)...")

# Build GeoDataFrame of grid cell centers
points = []
data_rows = []
for i in range(n_lat_ds):
    for j in range(n_lon_ds):
        lo = lon_ds[j] if lon_ds[j] <= 180 else lon_ds[j] - 360  # convert 0-360 to -180..180
        la = lat_ds[i]
        points.append(Point(lo, la))
        data_rows.append({
            "lat": la, "lon": lo,
            "annual_C": annual_ds[i, j],
            "summer_C": summer_ds[i, j],
            "cos_weight": math.cos(math.radians(la)),  # area weight
        })

gdf_points = gpd.GeoDataFrame(data_rows, geometry=points, crs="EPSG:4326")
print(f"  {len(gdf_points)} grid points created")

# Spatial join
joined = gpd.sjoin(gdf_points, world, how="inner", predicate="within")
print(f"  {len(joined)} points matched to countries")

# ── 6. Compute area-weighted country averages ──────────────────────────────

print("Computing country averages...")

results = []
for iso3, group in joined.groupby("iso_a3"):
    weights = group["cos_weight"].values
    w_sum = weights.sum()
    if w_sum == 0:
        continue

    avg_annual = np.average(group["annual_C"].values, weights=weights)
    avg_summer = np.average(group["summer_C"].values, weights=weights)
    country_name = group["name"].iloc[0]
    n_cells = len(group)

    results.append({
        "iso3": iso3,
        "country": country_name,
        "temp_annual_C": round(avg_annual, 2),
        "temp_summer_peak_C": round(avg_summer, 2),
        "n_grid_cells": n_cells,
    })

results.sort(key=lambda r: r["temp_annual_C"])

# ── 7. Save ────────────────────────────────────────────────────────────────

outpath = DATA / "country_temperatures.csv"
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys())
    w.writeheader()
    w.writerows(results)

print(f"\nSaved {len(results)} countries to {outpath}")
print("\nColdest 5:")
for r in results[:5]:
    print(f"  {r['iso3']} {r['country']:<25} annual={r['temp_annual_C']:>6.1f} C  "
          f"summer={r['temp_summer_peak_C']:>6.1f} C")
print("Hottest 5:")
for r in results[-5:]:
    print(f"  {r['iso3']} {r['country']:<25} annual={r['temp_annual_C']:>6.1f} C  "
          f"summer={r['temp_summer_peak_C']:>6.1f} C")
