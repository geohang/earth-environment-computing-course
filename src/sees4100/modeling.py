"""Simple environmental models for introductory computation labs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import rmse


def simple_water_balance_model(
    precip: np.ndarray,
    pet: np.ndarray,
    k_runoff: float = 0.3,
    k_baseflow: float = 0.05,
    initial_storage: float = 50.0,
) -> pd.DataFrame:
    """Run a simple bucket-style water-balance model.

    Parameters
    ----------
    precip:
        Precipitation input for each time step, in mm.
    pet:
        Potential evapotranspiration for each time step, in mm.
    k_runoff:
        Fraction of water surplus routed to quick runoff.
    k_baseflow:
        Fraction of current storage released as baseflow.
    initial_storage:
        Initial water storage in mm.
    """
    precip_arr = np.asarray(precip, dtype=float)
    pet_arr = np.asarray(pet, dtype=float)
    if precip_arr.shape != pet_arr.shape:
        raise ValueError("precip and pet must have the same shape.")
    if not (0 <= k_runoff <= 1):
        raise ValueError("k_runoff must be between 0 and 1.")
    if not (0 <= k_baseflow <= 1):
        raise ValueError("k_baseflow must be between 0 and 1.")

    storage = float(initial_storage)
    rows = []
    for p, e in zip(precip_arr, pet_arr):
        available = storage + max(p, 0.0)
        actual_et = min(max(e, 0.0), available)
        surplus = max(p - actual_et, 0.0)
        quickflow = k_runoff * surplus
        storage = max(available - actual_et - quickflow, 0.0)
        baseflow = k_baseflow * storage
        storage = max(storage - baseflow, 0.0)
        total_flow = quickflow + baseflow
        rows.append(
            {
                "precip_mm": float(p),
                "pet_mm": float(e),
                "actual_et_mm": float(actual_et),
                "quickflow_mm": float(quickflow),
                "baseflow_mm": float(baseflow),
                "simulated_flow_mm": float(total_flow),
                "storage_mm": float(storage),
            }
        )
    return pd.DataFrame(rows)


def calibrate_water_balance_grid_search(
    precip: np.ndarray,
    pet: np.ndarray,
    observed_flow: np.ndarray,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Calibrate runoff and baseflow coefficients with a small grid search."""
    observed = np.asarray(observed_flow, dtype=float)
    rows = []
    for k_runoff in np.linspace(0.05, 0.8, 16):
        for k_baseflow in np.linspace(0.01, 0.2, 20):
            sim = simple_water_balance_model(precip, pet, k_runoff=k_runoff, k_baseflow=k_baseflow)
            score = rmse(observed, sim["simulated_flow_mm"].to_numpy())
            rows.append({"k_runoff": float(k_runoff), "k_baseflow": float(k_baseflow), "rmse": score})
    table = pd.DataFrame(rows).sort_values("rmse").reset_index(drop=True)
    best = table.iloc[0].to_dict()
    return best, table
