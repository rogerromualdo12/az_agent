import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))

from faker import Faker

from layers import BRONZE, ensure_layers

ensure_layers()

fake = Faker()
NUM_CUSTOMERS = int(os.getenv("NUM_CUSTOMERS", "1000"))

customers = []
for i in range(NUM_CUSTOMERS):
    age = random.randint(18, 75)
    income = round(np.random.lognormal(mean=10.8, sigma=0.5))
    credit_score = int(np.clip(np.random.normal(680, 80), 300, 850))

    products = []
    if age > 21:
        products.append("Credit Card")
    if income > 30000:
        products.append("Savings Account")
    if income > 70000 and credit_score > 650:
        products.append("Mortgage")
    if income > 50000 and credit_score > 620:
        products.append("Personal Loan")

    default_risk = max(0.01, min(0.80, (700 - credit_score) / 1000))

    customers.append(
        {
            "customer_id": f"CUST{i:07d}",
            "name": fake.name(),
            "age": age,
            "income": income,
            "credit_score": credit_score,
            "products": ",".join(products),
            "default_risk": round(default_risk, 3),
            "churn_risk": round(float(np.random.beta(2, 8)), 3),
            "propensity_to_buy": round(float(np.random.beta(5, 2)), 3),
        }
    )

customers_df = pd.DataFrame(customers)
customers_path = BRONZE / "customers.csv"
customers_df.to_csv(customers_path, index=False)

life_events = []
for _, customer in customers_df.iterrows():
    if random.random() < 0.15:
        life_events.append({"customer_id": customer.customer_id, "event_type": "MARRIAGE"})
    if random.random() < 0.08:
        life_events.append({"customer_id": customer.customer_id, "event_type": "NEW_CHILD"})
    if random.random() < 0.10:
        life_events.append({"customer_id": customer.customer_id, "event_type": "NEW_JOB"})

life_events_df = pd.DataFrame(life_events)
life_events_path = BRONZE / "life_events.csv"
life_events_df.to_csv(life_events_path, index=False)

print(customers_df.head().to_string())
print(f"\nClientes: {len(customers_df)} -> {customers_path}")
print(f"Life events: {len(life_events_df)} -> {life_events_path}")
