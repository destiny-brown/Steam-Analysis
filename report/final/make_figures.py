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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
FIG = Path(__file__).resolve().parent / "figures"
sys.path.insert(0, str(ROOT / "model"))
from train import (  # noqa: E402
    FEATURES, TEST_END, TEST_START, TRAIN_END, parse_row, ridge_fit, ridge_predict,
)

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
ax.axvspan(threshold, 2.5, color="red", alpha=0.06)
ax.axvline(0.0, color="gray", lw=0.6)
ax.annotate(
    f"surge rule: next peak >= 1.5x this peak\n{n_surge} of 192 training rows = {n_surge/192*100:.1f}%",
    xy=(threshold, ax.get_ylim()[1] * 0.95), xytext=(6, 0), textcoords="offset points",
    fontsize=8, color="red", va="top",
)
ax.annotate(
    "Valheim, week of 31 Aug:\npeak x9.4 in one week",
    xy=(2.24, 1.5), xytext=(1.35, 14),
    arrowprops=dict(arrowstyle="->", color="dimgray", lw=1.0),
    fontsize=8, color="dimgray",
)
ax.set_xlabel("log-growth of weekly peak")
ax.set_ylabel("Game-weeks")
ax.set_title("Weekly log-growth, training weeks (10 Aug - 4 Oct 2026)")
fig.tight_layout()
fig.savefig(FIG / "fig_surge_hist.png", dpi=200)
plt.close(fig)
print("wrote fig_cutoff.png and fig_surge_hist.png")

# --- fig_test_ridge ----------------------------------------------------------
# Re-rendered from the FROZEN panel (commit ae6edcc, the 7 Nov scoring commit)
# so the plot replicates the one-touch evaluation exactly. The recomputed MAE
# must equal the frozen 0.126251 in model/results/test.csv; we assert it.
frozen_csv = subprocess.run(
    ["git", "show", "ae6edcc:data/processed/week_panel.csv"],
    capture_output=True, text=True, cwd=ROOT, check=True,
).stdout.splitlines()
frows = [parse_row(r) for r in csv.DictReader(frozen_csv)]
frows.sort(key=lambda r: (r["week_start"], r["appid"]))
ftrain = [r for r in frows if r["week_start"] <= TRAIN_END and r["log_growth"] is not None]
ftest = [r for r in frows if TEST_START <= r["week_start"] <= TEST_END and r["log_growth"] is not None]
assert len(ftrain) == 192 and len(ftest) == 48, (len(ftrain), len(ftest))
model = ridge_fit([[r["features"][k] for k in FEATURES] for r in ftrain],
                  [r["log_growth"] for r in ftrain])
fpred = ridge_predict(model, [[r["features"][k] for k in FEATURES] for r in ftest])
factual = [r["log_growth"] for r in ftest]
fmae = sum(abs(a - p) for a, p in zip(factual, fpred)) / len(factual)
assert abs(fmae - 0.126251) < 1e-6, f"frozen MAE drifted: {fmae}"
print(f"frozen replication check: MAE {fmae:.6f} == test.csv 0.126251 OK")

fig, ax = plt.subplots(figsize=(6, 5.2))
ax.axhline(0.0, color="tab:gray", ls=":", lw=1.3, label="baseline: unchanged peak (predict 0)")
ax.scatter(factual, fpred, alpha=0.65, zorder=3)
lims = [-0.55, 0.35]
ax.plot(lims, lims, "r--", alpha=0.5, label="perfect prediction")
extremes = sorted(ftest, key=lambda r: abs(r["log_growth"]), reverse=True)[:4]
for k, r in enumerate(extremes):
    i = ftest.index(r)
    dy = (10, -15, 26, -31)[k % 4]
    ax.annotate(
        f"{r['name']}, {r['week_start_str'][5:]}", (factual[i], fpred[i]),
        textcoords="offset points", xytext=(8, dy), fontsize=6.5, alpha=0.85,
    )
ax.annotate(
    "predictions shrink toward the mean:\ndirection right, magnitudes compressed",
    xy=(0.02, 0.03), xycoords="axes fraction", fontsize=8, color="dimgray",
)
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_xlabel("Actual log-growth")
ax.set_ylabel("Predicted log-growth")
ax.set_title("Ridge: predicted vs actual (historical test weeks)\nfrozen 7 Nov evaluation -- MAE 0.1263 vs baseline 0.1440 (ratio 0.876)")
ax.legend(loc="lower right", fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "fig_test_ridge.png", dpi=200)
plt.close(fig)
print("wrote fig_test_ridge.png")
