import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layers import BRONZE, ensure_layers

ensure_layers()
customers_path = BRONZE / "customers.csv"

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

transactions_path = BRONZE / "transactions.csv"
transactions_df.to_csv(transactions_path, index=False)
print(transactions_df.head().to_string())
print(f"\nTransacciones: {len(transactions_df)} -> {transactions_path}")
