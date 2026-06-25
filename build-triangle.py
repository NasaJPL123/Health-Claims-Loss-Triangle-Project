import numpy as np
import pandas as pd

# ── Step 1: Load claims data ──────────────────────────────────────────
claims = pd.read_csv("triangle-data.csv")

# ── Step 2: Build incremental triangle ───────────────────────────────
incremental = claims.pivot_table(
    index="accident_period",
    columns="lag_months",
    values="paid_amount",
    aggfunc="sum"
)

# ── Step 3: Build cumulative triangle ────────────────────────────────
cumulative = incremental.cumsum(axis=1)

print("=== INCREMENTAL TRIANGLE ===")
print(incremental.round(0))

# Evaluation date - what we know as of this point in time
eval_date = pd.Period("2023-10", "M")

# Mask future cells - convert index and columns to periods for comparison
for acc_period in cumulative.index:
    for lag in cumulative.columns:
        if pd.Period(acc_period, "M") + lag > eval_date:
            cumulative.loc[acc_period, lag] = np.nan
            incremental.loc[acc_period, lag] = np.nan

print("=== CUMULATIVE TRIANGLE (masked) ===")
print(cumulative.round(0))

age_to_age = pd.DataFrame(index=cumulative.index)

for i in range(len(cumulative.columns) - 1):
    col_current = cumulative.columns[i]
    col_next = cumulative.columns[i + 1]
    
    # Ratio of next period to current period for each accident year
    age_to_age[f"{col_current}→{col_next}"] = (
        cumulative[col_next] / cumulative[col_current]
    )

print("=== AGE-TO-AGE FACTORS ===")
print(age_to_age.round(4))
print()

# Simple average of each column (ignoring NaN rows automatically)
selected_factors = age_to_age.mean()
print("=== SELECTED FACTORS (simple average) ===")
print(selected_factors.round(4))