#!/usr/bin/env python3
"""Emit the sealed live forecast for the week of 9-15 November 2026.

Fit: ridge (alpha=1.0, the frozen configuration from model/train.py) refit on
all 288 labeled rows (train + validation + historical test, weeks of
10 Aug - 1 Nov). decisions.md 2026-11-08: standard post-evaluation practice;
the historical test weeks precede the forecast week, so no leakage.

Feature rows: the 24 games' live week (week_start 2026-11-02), whose
next_peak/log_growth are empty by construction.

Output: data/live/forecast_2026-11-09.csv with columns
emitted_at_utc,appid,name,predicted_log_growth,predicted_peak,model_name
Refuses to run at or after Monday 2026-11-09 00:00 UTC.
Once committed, this file is never edited again.
"""

from __future__ import annotations

import csv
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import FEATURES, load_panel, ridge_fit, ridge_predict  # noqa: E402

GAMES_CSV = ROOT / "collect" / "games.csv"
OUT_CSV = ROOT / "data" / "live" / "forecast_2026-11-09.csv"
LIVE_WEEK_START = "2026-11-02"
SEAL_DEADLINE_UTC = datetime(2026, 11, 9, 0, 0, 0, tzinfo=timezone.utc)
MODEL_NAME = "ridge_alpha1_refit_288"


def main() -> None:
    now = datetime.now(timezone.utc)
    if now >= SEAL_DEADLINE_UTC:
        raise RuntimeError(
            f"Seal deadline passed ({now.isoformat()} >= 2026-11-09T00:00:00Z). "
            "A forecast emitted now would not be sealed before the live week."
        )

    rows = load_panel()
    labeled = [r for r in rows if r["log_growth"] is not None]
    live = [r for r in rows if r["week_start_str"] == LIVE_WEEK_START]

    if len(labeled) != 288:
        raise RuntimeError(f"Expected 288 labeled rows, got {len(labeled)}")
    if len(live) != 24:
        raise RuntimeError(f"Expected 24 live rows for {LIVE_WEEK_START}, got {len(live)}")
    if any(r["log_growth"] is not None for r in live):
        raise RuntimeError("Live rows already have outcomes; refusing to forecast on labeled data.")

    X_train = [[r["features"][k] for k in FEATURES] for r in labeled]
    y_train = [r["log_growth"] for r in labeled]
    model = ridge_fit(X_train, y_train, alpha=1.0)

    X_live = [[r["features"][k] for k in FEATURES] for r in live]
    predicted_log_growth = ridge_predict(model, X_live)

    emitted_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    out_rows = []
    for r, plg in zip(live, predicted_log_growth):
        out_rows.append(
            {
                "emitted_at_utc": emitted_at,
                "appid": r["appid"],
                "name": r["name"],
                "predicted_log_growth": f"{plg:.6f}",
                "predicted_peak": f"{r['peak'] * math.exp(plg):.1f}",
                "model_name": MODEL_NAME,
            }
        )

    # Cross-check: every game in games.csv appears exactly once.
    expected = {(g["appid"].strip(), g["name"].strip()) for g in csv.DictReader(GAMES_CSV.open())}
    got = {(r["appid"], r["name"]) for r in out_rows}
    if got != expected:
        raise RuntimeError(f"Game set mismatch. Missing: {expected - got}. Extra: {got - expected}.")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["emitted_at_utc", "appid", "name", "predicted_log_growth", "predicted_peak", "model_name"],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"emitted_at_utc {emitted_at}")
    print(f"fit on {len(labeled)} labeled rows, predicted {len(out_rows)} games")
    for r in sorted(out_rows, key=lambda x: float(x["predicted_log_growth"]), reverse=True):
        print(f"  {float(r['predicted_log_growth']):+.4f}  {r['name']} (peak {float(r['predicted_peak']):,.0f})")
    print(f"wrote {OUT_CSV} -- sealed; do not edit after commit")


if __name__ == "__main__":
    main()
