"""Build synthetic spatial datasets for Earth & Environmental Computing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 4100


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_synthetic_spatial_data(processed_dir: Path | None = None) -> list[Path]:
    """Create irregular-point and gridded synthetic spatial datasets."""
    if processed_dir is None:
        processed_dir = project_root() / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(SEED)
    x = rng.uniform(0, 10, 80)
    y = rng.uniform(0, 8, 80)
    river_y = 3.5 + 0.8 * np.sin(x / 1.8)
    distance = np.abs(y - river_y)
    elevation = 220 + 4.5 * y + 9.0 * np.sin(x / 2.0) + rng.normal(0, 2.5, size=x.size)
    spatial_signal = 0.03 * np.sin(x / 1.5) + 0.02 * np.cos(y / 1.2)
    soil_moisture = 0.36 - 0.025 * distance - 0.0008 * (elevation - elevation.mean()) + spatial_signal
    soil_moisture += rng.normal(0, 0.018, size=x.size)
    soil_moisture = np.clip(soil_moisture, 0.05, 0.55)
    landcover = np.where(distance < 0.8, 1, np.where(elevation > np.median(elevation), 2, 3))
    points = pd.DataFrame(
        {
            "x_km": x,
            "y_km": y,
            "soil_moisture": soil_moisture,
            "elevation_m": elevation,
            "distance_to_river_km": distance,
            "landcover_code": landcover,
        }
    )

    gx = np.linspace(0, 10, 50)
    gy = np.linspace(0, 8, 50)
    xx, yy = np.meshgrid(gx, gy)
    elevation_grid = 210 + 5 * yy + 12 * np.exp(-((xx - 7) ** 2 + (yy - 5.5) ** 2) / 6)
    elevation_grid += 8 * np.sin(xx / 2.5)
    temperature_grid = 24.5 - 0.006 * elevation_grid + 1.2 * np.cos((xx - 4) / 2.0)

    elev = pd.DataFrame({"x_km": xx.ravel(), "y_km": yy.ravel(), "elevation_m": elevation_grid.ravel()})
    temp = pd.DataFrame({"x_km": xx.ravel(), "y_km": yy.ravel(), "temperature_c": temperature_grid.ravel()})

    outputs = [
        processed_dir / "synthetic_soil_moisture_spatial.csv",
        processed_dir / "synthetic_elevation_grid.csv",
        processed_dir / "synthetic_temperature_grid.csv",
    ]
    points.to_csv(outputs[0], index=False)
    elev.to_csv(outputs[1], index=False)
    temp.to_csv(outputs[2], index=False)
    return outputs


if __name__ == "__main__":
    for path in build_synthetic_spatial_data():
        print(f"Wrote {path}")
