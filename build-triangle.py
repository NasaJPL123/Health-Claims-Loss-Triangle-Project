import numpy as np
import pandas as pd

# ── Step 1 Load claims data ──────────────────────────────────────────
claims = pd.read_csv("triangle-data.csv")

# ── Step 2 Build incremental triangle ───────────────────────────────
incremental = claims.pivot_table(
    index="accident_period",
    columns="lag_months",
    values="paid_amount",
    aggfunc="sum"
)

# ── Step 3 Build cumulative triangle ────────────────────────────────
cumulative = incremental.cumsum(axis=1)

print("=== INCREMENTAL TRIANGLE ===")
print(incremental.round(0))

# Evaluation date 
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

# ── Step 5: CDF vector ────────────────────────────────────────────────
factors = selected_factors.values

cdfs = []
for i in range(len(factors)):
    cdf = np.prod(factors[i:])
    cdfs.append(cdf)

cdf_series = pd.Series(cdfs, index=cumulative.columns[:-1])
print()
print("=== CDF (Cumulative Development Factors) ===")
print(cdf_series.round(4))

# ── Step 6: Project ultimates ─────────────────────────────────────────
latest_diagonal = cumulative.ffill(axis=1).iloc[:, -1]
latest_lag = cumulative.notna().sum(axis=1) - 1
cdf_lookup = latest_lag.map(lambda x: cdf_series.iloc[x] if x < len(cdf_series) else 1.0)
ultimates = latest_diagonal * cdf_lookup

print()
print("=== PROJECTED ULTIMATES ===")
print(ultimates.round(0))

# ── Step 7: IBNR ──────────────────────────────────────────────────────
ibnr = ultimates - latest_diagonal

print()
print("=== IBNR BY ACCIDENT PERIOD ===")
print(ibnr.round(0))
print()
print(f"=== TOTAL IBNR RESERVE: ${ibnr.sum():,.0f} ===")

# ── Step 8: Export to Excel ───────────────────────────────────────────
with pd.ExcelWriter("loss_triangle.xlsx", engine="openpyxl") as writer:

    # Tab 1: Incremental triangle
    incremental.to_excel(writer, sheet_name="Incremental Triangle")

    # Tab 2: Cumulative triangle
    cumulative.to_excel(writer, sheet_name="Cumulative Triangle")

    # Tab 3: Age-to-age factors + selected
    age_to_age_export = age_to_age.copy()
    age_to_age_export.loc["Selected"] = selected_factors
    age_to_age_export.to_excel(writer, sheet_name="Age-to-Age Factors")

    # Tab 4: IBNR summary
    summary = pd.DataFrame({
        "Latest Diagonal": latest_diagonal,
        "CDF Applied": cdf_lookup,
        "Projected Ultimate": ultimates,
        "IBNR": ibnr
    })
    summary.loc["Total"] = summary.sum()
    summary.to_excel(writer, sheet_name="IBNR Summary")
