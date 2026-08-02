# Data Guide

This course uses small public and synthetic datasets prepared for classroom
use. Processed files are the stable inputs for notebooks.

## Processed datasets

- `iowa_city_weather_hourly.csv`: hourly weather observations or synthetic fallback data.
- `iowa_city_weather_daily.csv`: daily weather summaries for Iowa City.
- `iowa_streamflow_daily.csv`: daily mean discharge for the Iowa River at Iowa City.
- `iowa_stream_sites_annual_flow.csv`: annual streamflow summaries for watershed sites.
- `iowa_river_water_quality.csv`: real discrete water-quality samples for
  USGS site 05454500 from the Water Quality Portal (specific conductance,
  water temperature, pH, nitrate, turbidity). Nitrate results are normalized
  to `mg/L as N`; source values reported as `mg/L as NO3` are divided by
  4.42664 before use. When one sampling activity reports both forms, the
  original `as N` result is retained once. Exact duplicate rows are removed.
  The `activity_id` column identifies the sampling activity. The discrete sampling
  record at this site ends in 2012 and contains no dissolved oxygen results,
  so these data do not overlap the 2015-2025 streamflow record. Use them for
  seasonal and historical questions rather than paired flow analyses.
- `synthetic_soil_moisture_spatial.csv`: irregular spatial soil-moisture points.
- `synthetic_elevation_grid.csv`: 50 by 50 gridded synthetic elevation.
- `synthetic_temperature_grid.csv`: 50 by 50 gridded synthetic temperature.

## Raw data and fallback behavior

Run `python scripts/download_data.py` to place raw files in `data/raw/`.
Run `python scripts/clean_data.py` to create processed files. If a data service
is unavailable, the scripts create synthetic fallback data with the expected
columns so class notebooks still run.

Processed weather, streamflow, multisite, and water-quality tables retain a
`source_type` column. It records `public observation` or `synthetic fallback`
so students can identify what they are analyzing. The water-quality download
uses the full site record because this endpoint returns no data when the known
date filter is applied.
