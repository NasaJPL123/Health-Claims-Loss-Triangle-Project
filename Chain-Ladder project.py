import numpy as np
import pandas as pd

np.random.seed(42)  # makes random numbers reproducible

n_claims = 1000

# Accident month
accident_month = np.random.choice(
    pd.date_range("2023-01-01", "2023-12-01", freq="MS"),
    size=n_claims
)

# How many months after the accident did the claim get paid?
# Health claims pay out fast, so most lags are 0 or 1 month
lag_months = np.random.choice([0, 1, 2, 3, 4, 5], size=n_claims,
                               p=[0.50, 0.25, 0.12, 0.07, 0.04, 0.02])

# Claim amount (gamma right skewed)
paid_amount = np.round(np.random.gamma(shape=2, scale=500, size=n_claims), 2)

claims = pd.DataFrame({
    "accident_month": accident_month,
    "lag_months": lag_months,
    "paid_amount": paid_amount
})

# Convert to month periods for easier grouping later
claims["accident_period"] = claims["accident_month"].dt.to_period("M")
claims["paid_period"] = claims["accident_period"] + claims["lag_months"]

print(claims.head(n=10))
claims.to_csv("triangle-data.csv", index=False)
