"""Spatial analysis helpers for introductory geostatistics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def pairwise_distances_xy(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Calculate pairwise Euclidean distances for x-y coordinates."""
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    dx = x_arr[:, None] - x_arr[None, :]
    dy = y_arr[:, None] - y_arr[None, :]
    return np.sqrt(dx**2 + dy**2)


def empirical_semivariogram(
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    n_bins: int = 10,
    max_distance: float | None = None,
) -> pd.DataFrame:
    """Compute a simple binned empirical semivariogram.

    Parameters
    ----------
    x, y:
        Coordinate arrays.
    values:
        Observed values at the coordinates.
    n_bins:
        Number of distance bins.
    max_distance:
        Maximum pair distance to include. If omitted, half the maximum pair
        distance is used.
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    val = np.asarray(values, dtype=float)
    if not (len(x_arr) == len(y_arr) == len(val)):
        raise ValueError("x, y, and values must have the same length.")
    if len(val) < 2:
        raise ValueError("At least two observations are required.")

    distances = pairwise_distances_xy(x_arr, y_arr)
    diffs = val[:, None] - val[None, :]
    semivar = 0.5 * diffs**2
    upper = np.triu_indices(len(val), k=1)
    h = distances[upper]
    gamma = semivar[upper]
    if max_distance is None:
        max_distance = float(h.max() * 0.5)
    mask = h <= max_distance
    h = h[mask]
    gamma = gamma[mask]
    bins = np.linspace(0.0, max_distance, n_bins + 1)
    rows = []
    for i in range(n_bins):
        in_bin = (h >= bins[i]) & (h < bins[i + 1])
        if i == n_bins - 1:
            in_bin = (h >= bins[i]) & (h <= bins[i + 1])
        count = int(in_bin.sum())
        rows.append(
            {
                "bin": i + 1,
                "distance_min": float(bins[i]),
                "distance_max": float(bins[i + 1]),
                "distance_mid": float((bins[i] + bins[i + 1]) / 2),
                "semivariance": float(np.nanmean(gamma[in_bin])) if count else np.nan,
                "pair_count": count,
            }
        )
    return pd.DataFrame(rows)


def idw_predict(
    x_obs: np.ndarray,
    y_obs: np.ndarray,
    values: np.ndarray,
    x_pred: np.ndarray,
    y_pred: np.ndarray,
    power: float = 2,
) -> np.ndarray:
    """Predict values with inverse distance weighting."""
    x_obs_arr = np.asarray(x_obs, dtype=float)
    y_obs_arr = np.asarray(y_obs, dtype=float)
    val = np.asarray(values, dtype=float)
    x_pred_arr = np.asarray(x_pred, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    arrays = {
        "x_obs": x_obs_arr,
        "y_obs": y_obs_arr,
        "values": val,
        "x_pred": x_pred_arr,
        "y_pred": y_pred_arr,
    }
    for name, array in arrays.items():
        if array.ndim != 1:
            raise ValueError(f"{name} must be a one-dimensional array.")
    if not (len(x_obs_arr) == len(y_obs_arr) == len(val)):
        raise ValueError("Observed x, y, and values must have the same length.")
    if len(x_obs_arr) == 0:
        raise ValueError("At least one observation is required.")
    if len(x_pred_arr) != len(y_pred_arr):
        raise ValueError("Prediction x and y coordinates must have the same length.")
    if not np.isfinite(power) or power <= 0:
        raise ValueError("power must be a positive finite number.")
    if not all(np.isfinite(array).all() for array in arrays.values()):
        raise ValueError("IDW coordinates and values must be finite.")
    predictions = np.empty_like(x_pred_arr, dtype=float)
    for i, (xp, yp) in enumerate(zip(x_pred_arr, y_pred_arr)):
        distances = np.sqrt((x_obs_arr - xp) ** 2 + (y_obs_arr - yp) ** 2)
        exact = np.where(distances == 0)[0]
        if len(exact):
            predictions[i] = val[exact[0]]
        else:
            weights = 1.0 / distances**power
            predictions[i] = np.sum(weights * val) / np.sum(weights)
    return predictions


def leave_one_out_idw(x: np.ndarray, y: np.ndarray, values: np.ndarray, power: float = 2) -> pd.DataFrame:
    """Run leave-one-out cross-validation for IDW."""
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    val = np.asarray(values, dtype=float)
    rows = []
    for i in range(len(val)):
        mask = np.ones(len(val), dtype=bool)
        mask[i] = False
        pred = idw_predict(x_arr[mask], y_arr[mask], val[mask], x_arr[[i]], y_arr[[i]], power=power)[0]
        rows.append({"index": i, "observed": float(val[i]), "predicted": float(pred), "error": float(pred - val[i])})
    return pd.DataFrame(rows)
