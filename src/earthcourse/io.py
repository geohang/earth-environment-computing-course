"""Input and output helpers for Earth & Environmental Computing notebooks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def find_project_root(start: str | Path | None = None) -> Path:
    """Find the repository root by walking upward until a data folder is found.

    Parameters
    ----------
    start:
        Starting folder. If omitted, the current working directory is used.

    Returns
    -------
    pathlib.Path
        Path to the repository root.

    Raises
    ------
    FileNotFoundError
        If no parent folder contains a ``data`` directory.
    """
    current = Path.cwd() if start is None else Path(start).resolve()
    if current.is_file():
        current = current.parent
    while True:
        if (current / "data").exists():
            return current
        if current == current.parent:
            raise FileNotFoundError("Could not find a project root containing a data folder.")
        current = current.parent


def read_processed_csv(filename: str, **kwargs: object) -> pd.DataFrame:
    """Read a CSV file from ``data/processed``.

    Parameters
    ----------
    filename:
        Name of the processed CSV file.
    **kwargs:
        Extra keyword arguments passed to ``pandas.read_csv``.
    """
    root = find_project_root()
    path = root / "data" / "processed" / filename
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path, **kwargs)


def save_processed_csv(df: pd.DataFrame, filename: str) -> Path:
    """Save a DataFrame to ``data/processed`` and return the written path."""
    root = find_project_root()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    path = processed / filename
    df.to_csv(path, index=False)
    return path
