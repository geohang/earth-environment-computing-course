"""Intentionally messy streamflow analysis for the AI-assisted coding lab.

This script is designed for students to inspect, refactor, test, and improve.
It runs, but it contains repeated code, unclear names, fragile path handling,
and a small unit-label problem in the plot title.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


p = Path("data/processed/iowa_streamflow_daily.csv")
x = pd.read_csv(p)
x["date"] = pd.to_datetime(x["date"])

# monthly stuff
x["month"] = x["date"].dt.to_period("M").astype(str)
a = x.groupby("month")["discharge_cfs"].mean().reset_index()
print(a.head())

# same idea again, done a different way
x["year"] = x["date"].dt.year
b = x.groupby("year")["discharge_cfs"].mean().reset_index()
print(b.tail())

plt.figure(figsize=(9, 4))
plt.plot(x["date"], x["discharge_cfs"], color="steelblue", linewidth=0.8)
plt.title("Iowa River discharge in m3/s")
plt.xlabel("Date")
plt.ylabel("Discharge")
plt.tight_layout()
plt.savefig("streamflow_hydrograph_messy.png", dpi=150)
print("saved plot")
