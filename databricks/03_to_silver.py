import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layers import BRONZE, SILVER, ensure_layers


def require_bronze(*names: str) -> None:
    missing = [BRONZE / name for name in names if not (BRONZE / name).exists()]
    if missing:
        raise FileNotFoundError(f"Falta bronze: {missing}. Ejecuta 01 y 02.")


def clean_customers(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw.copy()
    df["products"] = df["products"].fillna("").astype(str)
    df["customer_id"] = df["customer_id"].astype(str)
    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype(int)
    df["income"] = pd.to_numeric(df["income"], errors="coerce").fillna(0)
    df["credit_score"] = pd.to_numeric(df["credit_score"], errors="coerce").fillna(0).astype(int)
    for col in ("default_risk", "churn_risk", "propensity_to_buy"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    exploded = (
        df.assign(product=df["products"].str.split(","))
        .explode("product")
    )
    exploded["product"] = exploded["product"].str.strip()
    products = exploded.loc[exploded["product"] != "", ["customer_id", "product"]].drop_duplicates()
    df["products"] = df["products"].str.split(",").apply(
        lambda items: [item.strip() for item in items if item.strip()]
    )
    return df, products


def clean_transactions(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["customer_id"] = df["customer_id"].astype(str)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["transaction_type"] = df["transaction_type"].fillna("UNKNOWN").astype(str)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df["timestamp"] = df["timestamp"].fillna("")
    return df


def clean_life_events(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["customer_id"] = df["customer_id"].astype(str)
    df["event_type"] = df["event_type"].fillna("").astype(str).str.strip()
    return df.loc[df["event_type"] != ""].copy()


def main() -> None:
    ensure_layers()
    require_bronze("customers.csv", "transactions.csv", "life_events.csv")

    customers, customer_products = clean_customers(pd.read_csv(BRONZE / "customers.csv"))
    transactions = clean_transactions(pd.read_csv(BRONZE / "transactions.csv"))
    life_events = clean_life_events(pd.read_csv(BRONZE / "life_events.csv"))

    customers.to_parquet(SILVER / "customers.parquet", index=False)
    customer_products.to_parquet(SILVER / "customer_products.parquet", index=False)
    transactions.to_parquet(SILVER / "transactions.parquet", index=False)
    life_events.to_parquet(SILVER / "life_events.parquet", index=False)

    print(f"Silver customers: {len(customers)}")
    print(f"Silver products: {len(customer_products)}")
    print(f"Silver transactions: {len(transactions)}")
    print(f"Silver life events: {len(life_events)}")
    print(f"-> {SILVER}")


if __name__ == "__main__":
    main()
