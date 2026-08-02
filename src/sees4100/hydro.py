"""Hydrologic calculation helpers used in SEES:4100 labs."""

from __future__ import annotations

import numpy as np
import pandas as pd


CFS_TO_M3S = 0.028316846592


def cfs_to_m3s(discharge_cfs: float | np.ndarray | pd.Series) -> float | np.ndarray | pd.Series:
    """Convert discharge from cubic feet per second to cubic meters per second."""
    return discharge_cfs * CFS_TO_M3S


def _with_datetime(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    return out


def annual_mean_flow(
    df: pd.DataFrame,
    date_col: str = "date",
    flow_col: str = "discharge_cfs",
) -> pd.DataFrame:
    """Calculate annual mean flow.

    Returns a DataFrame with columns ``year`` and ``mean_discharge_cfs``.
    """
    data = _with_datetime(df, date_col)
    data["year"] = data[date_col].dt.year
    result = (
        data.groupby("year", as_index=False)[flow_col]
        .mean()
        .rename(columns={flow_col: "mean_discharge_cfs"})
    )
    return result


def seven_day_low_flow(
    df: pd.DataFrame,
    date_col: str = "date",
    flow_col: str = "discharge_cfs",
) -> pd.DataFrame:
    """Calculate the annual minimum mean over seven consecutive calendar days.

    Missing dates break a window instead of allowing seven observations spread
    across a longer period to be treated as seven consecutive days.
    """
    data = _with_datetime(df, date_col).sort_values(date_col)
    data[flow_col] = pd.to_numeric(data[flow_col], errors="coerce")
    data = data.dropna(subset=[date_col])
    if data[date_col].duplicated().any():
        raise ValueError("Dates must be unique when calculating 7-day low flow.")
    data["year"] = data[date_col].dt.year
    pieces = []
    for year, group in data.groupby("year"):
        start = pd.Timestamp(year=int(year), month=1, day=1)
        end = pd.Timestamp(year=int(year), month=12, day=31)
        daily = (
            group.set_index(date_col)[flow_col]
            .reindex(pd.date_range(start, end, freq="D"))
        )
        rolling = daily.rolling(window=7, min_periods=7).mean()
        pieces.append({"year": int(year), "low7_discharge_cfs": float(rolling.min())})
    return pd.DataFrame(pieces)


def annual_peak_flow(
    df: pd.DataFrame,
    date_col: str = "date",
    flow_col: str = "discharge_cfs",
) -> pd.DataFrame:
    """Calculate annual peak daily flow and its date."""
    data = _with_datetime(df, date_col)
    data["year"] = data[date_col].dt.year
    rows = []
    for year, group in data.groupby("year"):
        idx = group[flow_col].idxmax()
        rows.append(
            {
                "year": int(year),
                "peak_date": data.loc[idx, date_col].date().isoformat(),
                "peak_discharge_cfs": float(data.loc[idx, flow_col]),
            }
        )
    return pd.DataFrame(rows)


def flow_duration_curve(df: pd.DataFrame, flow_col: str = "discharge_cfs") -> pd.DataFrame:
    """Return exceedance probability and sorted flow for a flow-duration curve."""
    values = pd.to_numeric(df[flow_col], errors="coerce").dropna().sort_values(ascending=False)
    n = len(values)
    if n == 0:
        return pd.DataFrame(columns=["exceedance_probability", flow_col])
    ranks = np.arange(1, n + 1)
    exceedance = ranks / (n + 1)
    return pd.DataFrame({"exceedance_probability": exceedance, flow_col: values.to_numpy()})
