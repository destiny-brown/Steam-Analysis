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

    actual = [float(r["actual_log_growth"]) for r in rows]
    pred = [float(r["predicted_log_growth"]) for r in rows]
    X_LO, X_HI = -0.35, 0.65
    SHORT = {
        "Counter-Strike 2": "CS2", "PUBG: BATTLEGROUNDS": "PUBG",
        "Team Fortress 2": "TF2", "Marvel Rivals": "Marvel Rivals",
        "THE FINALS": "FINALS", "Destiny 2": "Destiny 2", "Warframe": "Warframe",
        "HELLDIVERS 2": "HD2", "Left 4 Dead 2": "L4D2",
        "Grand Theft Auto V": "GTA V", "Rust": "Rust", "Valheim": "Valheim",
        "Palworld": "Palworld", "Terraria": "Terraria",
        "Stardew Valley": "Stardew", "ELDEN RING": "ELDEN RING",
        "Baldur's Gate 3": "BG3", "Path of Exile": "PoE", "Lost Ark": "Lost Ark",
        "Dead by Daylight": "DbD", "War Thunder": "War Thunder",
        "NARAKA: BLADEPOINT": "NARAKA", "Dota 2": "Dota 2",
        "Apex Legends": "Apex",
    }
    # Two panels, honest about the outlier: a wide zoomed panel where all 23
    # ordinary games are labeled, and a narrow full-scale panel where Path of
    # Exile (+3.05) appears in its true position instead of being hidden.
    fig = plt.figure(figsize=(11, 5.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[3.1, 1.0], wspace=0.04)
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharey=ax)

    ax.scatter(actual, pred, alpha=0.75, zorder=3)
    ax.plot([X_LO, X_HI], [X_LO, X_HI], "r--", alpha=0.5, label="perfect prediction")
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    order = sorted(range(len(rows)), key=lambda i: actual[i])
    for k, i in enumerate(order):
        if rows[i]["name"] == "Path of Exile":
            continue
        dy = (10, -14, 24, -28)[k % 4]
        ax.annotate(
            SHORT[rows[i]["name"]], (actual[i], pred[i]),
            textcoords="offset points", xytext=(0, dy), ha="center",
            fontsize=6, alpha=0.85,
        )
    ax.set_xlim(X_LO, X_HI)
    ax.set_ylim(X_LO, X_HI)
    ax.set_xlabel("Actual log-growth (recorder, 9-15 Nov)")
    ax.set_ylabel("Sealed prediction (emitted 8 Nov)")
    ax.set_title("Zoom: 23 of 24 games, all labeled")
    ax.legend(loc="upper left", fontsize=8)

    ax2.scatter(actual, pred, alpha=0.75, zorder=3)
    ax2.plot([X_LO, 3.25], [X_LO, 3.25], "r--", alpha=0.5)
    ax2.axhline(0, color="gray", lw=0.5)
    ax2.axvline(0, color="gray", lw=0.5)
    i_poe = next(i for i, r in enumerate(rows) if r["name"] == "Path of Exile")
    ax2.annotate(
        f"Path of Exile\nactual {actual[i_poe]:+.2f}\npredicted {pred[i_poe]:+.2f}",
        (actual[i_poe], pred[i_poe]), textcoords="offset points", xytext=(-72, 30),
        fontsize=7.5, color="tab:red",
        arrowprops=dict(arrowstyle="->", color="tab:red", lw=1.1),
    )
    ax2.set_xlim(X_LO, 3.25)
    ax2.set_xlabel("Actual (full scale)")
    ax2.set_title("Full scale")
    plt.setp(ax2.get_yticklabels(), visible=False)
    fig.suptitle(
        f"Sealed forecast vs reality, 24 games -- MAE {model_mae:.4f} "
        f"vs baseline {base_mae:.4f} (ratio {ratio:.3f})"
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    plt.close(fig)
    print(f"\nwrote {OUT_CSV}\nwrote {OUT_PNG}")


if __name__ == "__main__":
    main()
