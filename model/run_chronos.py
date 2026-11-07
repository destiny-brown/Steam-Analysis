#!/usr/bin/env python3
"""Chronos-2 small, zero-shot, on the historical test weeks.

For every test row (game, week t) the context is that game's weekly peaks
from 10 August 2026 through week t (the Sunday cutoff). The model predicts
one step ahead: week t+1's peak. Predicted log-growth is
log(predicted_peak / peak_t), the same target as the rest of the ladder.

If anything fails, the verbatim error goes to model/results/chronos_note.txt
per the README. That file is a deliverable either way.
"""

from __future__ import annotations

import csv
import math
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL_CSV = ROOT / "data" / "processed" / "week_panel.csv"
NOTE = ROOT / "model" / "results" / "chronos_note.txt"
TEST_START = "2026-10-19"
TEST_END = "2026-11-01"
BASELINE_TEST_MAE = 0.144049  # model/results/test.csv, unchanged_peak


def main() -> None:
    try:
        import numpy as np
        from chronos import Chronos2Pipeline

        rows = list(csv.DictReader(PANEL_CSV.open()))
        peaks: dict[str, list[tuple[str, float]]] = {}
        for row in rows:
            peaks.setdefault(row["appid"], []).append((row["week_start"], float(row["peak"])))
        for series in peaks.values():
            series.sort()

        pipeline = Chronos2Pipeline.from_pretrained("autogluon/chronos-2-small", device_map="cpu")

        contexts = []
        meta = []
        for row in rows:
            if not (TEST_START <= row["week_start"] <= TEST_END) or not row["log_growth"]:
                continue
            series = peaks[row["appid"]]
            context = [p for w, p in series if w <= row["week_start"] and p > 0]
            if len(context) < 3:
                continue
            contexts.append(np.array(context, dtype=np.float32))
            meta.append((row["appid"], row["name"], row["week_start"], float(row["peak"]), float(row["log_growth"])))

        forecasts = pipeline.predict(contexts, prediction_length=1)
        lines = []
        errors = []
        for (appid, name, week_start, peak, actual), forecast in zip(meta, forecasts):
            arr = np.asarray(forecast, dtype=float)
            # shape is (n_quantiles, prediction_length) or (prediction_length, n_quantiles)
            pred_peak = float(np.median(arr[:, -1] if arr.shape[0] < arr.shape[-1] else arr[-1, :]))
            if pred_peak <= 0:
                pred_peak = peak  # fallback: unchanged
            pred_log_growth = math.log(pred_peak / peak)
            err = abs(pred_log_growth - actual)
            errors.append(err)
            lines.append(f"{week_start},{appid},{name},{peak:.0f},{pred_peak:.0f},{pred_log_growth:.6f},{actual:.6f},{err:.6f}")

        test_mae = sum(errors) / len(errors)
        ratio = test_mae / BASELINE_TEST_MAE
        note = [
            "Chronos-2 small (autogluon/chronos-2-small), zero-shot, run 2026-11-07.",
            "Context: weekly peaks 2026-08-10 through the row's own week (Sunday cutoff).",
            "Forecast: one step ahead; median quantile as the point forecast.",
            "",
            f"rows scored: {len(errors)}",
            f"test MAE of log-growth: {test_mae:.6f}",
            f"unchanged-peak test MAE: {BASELINE_TEST_MAE:.6f}",
            f"ratio to baseline: {ratio:.4f}",
            "",
            "week_start,appid,name,peak,predicted_peak,predicted_log_growth,actual_log_growth,abs_error",
            *lines,
        ]
        NOTE.write_text("\n".join(note) + "\n")
        print(f"chronos-2 small test MAE: {test_mae:.4f} (ratio {ratio:.4f}), wrote {NOTE}")
    except Exception:
        NOTE.write_text(
            "Chronos-2 small attempt failed on 2026-11-07. Verbatim error:\n\n"
            + traceback.format_exc()
        )
        print(f"FAILED, verbatim error written to {NOTE}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
