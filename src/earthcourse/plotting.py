"""Small matplotlib helpers for Earth & Environmental Computing notebooks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from matplotlib.axes import Axes
from matplotlib.figure import Figure


def label_axes(ax: Axes, title: str, xlabel: str, ylabel: str) -> Axes:
    """Apply a title and axis labels to a matplotlib Axes."""
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return ax


def add_grid(ax: Axes, alpha: float = 0.25) -> Axes:
    """Add a light grid for classroom figures."""
    ax.grid(True, alpha=alpha)
    return ax


def save_figure(fig: Figure, path: str | Path, dpi: int = 150) -> Path:
    """Save a figure after creating parent folders."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    return output


def set_common_xticks(ax: Axes, ticks: Iterable[float] | None = None) -> Axes:
    """Set x-axis ticks when a lab needs consistent tick locations."""
    if ticks is not None:
        ax.set_xticks(list(ticks))
    return ax
