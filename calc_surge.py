import pandas as pd
import matplotlib.pyplot as plt


panel = pd.read_csv("data/processed/week_panel.csv")
training = panel[panel["week_start"] <= "2026-09-28"].copy()

surges = (
    (training["next_peak"] >= 1.5 * training["peak"])
    & (training["next_peak"] >= training["median_4w"] + 2 * training["mad_4w"])
)

total_rows = len(training)
surge_count = int(surges.sum())
base_rate = surge_count / total_rows * 100

growth = training["log_growth"].dropna()
surge_growth = training.loc[surges, "log_growth"].dropna()

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(growth, bins=20, color="steelblue", edgecolor="white", label="Training weeks")
ax.scatter(
    surge_growth,
    [0.5] * len(surge_growth),
    color="crimson",
    marker="|",
    s=180,
    linewidths=2,
    label="Surge rows",
)
ax.set_title("Training-week log-growth and surge rows")
ax.set_xlabel("log(next week peak) - log(this week peak)")
ax.set_ylabel("Number of game-weeks")
ax.legend()
fig.tight_layout()
fig.savefig("model/results/log_growth_histogram.png", dpi=150)
plt.close(fig)

print(f"Total training rows: {total_rows}")
print(f"Surge count: {surge_count}")
print(f"Base rate: {base_rate:.1f}%")
print("Saved plot: model/results/log_growth_histogram.png")
