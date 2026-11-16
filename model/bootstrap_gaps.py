"""Paired-bootstrap uncertainty for the three baseline-vs-ridge gaps.

Written 16 Nov 2026 after marker feedback: the report quoted a paired
bootstrap CI only for the validation gap while calling the historical test
edge "real". This script computes the same interval for all three windows
--- validation and test from the FROZEN panel at ae6edcc (ridge refit on
train rows only, replicating the one-touch 7 Nov evaluation), live from the
committed scoring table model/results/live_week.csv --- and writes
model/results/bootstrap_gaps.csv. Seed fixed at 0, 10,000 resamples.

Gap convention: per-row |baseline error| - |model error|; positive means
the model beats the baseline on that row.

Run:  .venv/bin/python model/bootstrap_gaps.py
"""

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import (  # noqa: E402
    FEATURES, TRAIN_END, TEST_START, TEST_END, RESULTS_DIR,
    parse_row, ridge_fit, ridge_predict, write_csv,
)
from datetime import datetime, timezone  # noqa: E402

FROZEN_COMMIT = "ae6edcc"
N_BOOT = 10_000
SEED = 0
VAL_START = datetime(2026, 10, 5, tzinfo=timezone.utc)
VAL_END = datetime(2026, 10, 12, tzinfo=timezone.utc)

# Values quoted in report/final/main.tex; drift fails the build of evidence.
EXPECTED = {
    "validation": (-0.0085, -0.0264, 0.0098, 21),  # model wins; baseline wins the other 27
    "test": (0.0178, -0.0012, 0.0364, 34),
    "live": (-0.0091, -0.0396, 0.0208, 11),
}


def bootstrap(d: np.ndarray) -> tuple[float, float, float, int]:
    rng = np.random.default_rng(SEED)
    means = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(N_BOOT)])
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), int((d > 0).sum())


def main() -> None:
    frozen_csv = subprocess.run(
        ["git", "show", f"{FROZEN_COMMIT}:data/processed/week_panel.csv"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    rows = [parse_row(r) for r in csv.DictReader(frozen_csv)]
    rows.sort(key=lambda r: (r["week_start"], r["appid"]))
    train = [r for r in rows if r["week_start"] <= TRAIN_END and r["log_growth"] is not None]
    model = ridge_fit([[r["features"][k] for k in FEATURES] for r in train],
                      [r["log_growth"] for r in train])

    def ridge_gap(lo, hi):
        w = [r for r in rows if lo <= r["week_start"] <= hi and r["log_growth"] is not None]
        p = ridge_predict(model, [[r["features"][k] for k in FEATURES] for r in w])
        y = np.array([r["log_growth"] for r in w])
        return np.abs(y) - np.abs(y - np.asarray(p))

    live_rows = list(csv.DictReader(open(RESULTS_DIR / "live_week.csv")))
    gaps = {
        "validation": ridge_gap(VAL_START, VAL_END),
        "test": ridge_gap(TEST_START, TEST_END),
        "live": np.array([float(r["baseline_abs_error"]) - float(r["model_abs_error"])
                          for r in live_rows]),
    }

    out = []
    for window, d in gaps.items():
        mean, lo, hi, wins = bootstrap(d)
        exp_mean, exp_lo, exp_hi, exp_wins = EXPECTED[window]
        assert abs(mean - exp_mean) < 5e-5, (window, mean)
        assert abs(lo - exp_lo) < 5e-4 and abs(hi - exp_hi) < 5e-4, (window, lo, hi)
        assert wins == exp_wins, (window, wins)
        out.append({"window": window, "n_rows": len(d), "mean_gap": round(mean, 6),
                    "ci95_lo": round(lo, 6), "ci95_hi": round(hi, 6),
                    "model_wins": wins, "n_boot": N_BOOT, "seed": SEED})
        print(f"{window:10s} n={len(d):3d} gap {mean:+.4f}  CI [{lo:+.4f}, {hi:+.4f}]  "
              f"model wins {wins}/{len(d)}")

    write_csv(RESULTS_DIR / "bootstrap_gaps.csv",
              ["window", "n_rows", "mean_gap", "ci95_lo", "ci95_hi",
               "model_wins", "n_boot", "seed"], out)
    print(f"wrote {RESULTS_DIR / 'bootstrap_gaps.csv'} (replication checks OK)")


if __name__ == "__main__":
    main()
