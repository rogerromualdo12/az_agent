# Financial Digital Twin

Hobby project that generates synthetic bank customers, loads them into Neo4j, and exposes a FastAPI + frontend to inspect each customer's digital twin.

```
financial-digital-twin/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/customers.py
│   │   ├── services/neo4j_service.py
│   │   ├── services/openai_service.py
│   │   └── models/customer.py
│   └── requirements.txt
├── databricks/
│   ├── 01_generate_customers.py
│   ├── 02_generate_transactions.py
│   ├── 03_load_neo4j.py
│   └── 04_segment_customers.py
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
docker compose up -d neo4j
python databricks/01_generate_customers.py
python databricks/02_generate_transactions.py
python databricks/03_load_neo4j.py
python databricks/04_segment_customers.py
cd backend && uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
python -m http.server 5500
```

Open http://127.0.0.1:5500 and http://localhost:7474 for Neo4j Browser (`neo4j` / `password`).

Optional: set `OPENAI_API_KEY` in `.env` to generate customer insights.

## Local scale

Defaults are sized for a laptop (`NUM_CUSTOMERS=1000`, `NUM_TRANSACTIONS=10000`). Raise them in `.env` before generating data if you want the original 10k / 500k volumes.

`04_segment_customers.py` clusters customers with K-Means on default risk and transaction behavior, writes `data/customer_segments.csv`, and saves charts in `data/plots/`.
