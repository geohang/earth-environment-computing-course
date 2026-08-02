"""Clean raw public or fallback data into processed classroom datasets."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from build_synthetic_spatial_data import build_synthetic_spatial_data


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
NITRATE_AS_NO3_TO_AS_N = 4.42664


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace({"M": np.nan, "T": 0.0, "": np.nan}), errors="coerce")


def source_type_column(df: pd.DataFrame) -> pd.Series:
    """Return a row-level source label retained in processed data."""
    if "source_note" in df.columns:
        return df["source_note"].fillna("public observation").astype(str)
    return pd.Series("public observation", index=df.index, dtype=str)


def read_rdb_or_csv(path: Path) -> pd.DataFrame:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "," in text.splitlines()[0] and not text.lstrip().startswith("#"):
        return pd.read_csv(path)
    lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    if not lines:
        raise ValueError(f"No tabular rows found in {path}")
    table = pd.read_csv(StringIO("\n".join(lines)), sep="\t", dtype=str)
    if len(table) and any(str(value).endswith("s") or str(value).endswith("d") for value in table.iloc[0].tolist()):
        table = table.iloc[1:].reset_index(drop=True)
    return table


def find_discharge_column(df: pd.DataFrame) -> str:
    """Find the NWIS daily mean discharge column in fallback or real data."""
    if "discharge_cfs" in df.columns:
        return "discharge_cfs"
    if "00060_00003" in df.columns:
        return "00060_00003"
    matches = [
        column
        for column in df.columns
        if column.endswith("_00060_00003") and not column.endswith("_cd")
    ]
    if matches:
        return matches[0]
    raise KeyError("Could not find a daily mean discharge column.")


def find_qualifier_column(df: pd.DataFrame, flow_col: str) -> str | None:
    """Find the matching NWIS qualifier column, if present."""
    candidates = [f"{flow_col}_cd", "00060_00003_cd", "qualifier"]
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def clean_weather() -> None:
    raw_path = RAW_DIR / "iowa_city_weather_hourly_raw.csv"
    if not raw_path.exists():
        raise FileNotFoundError("Run scripts/download_data.py before cleaning weather data.")
    df = pd.read_csv(raw_path)
    rename = {"latitude": "lat", "longitude": "lon", "elev": "elevation"}
    df = df.rename(columns=rename)
    df["valid"] = pd.to_datetime(df["valid"], errors="coerce")
    df["station"] = df.get("station", "IOW")
    df["tmpf"] = numeric(df.get("tmpf", pd.Series(index=df.index, dtype=float)))
    df["dwpf"] = numeric(df.get("dwpf", pd.Series(index=df.index, dtype=float)))
    df["relh"] = numeric(df.get("relh", pd.Series(index=df.index, dtype=float)))
    df["p01i"] = numeric(df.get("p01i", pd.Series(index=df.index, dtype=float))).fillna(0)
    df["sknt"] = numeric(df.get("sknt", pd.Series(index=df.index, dtype=float)))
    df["source_type"] = source_type_column(df)
    df["temp_c"] = (df["tmpf"] - 32) * 5 / 9
    df["dewpoint_c"] = (df["dwpf"] - 32) * 5 / 9
    df["precipitation_mm"] = df["p01i"] * 25.4
    df["wind_speed_mps"] = df["sknt"] * 0.514444
    if "lat" not in df:
        df["lat"] = 41.6392
    if "lon" not in df:
        df["lon"] = -91.5465
    if "elevation" not in df:
        df["elevation"] = 203.0
    df["valid"] = df["valid"].dt.floor("h")
    hourly = (
        df.groupby(["station", "valid"], as_index=False)
        .agg(
            temp_c=("temp_c", "mean"),
            dewpoint_c=("dewpoint_c", "mean"),
            relative_humidity=("relh", "mean"),
            wind_speed_mps=("wind_speed_mps", "mean"),
            precipitation_mm=("precipitation_mm", "max"),
            latitude=("lat", "first"),
            longitude=("lon", "first"),
            elevation_m=("elevation", "first"),
            source_type=("source_type", "first"),
        )
        .rename(columns={"valid": "datetime"})
    )
    hourly = hourly[
        [
            "datetime", "station", "temp_c", "dewpoint_c", "relative_humidity",
            "wind_speed_mps", "precipitation_mm", "latitude", "longitude",
            "elevation_m", "source_type",
        ]
    ]
    hourly.to_csv(PROCESSED_DIR / "iowa_city_weather_hourly.csv", index=False)

    hourly["date"] = pd.to_datetime(hourly["datetime"]).dt.date
    daily = (
        hourly.groupby(["date", "station"], as_index=False)
        .agg(
            temp_mean_c=("temp_c", "mean"),
            temp_min_c=("temp_c", "min"),
            temp_max_c=("temp_c", "max"),
            dewpoint_mean_c=("dewpoint_c", "mean"),
            relative_humidity_mean=("relative_humidity", "mean"),
            wind_speed_mean_mps=("wind_speed_mps", "mean"),
            precipitation_mm=("precipitation_mm", "sum"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            elevation_m=("elevation_m", "first"),
            source_type=("source_type", "first"),
        )
    )
    daily.to_csv(PROCESSED_DIR / "iowa_city_weather_daily.csv", index=False)
    print("Wrote weather processed files")


def clean_streamflow() -> None:
    raw_path = RAW_DIR / "iowa_streamflow_daily_raw.rdb"
    if not raw_path.exists():
        raw_path = RAW_DIR / "iowa_streamflow_daily_raw.csv"
    df = read_rdb_or_csv(raw_path)
    date_col = "datetime" if "datetime" in df.columns else "date"
    flow_col = find_discharge_column(df)
    qual_col = find_qualifier_column(df, flow_col)
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[date_col], errors="coerce").dt.date,
            "site_no": df.get("site_no", "05454500"),
            "site_name": df.get("site_name", "Iowa River at Iowa City, IA"),
            "discharge_cfs": numeric(df[flow_col]),
            "qualifier": df[qual_col] if qual_col else "",
            "source_type": source_type_column(df),
        }
    ).dropna(subset=["date", "discharge_cfs"])
    out["discharge_m3s"] = out["discharge_cfs"] * 0.028316846592
    out = out[
        [
            "date", "site_no", "site_name", "discharge_cfs", "discharge_m3s",
            "qualifier", "source_type",
        ]
    ]
    out.to_csv(PROCESSED_DIR / "iowa_streamflow_daily.csv", index=False)
    print("Wrote streamflow daily processed file")


def clean_multisite() -> None:
    meta_path = RAW_DIR / "iowa_stream_sites_metadata_raw.rdb"
    flow_path = RAW_DIR / "iowa_stream_sites_daily_raw.rdb"
    if not meta_path.exists():
        meta_path = RAW_DIR / "iowa_stream_sites_metadata_raw.csv"
    if not flow_path.exists():
        flow_path = RAW_DIR / "iowa_stream_sites_daily_raw.csv"
    meta = read_rdb_or_csv(meta_path)
    flow = read_rdb_or_csv(flow_path)
    meta = meta.rename(
        columns={
            "station_nm": "site_name",
            "dec_lat_va": "latitude",
            "dec_long_va": "longitude",
            "drain_area_va": "drainage_area_sqmi",
        }
    )
    for col in ["latitude", "longitude", "drainage_area_sqmi"]:
        if col in meta:
            meta[col] = numeric(meta[col])
    meta["source_type"] = source_type_column(meta)
    date_col = "datetime" if "datetime" in flow.columns else "date"
    flow_col = find_discharge_column(flow)
    flow = flow[["site_no", date_col, flow_col]].copy()
    flow["date"] = pd.to_datetime(flow[date_col], errors="coerce")
    flow["year"] = flow["date"].dt.year
    flow["discharge_cfs"] = numeric(flow[flow_col])
    valid_flow = flow.dropna(subset=["date", "discharge_cfs"]).copy()
    annual = (
        valid_flow
        .groupby(["site_no", "year"], as_index=False)
        .agg(
            mean_discharge_cfs=("discharge_cfs", "mean"),
            peak_discharge_cfs=("discharge_cfs", "max"),
        )
    )
    low7_rows = []
    for (site_no, year), group in valid_flow.groupby(["site_no", "year"]):
        start = pd.Timestamp(year=int(year), month=1, day=1)
        end = pd.Timestamp(year=int(year), month=12, day=31)
        daily = (
            group.sort_values("date")
            .drop_duplicates("date")
            .set_index("date")["discharge_cfs"]
            .reindex(pd.date_range(start, end, freq="D"))
        )
        low7_rows.append(
            {
                "site_no": site_no,
                "year": int(year),
                "low7_discharge_cfs": float(
                    daily.rolling(7, min_periods=7).mean().min()
                ),
            }
        )
    annual = annual.merge(pd.DataFrame(low7_rows), on=["site_no", "year"], how="left")
    annual["year"] = annual["year"].astype(int)
    keep_meta = [
        "site_no", "site_name", "latitude", "longitude",
        "drainage_area_sqmi", "source_type",
    ]
    for col in keep_meta:
        if col not in meta:
            meta[col] = np.nan
    out = annual.merge(meta[keep_meta].drop_duplicates("site_no"), on="site_no", how="left")
    out = out[keep_meta + ["year", "mean_discharge_cfs", "peak_discharge_cfs", "low7_discharge_cfs"]]
    out.to_csv(PROCESSED_DIR / "iowa_stream_sites_annual_flow.csv", index=False)
    print("Wrote multisite annual flow processed file")


def normalize_water_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Select, normalize, and label water-quality records."""
    rename = {
        "ActivityIdentifier": "activity_id",
        "ActivityStartDate": "date",
        "MonitoringLocationIdentifier": "site_id",
        "CharacteristicName": "characteristic_name",
        "ResultMeasureValue": "result_value",
        "ResultMeasure/MeasureUnitCode": "result_unit",
        "ActivityMediaName": "sample_medium",
        "ActivityTypeCode": "activity_type",
        "LatitudeMeasure": "latitude",
        "LongitudeMeasure": "longitude",
    }
    df = df.rename(columns=rename)
    needed = [
        "activity_id", "date", "site_id", "characteristic_name", "result_value",
        "result_unit", "sample_medium", "activity_type", "latitude", "longitude",
    ]
    for col in needed:
        if col not in df:
            df[col] = np.nan
    df["source_type"] = source_type_column(df)
    out = df[needed + ["source_type"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    out["result_value"] = numeric(out["result_value"])
    out["latitude"] = numeric(out["latitude"])
    out["longitude"] = numeric(out["longitude"])
    out = out.dropna(subset=["date", "characteristic_name", "result_value"])
    nitrate = out["characteristic_name"].astype(str).str.casefold().eq("nitrate")
    normalized_unit = (
        out["result_unit"].astype(str).str.casefold().str.replace(" ", "", regex=False)
    )
    nitrate_as_no3 = nitrate & normalized_unit.eq("mg/lasno3")
    nitrate_as_n = nitrate & normalized_unit.eq("mg/lasn")
    out["_unit_priority"] = np.where(nitrate_as_n, 0, np.where(nitrate_as_no3, 1, 0))
    out.loc[nitrate_as_no3, "result_value"] = (
        out.loc[nitrate_as_no3, "result_value"] / NITRATE_AS_NO3_TO_AS_N
    )
    out.loc[nitrate_as_no3 | nitrate_as_n, "result_unit"] = "mg/L as N"
    known_site = out["site_id"].astype(str).eq("USGS-05454500")
    out.loc[known_site, "latitude"] = out.loc[known_site, "latitude"].fillna(41.656)
    out.loc[known_site, "longitude"] = out.loc[known_site, "longitude"].fillna(-91.536)
    with_activity = out["activity_id"].notna()
    identified = (
        out.loc[with_activity]
        .sort_values("_unit_priority")
        .drop_duplicates(["activity_id", "characteristic_name"], keep="first")
    )
    unidentified = out.loc[~with_activity].drop_duplicates()
    out = (
        pd.concat([identified, unidentified], ignore_index=True)
        .drop(columns="_unit_priority")
        .drop_duplicates()
        .reset_index(drop=True)
    )
    return out


def clean_water_quality() -> None:
    raw_path = RAW_DIR / "iowa_river_water_quality_raw.csv"
    df = pd.read_csv(raw_path, low_memory=False)
    out = normalize_water_quality(df)
    out.to_csv(PROCESSED_DIR / "iowa_river_water_quality.csv", index=False)
    print("Wrote water-quality processed file")


def main() -> None:
    clean_weather()
    clean_streamflow()
    clean_multisite()
    clean_water_quality()
    for path in build_synthetic_spatial_data(PROCESSED_DIR):
        print(f"Wrote {path.name}")


if __name__ == "__main__":
    main()
