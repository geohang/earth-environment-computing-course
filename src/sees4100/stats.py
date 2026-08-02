"""Small statistics helpers for SEES:4100."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def linear_regression_summary(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """Fit a simple linear regression and return common summary values."""
    result = scipy_stats.linregress(np.asarray(x, dtype=float), np.asarray(y, dtype=float))
    y_pred = result.intercept + result.slope * np.asarray(x, dtype=float)
    return {
        "slope": float(result.slope),
        "intercept": float(result.intercept),
        "r_value": float(result.rvalue),
        "r_squared": float(result.rvalue**2),
        "p_value": float(result.pvalue),
        "stderr": float(result.stderr),
        "rmse": rmse(y, y_pred),
        "mae": mae(y, y_pred),
    }


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate root mean square error."""
    true = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((true - pred) ** 2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate mean absolute error."""
    true = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(true - pred)))


def train_test_split_by_time(df: pd.DataFrame, date_col: str, split_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a DataFrame into train and test sets using a date threshold."""
    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col])
    split = pd.Timestamp(split_date)
    train = data[data[date_col] < split].copy()
    test = data[data[date_col] >= split].copy()
    return train, test
