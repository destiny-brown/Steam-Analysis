#!/usr/bin/env python3
"""Figures for the final report that did not already exist.

fig_cutoff.png   : Counter-Strike 2 players, 28 Sep - 11 Oct 2026, with the
                   Sunday 4 Oct 23:59 UTC cutoff marked (report opener).
fig_surge_hist.png: training-week log-growth histogram (192 rows) with the
                   surge threshold drawn and the base rate annotated.
Both are drawn only from files already in the repository.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
FIG = Path(__file__).resolve().parent / "figures"

# --- fig_cutoff -------------------------------------------------------------
points = json.loads((ROOT / "data/feasibility/steamcharts/730.json").read_text())
start = datetime(2026, 9, 28, tzinfo=timezone.utc)
end = datetime(2026, 10, 12, tzinfo=timezone.utc)
cutoff = datetime(2026, 10, 4, 23, 59, 59, tzinfo=timezone.utc)
ts = [datetime.fromtimestamp(p[0] / 1000, tz=timezone.utc) for p in points]
ys = [p[1] for p in points]
sel = [(t, y) for t, y in zip(ts, ys) if start <= t < end and y > 0]
xs, vals = zip(*sel)

fig, ax = plt.subplots(figsize=(6.6, 2.9))
ax.plot(xs, vals, lw=1.2, color="tab:blue")
ax.axvline(cutoff, color="red", ls="--", lw=1.2)
ax.axvspan(cutoff, end, color="gray", alpha=0.12)
ax.annotate(
    "Sunday 4 Oct 23:59 UTC\nall model inputs known here",
    xy=(cutoff, max(vals) * 0.97), xytext=(-190, -4), textcoords="offset points",
    ha="left", va="top", fontsize=8, color="red",
)
ax.annotate(
    "the week being predicted",
    xy=(datetime(2026, 10, 9, tzinfo=timezone.utc), max(vals) * 0.55),
    ha="center", fontsize=8, color="dimgray",
)
ax.set_ylabel("Players")
ax.set_title("Counter-Strike 2 concurrent players, 28 Sep - 11 Oct 2026")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
fig.tight_layout()
fig.savefig(FIG / "fig_cutoff.png", dpi=200)
plt.close(fig)

# --- fig_surge_hist ---------------------------------------------------------
growths = []
n_surge = 0
for row in csv.DictReader((ROOT / "data/processed/week_panel.csv").open()):
    if row["week_start"] <= "2026-09-28" and row["log_growth"]:
        g = float(row["log_growth"])
        growths.append(g)
        # Full surge rule (README): next peak >= 1.5x this peak AND at least
        # two robust deviations above the trailing four-week median. The first
        # week (2026-08-10) has no trailing window (mad_4w blank), so its
        # 1.5x row cannot be a surge. Matches analysis/calendar_notes.md: 5/192.
        if g >= math.log(1.5) and row["mad_4w"] != "":
            n_surge += 1
assert len(growths) == 192, f"expected 192 training rows, got {len(growths)}"
threshold = math.log(1.5)
print(f"surges (full rule): {n_surge}/192 = {n_surge/192:.3f}")

fig, ax = plt.subplots(figsize=(5.2, 2.9))
ax.hist(growths, bins=30, edgecolor="black", alpha=0.7)
ax.axvline(threshold, color="red", ls="--", lw=1.2)
ax.axvline(0.0, color="gray", lw=0.6)
ax.annotate(
    f"surge rule: next peak >= 1.5x this peak\n{n_surge} of 192 training rows = {n_surge/192*100:.1f}%",
    xy=(threshold, ax.get_ylim()[1] * 0.95), xytext=(6, 0), textcoords="offset points",
    fontsize=8, color="red", va="top",
)
ax.set_xlabel("log-growth of weekly peak")
ax.set_ylabel("Game-weeks")
ax.set_title("Weekly log-growth, training weeks (10 Aug - 4 Oct 2026)")
fig.tight_layout()
fig.savefig(FIG / "fig_surge_hist.png", dpi=200)
plt.close(fig)
print("wrote fig_cutoff.png and fig_surge_hist.png")
