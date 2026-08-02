"""Download public teaching data or create synthetic fallback raw files."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SITES = [
    "05451210", "05451500", "05451700", "05451900", "05452000", "05452200",
    "05453000", "05453100", "05453520", "05454000", "05454220", "05454300",
    "05454500", "05455100", "05455500", "05455700", "05465500",
]


def fetch_text(url: str, path: Path, timeout: int = 30) -> bool:
    """Fetch a URL to a text file. Return True on success."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        text = response.text
        if len(text.strip()) < 100:
            raise ValueError("Response was too small to be useful.")
        path.write_text(text, encoding="utf-8")
        print(f"Downloaded {path.name}")
        return True
    except Exception as exc:
        print(f"Download failed for {path.name}: {exc}")
        return False


def fetch_csv(
    url: str,
    path: Path,
    required_columns: set[str],
    min_rows: int = 1,
    timeout: int = 30,
) -> bool:
    """Fetch and validate a CSV before replacing an existing raw file."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        frame = pd.read_csv(StringIO(response.text), low_memory=False)
        missing = required_columns.difference(frame.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        if len(frame) < min_rows:
            raise ValueError(f"Expected at least {min_rows} rows; received {len(frame)}.")
        path.write_text(response.text, encoding="utf-8")
        print(f"Downloaded and validated {path.name}: {len(frame)} rows")
        return True
    except Exception as exc:
        print(f"Download failed validation for {path.name}: {exc}")
        return False


def compact_asos_hourly(path: Path) -> None:
    """Compact dense ASOS reports to one teaching record per station-hour."""
    df = pd.read_csv(path, low_memory=False)
    if "valid" not in df.columns or len(df) < 100000:
        return
    df["valid"] = pd.to_datetime(df["valid"], errors="coerce")
    df = df.dropna(subset=["valid"]).copy()
    df["valid"] = df["valid"].dt.floor("h")
    for column in ["tmpf", "dwpf", "relh", "p01i", "sknt", "lat", "lon", "elevation"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column].replace({"M": np.nan, "T": 0.0}), errors="coerce")
    if "station" not in df.columns:
        df["station"] = "IOW"
    agg = {}
    for column in ["tmpf", "dwpf", "relh", "sknt"]:
        if column in df.columns:
            agg[column] = "mean"
    if "p01i" in df.columns:
        agg["p01i"] = "max"
    for column in ["lat", "lon", "elevation"]:
        if column in df.columns:
            agg[column] = "first"
    if "source_note" in df.columns:
        agg["source_note"] = "first"
    compact = df.groupby(["station", "valid"], as_index=False).agg(agg)
    compact.to_csv(path, index=False)
    print(f"Compacted ASOS raw file to {len(compact)} hourly records")


def synthetic_weather(path: Path) -> None:
    rng = np.random.default_rng(4100)
    dates = pd.date_range("2019-01-01", "2025-12-31 23:00", freq="h")
    day = dates.dayofyear.to_numpy()
    hour = dates.hour.to_numpy()
    seasonal_c = 11 + 14 * np.sin(2 * np.pi * (day - 95) / 365.25)
    daily_c = 4 * np.sin(2 * np.pi * (hour - 14) / 24)
    temp_c = seasonal_c + daily_c + rng.normal(0, 2.0, size=len(dates))
    dew_c = temp_c - rng.uniform(2, 9, size=len(dates))
    relh = np.clip(100 - 5 * (temp_c - dew_c) + rng.normal(0, 4, size=len(dates)), 25, 100)
    precip_in = rng.gamma(0.5, 0.08, size=len(dates)) * (rng.random(len(dates)) < 0.08)
    wind_kt = np.clip(rng.normal(8, 3, size=len(dates)), 0, None)
    df = pd.DataFrame(
        {
            "station": "IOW_SYNTHETIC",
            "valid": dates,
            "tmpf": temp_c * 9 / 5 + 32,
            "dwpf": dew_c * 9 / 5 + 32,
            "relh": relh,
            "p01i": precip_in,
            "sknt": wind_kt,
            "lat": 41.6392,
            "lon": -91.5465,
            "elevation": 203.0,
            "source_note": "synthetic fallback",
        }
    )
    df.to_csv(path, index=False)
    print(f"Wrote synthetic fallback {path.name}")


def synthetic_streamflow(path: Path) -> None:
    rng = np.random.default_rng(4101)
    dates = pd.date_range("2015-01-01", "2025-12-31", freq="D")
    day = dates.dayofyear.to_numpy()
    seasonal = 1800 + 900 * np.sin(2 * np.pi * (day - 80) / 365.25)
    storm = rng.gamma(2.0, 120.0, size=len(dates)) * (rng.random(len(dates)) < 0.18)
    flow = np.clip(seasonal + storm + rng.normal(0, 120, size=len(dates)), 80, None)
    df = pd.DataFrame(
        {
            "agency_cd": "USGS",
            "site_no": "05454500",
            "datetime": dates.date.astype(str),
            "00060_00003": flow,
            "00060_00003_cd": "A",
            "site_name": "Iowa River at Iowa City, IA",
            "source_note": "synthetic fallback",
        }
    )
    df.to_csv(path, index=False)
    print(f"Wrote synthetic fallback {path.name}")


def synthetic_multisite(raw_dir: Path) -> None:
    rng = np.random.default_rng(4102)
    site_rows = []
    flow_rows = []
    dates = pd.date_range("2020-01-01", "2025-12-31", freq="D")
    for i, site in enumerate(SITES):
        lat = 41.2 + 0.08 * i + rng.normal(0, 0.02)
        lon = -92.6 + 0.07 * i + rng.normal(0, 0.02)
        area = 80 + 60 * i + rng.normal(0, 8)
        site_rows.append(
            {
                "site_no": site,
                "station_nm": f"Synthetic Iowa River watershed site {site}",
                "dec_lat_va": lat,
                "dec_long_va": lon,
                "drain_area_va": max(area, 10),
                "source_note": "synthetic fallback",
            }
        )
        base = 120 + 8 * area
        seasonal = base + 0.35 * base * np.sin(2 * np.pi * (dates.dayofyear.to_numpy() - 70) / 365.25)
        flow = np.clip(seasonal + rng.gamma(2.0, 40.0, size=len(dates)), 5, None)
        for dt, q in zip(dates, flow):
            flow_rows.append(
                {
                    "site_no": site,
                    "datetime": dt.date().isoformat(),
                    "00060_00003": q,
                    "00060_00003_cd": "A",
                    "source_note": "synthetic fallback",
                }
            )
    pd.DataFrame(site_rows).to_csv(raw_dir / "iowa_stream_sites_metadata_raw.csv", index=False)
    pd.DataFrame(flow_rows).to_csv(raw_dir / "iowa_stream_sites_daily_raw.csv", index=False)
    print("Wrote synthetic fallback multisite files")


def synthetic_water_quality(path: Path) -> None:
    rng = np.random.default_rng(4103)
    dates = pd.date_range("2010-01-01", "2025-12-31", freq="21D")
    chars = [
        ("Nitrate", "mg/L as N", 4.0, 1.4),
        ("Specific conductance", "uS/cm", 620.0, 80.0),
        ("pH", "pH units", 7.8, 0.25),
        ("Turbidity", "NTU", 18.0, 8.0),
        ("Temperature, water", "deg C", 13.0, 8.0),
        ("Dissolved oxygen", "mg/L", 9.0, 1.8),
    ]
    rows = []
    for dt in dates:
        for name, unit, mean, sd in chars:
            value = max(mean + rng.normal(0, sd), 0.01)
            rows.append(
                {
                    "ActivityStartDate": dt.date().isoformat(),
                    "MonitoringLocationIdentifier": "USGS-05454500",
                    "CharacteristicName": name,
                    "ResultMeasureValue": value,
                    "ResultMeasure/MeasureUnitCode": unit,
                    "ActivityMediaName": "Water",
                    "ActivityTypeCode": "Sample-Routine",
                    "LatitudeMeasure": 41.656,
                    "LongitudeMeasure": -91.536,
                    "source_note": "synthetic fallback",
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Wrote synthetic fallback {path.name}")


def main() -> None:
    weather_path = RAW_DIR / "iowa_city_weather_hourly_raw.csv"
    weather_downloaded = False
    for station in ["IOW", "CID", "DSM"]:
        weather_url = (
            "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"
            f"station={station}&data=tmpf&data=dwpf&data=relh&data=p01i&data=sknt"
            "&year1=2019&month1=1&day1=1&year2=2025&month2=12&day2=31"
            "&tz=Etc/UTC&format=onlycomma&latlon=yes&elev=yes&missing=M&trace=T"
            "&direct=no&report_type=1&report_type=2"
        )
        if fetch_csv(
            weather_url,
            weather_path,
            required_columns={"station", "valid", "tmpf"},
            min_rows=1000,
        ):
            weather_downloaded = True
            compact_asos_hourly(weather_path)
            break
    if not weather_downloaded:
        synthetic_weather(weather_path)

    stream_url = (
        "https://waterservices.usgs.gov/nwis/dv/?format=rdb&sites=05454500"
        "&startDT=2015-01-01&endDT=2025-12-31&parameterCd=00060&statCd=00003&siteStatus=all"
    )
    stream_path = RAW_DIR / "iowa_streamflow_daily_raw.rdb"
    if not fetch_text(stream_url, stream_path):
        synthetic_streamflow(stream_path)

    sites = ",".join(SITES)
    site_meta_url = f"https://waterservices.usgs.gov/nwis/site/?format=rdb&sites={sites}&siteOutput=expanded"
    site_flow_url = (
        "https://waterservices.usgs.gov/nwis/dv/?format=rdb"
        f"&sites={sites}&startDT=2020-01-01&endDT=2025-12-31"
        "&parameterCd=00060&statCd=00003&siteStatus=all"
    )
    ok_meta = fetch_text(site_meta_url, RAW_DIR / "iowa_stream_sites_metadata_raw.rdb")
    ok_flow = fetch_text(site_flow_url, RAW_DIR / "iowa_stream_sites_daily_raw.rdb")
    if not (ok_meta and ok_flow):
        synthetic_multisite(RAW_DIR)

    wq_url = (
        "https://www.waterqualitydata.us/data/Result/search?"
        "siteid=USGS-05454500"
        "&characteristicName=Nitrate&characteristicName=Specific%20conductance"
        "&characteristicName=pH&characteristicName=Turbidity"
        "&characteristicName=Temperature%2C%20water&characteristicName=Dissolved%20oxygen"
        "&mimeType=csv&zip=no"
    )
    wq_path = RAW_DIR / "iowa_river_water_quality_raw.csv"
    if not fetch_csv(
        wq_url,
        wq_path,
        required_columns={
            "ActivityStartDate",
            "MonitoringLocationIdentifier",
            "CharacteristicName",
            "ResultMeasureValue",
            "ResultMeasure/MeasureUnitCode",
        },
        min_rows=1,
        timeout=45,
    ):
        synthetic_water_quality(wq_path)


if __name__ == "__main__":
    main()
