#!/usr/bin/env python3
"""Score the sealed forecast for 9-15 November 2026 against the recorder.

Ground truth: hourly player counts from the two recorder legs
(data/live/steam_players.csv = Mac, data/live/cloud/steam_players.csv =
GitHub Actions), merged, zero counts dropped (API artifacts, per README),
per-game peak = max over 2026-11-09T00:00Z .. 2026-11-15T23:59Z.

actual_log_growth = log(actual_peak / peak_of_2026-11-02_week), where the
denominator is the same panel peak the sealed forecast multiplied.

Writes model/results/live_week.csv (per game) and prints the summary:
sealed-model MAE, unchanged-peak baseline MAE, and the ratio.
Also saves model/results/live_week_pred_vs_actual.png.
Run once, Monday 16 November 2026, after 07:59 HKT.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FORECAST_CSV = ROOT / "data" / "live" / "forecast_2026-11-09.csv"
PANEL_CSV = ROOT / "data" / "processed" / "week_panel.csv"
LEGS = {
    "mac": ROOT / "data" / "live" / "steam_players.csv",
    "cloud": ROOT / "data" / "live" / "cloud" / "steam_players.csv",
}
OUT_CSV = ROOT / "model" / "results" / "live_week.csv"
OUT_PNG = ROOT / "model" / "results" / "live_week_pred_vs_actual.png"

WINDOW_START = "2026-11-09T00:00:00Z"
WINDOW_END = "2026-11-15T23:59:59Z"
FEATURE_WEEK_START = "2026-11-02"


def load_peaks() -> dict[str, tuple[float, int, dict[str, float]]]:
    """Per appid: merged max, distinct hours seen, per-leg max."""
    best: dict[str, float] = defaultdict(float)
    hours: dict[str, set] = defaultdict(set)
    per_leg: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for leg, path in LEGS.items():
        with path.open() as handle:
            for row in csv.DictReader(handle):
                ts = row["collected_at_utc"]
                if not (WINDOW_START <= ts <= WINDOW_END):
                    continue
                raw = row.get("player_count", "")
                if not raw or row.get("ok") != "1":
                    continue  # failed request
                count = int(raw)
                if count == 0:
                    continue  # API artifact, per README zero rule
                appid = row["appid"]
                best[appid] = max(best[appid], count)
                hours[appid].add(ts[:13])  # distinct UTC hour
                per_leg[appid][leg] = max(per_leg[appid][leg], count)
    return {a: (best[a], len(hours[a]), dict(per_leg[a])) for a in best}


def main() -> None:
    forecast = {r["appid"]: r for r in csv.DictReader(FORECAST_CSV.open())}
    if len(forecast) != 24:
        raise RuntimeError(f"Sealed forecast has {len(forecast)} games, expected 24")

    panel_peak: dict[str, float] = {}
    for r in csv.DictReader(PANEL_CSV.open()):
        if r["week_start"] == FEATURE_WEEK_START:
            panel_peak[r["appid"]] = float(r["peak"])

    peaks = load_peaks()
    missing = [a for a in forecast if a not in peaks]
    if missing:
        raise RuntimeError(f"No recorder data in the live window for appids: {missing}")

    rows = []
    model_errs, base_errs = [], []
    for appid, f in sorted(forecast.items(), key=lambda kv: -float(kv[1]["predicted_log_growth"])):
        actual_peak, n_hours, leg_peaks = peaks[appid]
        peak_prev = panel_peak[appid]
        actual_lg = math.log(actual_peak / peak_prev)
        pred_lg = float(f["predicted_log_growth"])
        model_errs.append(abs(pred_lg - actual_lg))
        base_errs.append(abs(actual_lg))  # unchanged-peak predicts log_growth = 0
        mac_p = leg_peaks.get("mac", 0.0)
        cloud_p = leg_peaks.get("cloud", 0.0)
        rows.append(
            {
                "appid": appid,
                "name": f["name"],
                "peak_week_2026_11_02": int(peak_prev),
                "actual_peak_2026_11_09_week": int(actual_peak),
                "hours_observed": n_hours,
                "mac_peak": int(mac_p),
                "cloud_peak": int(cloud_p),
                "actual_log_growth": f"{actual_lg:.6f}",
                "predicted_log_growth": f"{pred_lg:.6f}",
                "model_abs_error": f"{abs(pred_lg - actual_lg):.6f}",
                "baseline_abs_error": f"{abs(actual_lg):.6f}",
                "model_name": f["model_name"],
            }
        )

    model_mae = sum(model_errs) / len(model_errs)
    base_mae = sum(base_errs) / len(base_errs)
    ratio = model_mae / base_mae

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'game':<28}{'actual_lg':>10}{'pred_lg':>10}{'model_err':>10}{'base_err':>10}{'hrs':>5}")
    for r in rows:
        print(
            f"{r['name']:<28}{float(r['actual_log_growth']):>+10.4f}"
            f"{float(r['predicted_log_growth']):>+10.4f}"
            f"{float(r['model_abs_error']):>10.4f}{float(r['baseline_abs_error']):>10.4f}"
            f"{r['hours_observed']:>5}"
        )
    print(f"\nsealed model MAE of log-growth: {model_mae:.4f}")
    print(f"unchanged-peak baseline MAE:    {base_mae:.4f}")
    print(f"ratio to baseline:              {ratio:.4f}  ({'BEATS baseline' if ratio < 1 else 'does not beat baseline'})")

    disagree = [
        (r["name"], r["mac_peak"], r["cloud_peak"])
        for r in rows
        if r["mac_peak"] and r["cloud_peak"] and abs(r["mac_peak"] - r["cloud_peak"]) / max(r["mac_peak"], r["cloud_peak"]) > 0.10
    ]
    if disagree:
        print("\nleg disagreement >10% (peak hour may differ between legs):")
        for name, m, c in disagree:
            print(f"  {name}: mac {m:,} vs cloud {c:,}")
    else:
        print("\nmac/cloud leg peaks agree within 10% on every game with both legs present.")

    fig, ax = plt.subplots(figsize=(6, 6))
    actual = [float(r["actual_log_growth"]) for r in rows]
    pred = [float(r["predicted_log_growth"]) for r in rows]
    # Zoom to the dense region. Path of Exile (actual +3.05) is 5x beyond the
    # next-largest value; without zoom the other 23 games collapse into a
    # corner. PoE is marked with an edge arrow and its exact numbers instead.
    X_LO, X_HI = -0.35, 0.65
    ax.scatter(actual, pred, alpha=0.75, zorder=3)
    ax.plot([X_LO, X_HI], [X_LO, X_HI], "r--", alpha=0.5, label="perfect prediction")
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    for r in rows:
        a = float(r["actual_log_growth"])
        if abs(a) > 0.15 and X_LO <= a <= X_HI:
            ax.annotate(
                r["name"],
                (a, float(r["predicted_log_growth"])),
                fontsize=7, alpha=0.8,
            )
    poe = next(r for r in rows if r["name"] == "Path of Exile")
    ax.annotate(
        f"Path of Exile: actual {float(poe['actual_log_growth']):+.2f},\n"
        f"predicted {float(poe['predicted_log_growth']):+.2f} (off scale)",
        xy=(X_HI - 0.005, float(poe["predicted_log_growth"])),
        xytext=(0.30, 0.18),
        arrowprops=dict(arrowstyle="->", color="tab:red", lw=1.2),
        fontsize=8, color="tab:red",
    )
    ax.set_xlim(X_LO, X_HI)
    ax.set_ylim(X_LO, X_HI)
    ax.set_xlabel("Actual log-growth (recorder, 9-15 Nov)")
    ax.set_ylabel("Sealed prediction (emitted 8 Nov)")
    ax.set_title(f"Sealed forecast vs reality, 24 games\nMAE {model_mae:.4f} vs baseline {base_mae:.4f} (ratio {ratio:.3f})")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    plt.close(fig)
    print(f"\nwrote {OUT_CSV}\nwrote {OUT_PNG}")


if __name__ == "__main__":
    main()
