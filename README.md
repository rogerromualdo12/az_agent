# Financial Digital Twin

Hobby project that generates synthetic bank customers, processes them through a medallion lakehouse (bronze / silver / gold), loads a Neo4j graph, and exposes a FastAPI + frontend to inspect each customer's digital twin.

```
financial-digital-twin/
├── backend/
├── databricks/
│   ├── 01_generate_customers.py   # → bronze
│   ├── 02_generate_transactions.py
│   ├── 03_to_silver.py
│   ├── 04_to_gold.py              # 360 + K-Means + plots
│   └── 05_load_neo4j.py           # gold + silver → graph
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── frontend/
├── docker-compose.yml
└── .env
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
docker compose up -d neo4j --wait
python databricks/01_generate_customers.py
python databricks/02_generate_transactions.py
python databricks/03_to_silver.py
python databricks/04_to_gold.py
python databricks/05_load_neo4j.py
cd backend && uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
python -m http.server 5500
```

Open http://127.0.0.1:5500 and http://localhost:7474 for Neo4j Browser (`neo4j` / `password`).

Optional: set `OPENAI_API_KEY` in `.env` to generate customer insights.

## Medallion layers

| Layer | What it holds | Writer |
|---|---|---|
| **Bronze** | Raw CSV from the generator (or a future company dump) | 01, 02 |
| **Silver** | Typed parquet, cleaned products, timestamps | 03 |
| **Gold** | Customer 360, `customer_value`, K-Means `segment`, plots | 04 |

Neo4j is serving, not a lakehouse layer. Job 05 reads gold (party/metrics) and silver (transactions, products, events).

## Local scale

Defaults are sized for a laptop (`NUM_CUSTOMERS=1000`, `NUM_TRANSACTIONS=10000`). Raise them in `.env` before generating data if you want the original 10k / 500k volumes.
