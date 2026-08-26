import pandas as pd
import numpy as np
from faker import Faker
import random

fake = Faker()

NUM_CUSTOMERS = 10000

customers = []

for i in range(NUM_CUSTOMERS):

    age = random.randint(18, 75)

    income = np.random.lognormal(
        mean=10.8,
        sigma=0.5
    )

    income = round(income)

    credit_score = int(
        np.clip(
            np.random.normal(680, 80),
            300,
            850
        )
    )

    products = []

    if age > 21:
        products.append("Credit Card")

    if income > 30000:
        products.append("Savings Account")

    if income > 70000 and credit_score > 650:
        products.append("Mortgage")

    if income > 50000 and credit_score > 620:
        products.append("Personal Loan")

    default_risk = max(
        0.01,
        min(
            0.80,
            (700 - credit_score) / 1000
        )
    )

    churn_risk = np.random.beta(2, 8)

    propensity_to_buy = np.random.beta(5, 2)

    customers.append({
        "customer_id": f"CUST{i:07d}",
        "name": fake.name(),
        "age": age,
        "income": income,
        "credit_score": credit_score,
        "products": ",".join(products),
        "default_risk": round(default_risk, 3),
        "churn_risk": round(churn_risk, 3),
        "propensity_to_buy": round(propensity_to_buy, 3)
    })

customers_df = pd.DataFrame(customers)

print(customers_df.head().to_string())
print(f"\nFilas: {len(customers_df)}")

customers_df.to_csv("customers.csv", index=False)
print("Guardado en customers.csv")
print(customers_df.head())