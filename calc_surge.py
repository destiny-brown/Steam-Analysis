import pandas as pd


panel = pd.read_csv("data/processed/week_panel.csv")
training = panel[panel["week_start"] <= "2026-09-28"].copy()

surges = (
    (training["next_peak"] >= 1.5 * training["peak"])
    & (training["next_peak"] >= training["median_4w"] + 2 * training["mad_4w"])
)

total_rows = len(training)
surge_count = int(surges.sum())
base_rate = surge_count / total_rows * 100

print(f"Total training rows: {total_rows}")
print(f"Surge count: {surge_count}")
print(f"Base rate: {base_rate:.1f}%")
