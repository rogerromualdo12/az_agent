import os
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
customers_path = DATA_DIR / "customers.csv"

if not customers_path.exists():
    raise FileNotFoundError("Ejecuta primero databricks/01_generate_customers.py")

fake = Faker()
customers_df = pd.read_csv(customers_path)
NUM_TRANSACTIONS = int(os.getenv("NUM_TRANSACTIONS", "10000"))

sampled = customers_df.sample(n=NUM_TRANSACTIONS, replace=True)
transactions_df = pd.DataFrame(
    {
        "customer_id": sampled["customer_id"].to_numpy(),
        "amount": np.round(np.random.exponential(120, size=NUM_TRANSACTIONS), 2),
        "transaction_type": np.random.choice(
            ["PURCHASE", "ATM", "TRANSFER", "PAYMENT"],
            size=NUM_TRANSACTIONS,
        ),
        "timestamp": [
            fake.date_time_between(start_date="-365d", end_date="now")
            for _ in range(NUM_TRANSACTIONS)
        ],
    }
)

transactions_path = DATA_DIR / "transactions.csv"
transactions_df.to_csv(transactions_path, index=False)
print(transactions_df.head().to_string())
print(f"\nTransacciones: {len(transactions_df)} -> {transactions_path}")
