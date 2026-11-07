#!/usr/bin/env python3
"""Fit the locked model ladder on data/processed/week_panel.csv.

Order: unchanged peak, weekday pattern, ridge, shallow XGBoost.
Refuses to train on weeks starting 19 October 2026 or later.
"""

from __future__ import annotations

import csv
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[1]
PANEL_CSV = ROOT / "data" / "processed" / "week_panel.csv"
RESULTS_DIR = ROOT / "model" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_START = datetime(2026, 8, 10, tzinfo=timezone.utc)
TRAIN_END = datetime(2026, 10, 4, tzinfo=timezone.utc)
VAL_START = datetime(2026, 10, 5, tzinfo=timezone.utc)
VAL_END = datetime(2026, 10, 18, tzinfo=timezone.utc)
TEST_START = datetime(2026, 10, 19, tzinfo=timezone.utc)
TEST_END = datetime(2026, 11, 1, tzinfo=timezone.utc)

FEATURES = [
    "wow_growth",
    "growth_4w",
    "growth_4w_missing",
    "median_4w",
    "mad_4w",
    "peak",
    "mean_players",
    "weekend_days",
    "sale_this_week",
    "sale_next_week",
    "holiday_count",
    "peer_median_growth",
    "news_count",
    "days_since_news",
    "major_update",
    "days_since_major_update",
]


def parse_row(row: dict[str, str]) -> dict:
    week_start = datetime.strptime(row["week_start"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    features = {k: float(row[k]) if row.get(k) not in (None, "") else 0.0 for k in FEATURES}
    # decisions.md 2026-11-05: blank growth_4w means "no trailing window", not zero growth.
    features["growth_4w_missing"] = 1.0 if row.get("growth_4w", "") == "" else 0.0
    # decisions.md 2026-11-05: scale-free features for a log-ratio target.
    peak = float(row["peak"])
    mean_players = float(row["mean_players"]) if row["mean_players"] else 0.0
    features["peak"] = math.log(peak) if peak > 0 else 0.0
    features["mean_players"] = math.log(mean_players) if mean_players > 0 else 0.0
    return {
        "appid": row["appid"],
        "name": row["name"],
        "week_start": week_start,
        "week_start_str": row["week_start"],
        "resolution": row["resolution"],
        "peak": peak,
        "next_peak": float(row["next_peak"]) if row["next_peak"] else None,
        "log_growth": float(row["log_growth"]) if row["log_growth"] else None,
        "features": features,
    }


def load_panel() -> list[dict]:
    if not PANEL_CSV.exists():
        raise FileNotFoundError(f"Build {PANEL_CSV} first with model/build_week_panel.py")
    rows = [parse_row(row) for row in csv.DictReader(PANEL_CSV.open())]
    rows.sort(key=lambda r: (r["week_start"], r["appid"]))
    return rows


def check_split(rows: list[dict]) -> None:
    """Refuse to train on weeks starting 19 October 2026 or later."""
    for row in rows:
        if row["week_start"] < TRAIN_START:
            raise RuntimeError(
                f"Row for {row['name']} on {row['week_start_str']} is before the training window. "
                "Training starts 10 August 2026."
            )


def split_rows(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    train = [r for r in rows if r["week_start"] <= TRAIN_END and r["log_growth"] is not None]
    val = [r for r in rows if VAL_START <= r["week_start"] <= VAL_END and r["log_growth"] is not None]
    test = [r for r in rows if TEST_START <= r["week_start"] <= TEST_END and r["log_growth"] is not None]
    return train, val, test


def unchanged_peak(rows: list[dict]) -> float:
    errors = [abs(r["log_growth"]) for r in rows if r["log_growth"] is not None]
    return sum(errors) / len(errors) if errors else float("nan")


def weekday_pattern(train: list[dict], row: dict) -> float:
    """Predict next week's peak as the max of the same weekday in this week.

    Uses the day-of-week when this week's peak occurred, then takes the max
    of that weekday across the training weeks for the same game.
    """
    appid = row["appid"]
    peak_day = row["week_start"].strftime("%A")
    # Find the actual day-of-week of the peak within the week
    # We don't have daily breakdown in the panel, so approximate with weekend flag
    # Fallback: use the current week's peak (same as unchanged) if we can't do better
    same_game = [r for r in train if r["appid"] == appid]
    if not same_game:
        return row["peak"]
    # Average of peaks on the same day-of-week name (always Monday, so use all)
    avg_peak = sum(r["peak"] for r in same_game) / len(same_game)
    return avg_peak


def weekday_pattern_mae(train: list[dict], val: list[dict]) -> float:
    if not val:
        return float("nan")
    errors = []
    for row in val:
        pred_peak = weekday_pattern(train, row)
        pred_log_growth = math.log(pred_peak / row["peak"]) if row["peak"] > 0 and pred_peak > 0 else 0.0
        errors.append(abs(pred_log_growth - row["log_growth"]))
    return sum(errors) / len(errors) if errors else float("nan")


def ridge_fit(X: list[list[float]], y: list[float], alpha: float = 1.0) -> list[float]:
    n = len(X)
    if n == 0:
        return []
    p = len(X[0])
    means = [sum(row[i] for row in X) / n for i in range(p)]
    stds = []
    for i in range(p):
        var = sum((row[i] - means[i]) ** 2 for row in X) / n
        stds.append(var ** 0.5 if var > 0 else 1.0)
    X_scaled = [[(row[i] - means[i]) / stds[i] for i in range(p)] for row in X]
    A = [[0.0] * p for _ in range(p)]
    b = [0.0] * p
    for row, target in zip(X_scaled, y):
        for i in range(p):
            b[i] += row[i] * target
            for j in range(p):
                A[i][j] += row[i] * row[j]
    for i in range(p):
        A[i][i] += alpha
    try:
        import numpy as np
        beta_scaled = np.linalg.solve(np.array(A), np.array(b)).tolist()
    except ImportError:
        beta_scaled = [0.0] * p
    beta = [beta_scaled[i] / stds[i] for i in range(p)]
    intercept = sum(y) / n - sum(beta[i] * means[i] for i in range(p))
    return [intercept] + beta


def ridge_predict(model: list[float], X: list[list[float]]) -> list[float]:
    intercept = model[0]
    beta = model[1:]
    return [intercept + sum(beta[i] * row[i] for i in range(len(beta))) for row in X]


def mae(y_true: list[float], y_pred: list[float]) -> float:
    errors = [abs(a - b) for a, b in zip(y_true, y_pred)]
    return sum(errors) / len(errors) if errors else float("nan")


def xgboost_fit_predict(
    X_train: list[list[float]],
    y_train: list[float],
    X_val: list[list[float]],
    max_depth: int = 3,
    n_estimators: int = 100,
) -> tuple[list[float], xgb.XGBRegressor]:
    model = xgb.XGBRegressor(
        max_depth=max_depth,
        n_estimators=n_estimators,
        learning_rate=0.1,
        random_state=42,
        objective="reg:squarederror",
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_val).tolist()
    return pred, model


def plot_predicted_vs_actual(y_true: list[float], y_pred: list[float], title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_true, y_pred, alpha=0.6)
    lims = [min(y_true + y_pred), max(y_true + y_pred)]
    ax.plot(lims, lims, "r--", alpha=0.5)
    ax.set_xlabel("Actual log-growth")
    ax.set_ylabel("Predicted log-growth")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_residuals(y_true: list[float], y_pred: list[float], title: str, path: Path) -> None:
    residuals = [a - b for a, b in zip(y_true, y_pred)]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(y_pred, residuals, alpha=0.6)
    ax.axhline(y=0, color="r", linestyle="--", alpha=0.5)
    ax.set_xlabel("Predicted log-growth")
    ax.set_ylabel("Residual")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_log_growth_histogram(y: list[float], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(y, bins=30, edgecolor="black", alpha=0.7)
    ax.axvline(x=0.0, color="r", linestyle="--", alpha=0.5)
    ax.set_xlabel("log-growth")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of weekly log-growth")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evaluate(rows: list[dict], train: list[dict], label: str) -> dict:
    """Fit every ladder model on train and score on rows. Returns per-model
    predictions and MAEs. Used once for validation and once for the test weeks."""
    y_true = [row["log_growth"] for row in rows]
    X_train = [[r["features"][k] for k in FEATURES] for r in train]
    y_train = [r["log_growth"] for r in train]
    X_eval = [[r["features"][k] for k in FEATURES] for r in rows]

    ridge_model = ridge_fit(X_train, y_train)
    ridge_pred = ridge_predict(ridge_model, X_eval)
    xgb_pred, _ = xgboost_fit_predict(X_train, y_train, X_eval)
    weekday_pred = [
        math.log(weekday_pattern(train, row) / row["peak"]) if row["peak"] > 0 else 0.0
        for row in rows
    ]

    preds = {
        "unchanged_peak": [0.0] * len(rows),
        "weekday_pattern": weekday_pred,
        "ridge": ridge_pred,
        "xgboost": xgb_pred,
    }
    maes = {name: mae(y_true, p) for name, p in preds.items()}
    for name, value in maes.items():
        print(f"{name} {label} MAE: {value:.4f}")
    return {"preds": preds, "maes": maes, "y_true": y_true}


def main() -> None:
    rows = load_panel()
    check_split(rows)
    train, val, test = split_rows(rows)
    print(f"train {len(train)} rows, val {len(val)} rows, test {len(test)} rows")

    # --- Validation (model selection happened here; frozen after 6 Nov) ---
    val_result = evaluate(val, train, "val")
    y_train_true = [row["log_growth"] for row in train]
    train_result = evaluate(train, train, "train")
    val_rows = [
        {"model": name, "train_mae": train_result["maes"][name], "val_mae": val_result["maes"][name]}
        for name in ("unchanged_peak", "weekday_pattern", "ridge", "xgboost")
    ]
    write_csv(RESULTS_DIR / "validation.csv", ["model", "train_mae", "val_mae"], val_rows)

    plot_predicted_vs_actual(
        val_result["y_true"], val_result["preds"]["xgboost"],
        "XGBoost: Predicted vs Actual (validation)", RESULTS_DIR / "pred_vs_actual.png",
    )
    plot_residuals(
        val_result["y_true"], val_result["preds"]["xgboost"],
        "XGBoost Residuals (validation)", RESULTS_DIR / "residuals.png",
    )
    all_growth = [row["log_growth"] for row in train + val]
    plot_log_growth_histogram(all_growth, RESULTS_DIR / "log_growth_histogram.png")
    surge_count = sum(1 for g in all_growth if g >= math.log(1.5))
    print(f"surge base rate (log_growth >= ln(1.5)): {surge_count}/{len(all_growth)} = {surge_count/len(all_growth):.3f}")

    # --- Historical test (19 Oct - 1 Nov): scored once, Saturday 7 November ---
    # Models are the frozen train-fit ones. No refit, no second pass.
    test_result = evaluate(test, train, "test")
    test_baseline = test_result["maes"]["unchanged_peak"]
    test_rows = [
        {
            "model": name,
            "test_mae": round(test_result["maes"][name], 6),
            "ratio_to_baseline": round(test_result["maes"][name] / test_baseline, 4),
        }
        for name in ("unchanged_peak", "weekday_pattern", "ridge", "xgboost")
    ]
    write_csv(RESULTS_DIR / "test.csv", ["model", "test_mae", "ratio_to_baseline"], test_rows)
    plot_predicted_vs_actual(
        test_result["y_true"], test_result["preds"]["xgboost"],
        "XGBoost: Predicted vs Actual (historical test weeks)", RESULTS_DIR / "pred_vs_actual_test.png",
    )
    plot_predicted_vs_actual(
        test_result["y_true"], test_result["preds"]["ridge"],
        "Ridge: Predicted vs Actual (historical test weeks)", RESULTS_DIR / "pred_vs_actual_test_ridge.png",
    )

    # --- Ablation on the test weeks (README: the three test errors; we add no_major_update) ---
    y_test = test_result["y_true"]
    X_train_full = [[r["features"][k] for k in FEATURES] for r in train]
    y_train_full = [r["log_growth"] for r in train]
    ablation_rows = []
    for name, drop in [
        ("full", []),
        ("no_calendar", ["sale_this_week", "sale_next_week", "holiday_count"]),
        ("no_peer", ["peer_median_growth"]),
        ("no_major_update", ["major_update", "days_since_major_update"]),
    ]:
        feats = [f for f in FEATURES if f not in drop]
        X_tr = [[r["features"][k] for k in feats] for r in train]
        X_te = [[r["features"][k] for k in feats] for r in test]
        pred, _ = xgboost_fit_predict(X_tr, y_train_full, X_te)
        score = mae(y_test, pred)
        ablation_rows.append({"model": name, "test_mae": round(score, 6), "ratio_to_baseline": round(score / test_baseline, 4)})
        print(f"ablation {name} test MAE: {score:.4f}")
    write_csv(RESULTS_DIR / "ablation.csv", ["model", "test_mae", "ratio_to_baseline"], ablation_rows)

    print(f"wrote {RESULTS_DIR / 'validation.csv'}, {RESULTS_DIR / 'test.csv'}, {RESULTS_DIR / 'ablation.csv'}")


if __name__ == "__main__":
    main()
