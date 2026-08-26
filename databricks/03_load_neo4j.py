import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
customers_path = DATA_DIR / "customers.csv"
transactions_path = DATA_DIR / "transactions.csv"
life_events_path = DATA_DIR / "life_events.csv"

for path in (customers_path, transactions_path, life_events_path):
    if not path.exists():
        raise FileNotFoundError(f"Falta {path}. Genera los CSV antes de cargar Neo4j.")

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
BATCH_SIZE = int(os.getenv("NEO4J_BATCH_SIZE", "500"))


def chunks(frame: pd.DataFrame, size: int):
    for start in range(0, len(frame), size):
        yield frame.iloc[start : start + size]


def load() -> None:
    customers = pd.read_csv(customers_path)
    transactions = pd.read_csv(transactions_path)
    life_events = pd.read_csv(life_events_path)
    
    customers["products"] = customers["products"].fillna("").astype(str)
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
            rows = batch.to_dict("records")
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
                    c.propensity_to_buy = toFloat(row.propensity_to_buy)
                WITH c, row
                FOREACH (
                    product_name IN [x IN split(coalesce(row.products, ""), ",") WHERE trim(x) <> "" | trim(x)] |
                    MERGE (p:Product {name: product_name})
                    MERGE (c)-[:HAS_PRODUCT]->(p)
                )
                """,
                rows=rows,
            )

        for batch in chunks(transactions, BATCH_SIZE):
            rows = batch.to_dict("records")
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
            rows = batch.to_dict("records")
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
        f"Cargado en Neo4j: {len(customers)} clientes, "
        f"{len(transactions)} transacciones, {len(life_events)} life events"
    )


if __name__ == "__main__":
    load()
