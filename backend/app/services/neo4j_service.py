from neo4j import GraphDatabase

from app.config import settings
from app.models.customer import Customer, CustomerDetail, LifeEvent, Transaction


class Neo4jService:
    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self) -> None:
        self._driver.close()

    def list_customers(self, limit: int = 50, offset: int = 0, q: str = "") -> list[Customer]:
        query = """
        MATCH (c:Customer)
        WHERE $q = "" OR toLower(c.name) CONTAINS toLower($q)
           OR toLower(c.customer_id) CONTAINS toLower($q)
        OPTIONAL MATCH (c)-[:HAS_PRODUCT]->(p:Product)
        WITH c, collect(p.name) AS products
        RETURN c, products
        ORDER BY c.customer_id
        SKIP $offset
        LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(query, q=q, offset=offset, limit=limit)
            return [self._to_customer(record["c"], record["products"]) for record in result]

    def get_customer(self, customer_id: str) -> CustomerDetail | None:
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        OPTIONAL MATCH (c)-[:HAS_PRODUCT]->(p:Product)
        OPTIONAL MATCH (c)-[:MADE]->(t:Transaction)
        OPTIONAL MATCH (c)-[:HAD_EVENT]->(e:LifeEvent)
        RETURN c,
               collect(DISTINCT p.name) AS products,
               collect(DISTINCT t) AS transactions,
               collect(DISTINCT e) AS events
        """
        with self._driver.session() as session:
            record = session.run(query, customer_id=customer_id).single()
            if record is None or record["c"] is None:
                return None

            transactions = [
                Transaction(
                    customer_id=customer_id,
                    amount=tx.get("amount", 0),
                    transaction_type=tx.get("transaction_type", ""),
                    timestamp=str(tx.get("timestamp", "")),
                )
                for tx in record["transactions"]
                if tx is not None
            ]
            transactions.sort(key=lambda item: item.timestamp, reverse=True)

            events = [
                LifeEvent(customer_id=customer_id, event_type=event.get("event_type", ""))
                for event in record["events"]
                if event is not None
            ]

            customer = self._to_customer(record["c"], record["products"])
            return CustomerDetail(
                **customer.model_dump(),
                transactions=transactions[:25],
                life_events=events,
            )

    def get_graph(self, customer_id: str) -> dict:
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        OPTIONAL MATCH (c)-[r]->(n)
        RETURN c,
               collect(DISTINCT {type: type(r), node: n, labels: labels(n)}) AS neighbors
        """
        with self._driver.session() as session:
            record = session.run(query, customer_id=customer_id).single()
            if record is None or record["c"] is None:
                return {"nodes": [], "edges": []}

            customer = record["c"]
            nodes = [
                {
                    "id": customer["customer_id"],
                    "label": customer["name"],
                    "type": "Customer",
                }
            ]
            edges = []
            for neighbor in record["neighbors"]:
                node = neighbor.get("node")
                if node is None:
                    continue
                labels = neighbor.get("labels") or []
                node_type = labels[0] if labels else "Node"
                node_id = (
                    node.get("name")
                    or node.get("transaction_type")
                    or node.get("event_type")
                    or str(node.element_id)
                )
                unique_id = f"{node_type}:{node.element_id}"
                nodes.append(
                    {
                        "id": unique_id,
                        "label": str(node_id),
                        "type": node_type,
                    }
                )
                edges.append(
                    {
                        "source": customer["customer_id"],
                        "target": unique_id,
                        "type": neighbor.get("type") or "RELATED",
                    }
                )
            return {"nodes": nodes, "edges": edges}

    @staticmethod
    def _to_customer(node, products: list[str]) -> Customer:
        return Customer(
            customer_id=node["customer_id"],
            name=node["name"],
            age=int(node.get("age") or 0),
            income=float(node.get("income") or 0),
            credit_score=int(node.get("credit_score") or 0),
            products=[product for product in products if product],
            default_risk=float(node.get("default_risk") or 0),
            churn_risk=float(node.get("churn_risk") or 0),
            propensity_to_buy=float(node.get("propensity_to_buy") or 0),
        )


neo4j_service = Neo4jService()
