"""Drop-one-group ablation of BOTH learners on the frozen one-touch test weeks.

Written 16 Nov 2026 after marker feedback: the original ablation
(model/results/ablation.csv, frozen 7 Nov) covered XGBoost only and never
isolated the momentum block. This script re-derives the full 2x5 grid from
the FROZEN panel at commit ae6edcc (the 7 Nov scoring commit), asserts the
full-model cells reproduce the frozen numbers exactly, and writes
model/results/ablation_full.csv. Diagnostic only: the ladder was chosen and
frozen before this ran; nothing here re-opens model selection.

Run:  .venv/bin/python model/ablate_full.py
"""

import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import (  # noqa: E402
    FEATURES, TRAIN_END, TEST_START, TEST_END, RESULTS_DIR,
    parse_row, ridge_fit, ridge_predict, xgboost_fit_predict, mae, write_csv,
)

FROZEN_COMMIT = "ae6edcc"
FROZEN_RIDGE_MAE = 0.126251    # model/results/test.csv
FROZEN_XGB_FULL_MAE = 0.131923  # model/results/ablation.csv, "full" row

MOMENTUM = ["wow_growth", "growth_4w", "growth_4w_missing", "median_4w", "mad_4w"]
GROUPS = [
    ("full", []),
    ("no_momentum", MOMENTUM),
    ("no_calendar", ["sale_this_week", "sale_next_week", "holiday_count"]),
    ("no_major_update", ["major_update", "days_since_major_update"]),
    ("no_peer", ["peer_median_growth"]),
]


def main() -> None:
    frozen_csv = subprocess.run(
        ["git", "show", f"{FROZEN_COMMIT}:data/processed/week_panel.csv"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    rows = [parse_row(r) for r in csv.DictReader(frozen_csv)]
    rows.sort(key=lambda r: (r["week_start"], r["appid"]))
    train = [r for r in rows if r["week_start"] <= TRAIN_END and r["log_growth"] is not None]
    test = [r for r in rows if TEST_START <= r["week_start"] <= TEST_END and r["log_growth"] is not None]
    assert len(train) == 192 and len(test) == 48, (len(train), len(test))
    y_train = [r["log_growth"] for r in train]
    y_test = [r["log_growth"] for r in test]
    baseline = mae(y_test, [0.0] * len(y_test))

    out = []
    for model_name in ("ridge", "xgboost"):
        for group, drop in GROUPS:
            feats = [f for f in FEATURES if f not in drop]
            X_tr = [[r["features"][k] for k in feats] for r in train]
            X_te = [[r["features"][k] for k in feats] for r in test]
            if model_name == "ridge":
                model = ridge_fit(X_tr, y_train)
                pred = ridge_predict(model, X_te)
            else:
                pred, _ = xgboost_fit_predict(X_tr, y_train, X_te)
            score = mae(y_test, pred)
            out.append({
                "model": model_name, "drop_group": group,
                "test_mae": round(score, 6),
                "ratio_to_baseline": round(score / baseline, 4),
            })
            print(f"{model_name:7s} {group:16s} test MAE {score:.4f} ratio {score / baseline:.3f}")

    cells = {(r["model"], r["drop_group"]): r["test_mae"] for r in out}
    assert abs(cells[("ridge", "full")] - FROZEN_RIDGE_MAE) < 1e-6, cells[("ridge", "full")]
    assert abs(cells[("xgboost", "full")] - FROZEN_XGB_FULL_MAE) < 1e-6, cells[("xgboost", "full")]
    for group in ("no_calendar", "no_peer", "no_major_update"):
        assert abs(cells[("xgboost", group)] - FROZEN_XGB_FULL_MAE) > 0  # sanity: not the full fit
    print("frozen replication checks OK (ridge full == 0.126251, xgboost full == 0.131923)")

    write_csv(RESULTS_DIR / "ablation_full.csv",
              ["model", "drop_group", "test_mae", "ratio_to_baseline"], out)
    print(f"wrote {RESULTS_DIR / 'ablation_full.csv'}")


if __name__ == "__main__":
    main()
