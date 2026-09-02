import json
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layers import GOLD, ROOT, SILVER

load_dotenv(ROOT / ".env")

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
BATCH_SIZE = int(os.getenv("NEO4J_BATCH_SIZE", "500"))


def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records"))


def chunks(frame: pd.DataFrame, size: int):
    for start in range(0, len(frame), size):
        yield frame.iloc[start : start + size]


def load() -> None:
    gold_path = GOLD / "customer_360.parquet"
    products_path = SILVER / "customer_products.parquet"
    transactions_path = SILVER / "transactions.parquet"
    events_path = SILVER / "life_events.parquet"
    for path in (gold_path, products_path, transactions_path, events_path):
        if not path.exists():
            raise FileNotFoundError(f"Falta {path}. Ejecuta 03_to_silver.py y 04_to_gold.py.")

    customers = pd.read_parquet(gold_path)
    products = pd.read_parquet(products_path)
    transactions = pd.read_parquet(transactions_path)
    life_events = pd.read_parquet(events_path)

    for frame in (customers, products, transactions, life_events):
        if "customer_id" in frame.columns:
            frame["customer_id"] = frame["customer_id"].astype(str)

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        session.run(
            "CREATE CONSTRAINT customer_id IF NOT EXISTS "
            "FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE"
        )
        session.run(
            "CREATE CONSTRAINT product_name IF NOT EXISTS "
            "FOR (p:Product) REQUIRE p.name IS UNIQUE"
        )

        for batch in chunks(customers, BATCH_SIZE):
            rows = records(batch)
            session.run(
                """
                UNWIND $rows AS row
                MERGE (c:Customer {customer_id: row.customer_id})
                SET c.name = row.name,
                    c.age = toInteger(row.age),
                    c.income = toFloat(row.income),
                    c.credit_score = toInteger(row.credit_score),
                    c.default_risk = toFloat(row.default_risk),
                    c.churn_risk = toFloat(row.churn_risk),
                    c.propensity_to_buy = toFloat(row.propensity_to_buy),
                    c.tx_count = toInteger(row.tx_count),
                    c.tx_sum = toFloat(row.tx_sum),
                    c.customer_value = toFloat(row.customer_value),
                    c.segment_id = toInteger(row.segment_id),
                    c.segment = row.segment
                """,
                rows=rows,
            )

        for batch in chunks(products, BATCH_SIZE):
            rows = records(batch)
            session.run(
                """
                UNWIND $rows AS row
                MATCH (c:Customer {customer_id: row.customer_id})
                MERGE (p:Product {name: row.product})
                MERGE (c)-[:HAS_PRODUCT]->(p)
                """,
                rows=rows,
            )

        for batch in chunks(transactions, BATCH_SIZE):
            rows = records(batch)
            session.run(
                """
                UNWIND $rows AS row
                MATCH (c:Customer {customer_id: row.customer_id})
                CREATE (t:Transaction {
                    amount: toFloat(row.amount),
                    transaction_type: row.transaction_type,
                    timestamp: row.timestamp
                })
                MERGE (c)-[:MADE]->(t)
                """,
                rows=rows,
            )

        for batch in chunks(life_events, BATCH_SIZE):
            rows = records(batch)
            session.run(
                """
                UNWIND $rows AS row
                MATCH (c:Customer {customer_id: row.customer_id})
                CREATE (e:LifeEvent {event_type: row.event_type})
                MERGE (c)-[:HAD_EVENT]->(e)
                """,
                rows=rows,
            )

    driver.close()
    print(
        f"Cargado en Neo4j desde gold/silver: {len(customers)} clientes, "
        f"{len(transactions)} transacciones, {len(life_events)} life events"
    )


if __name__ == "__main__":
    load()
