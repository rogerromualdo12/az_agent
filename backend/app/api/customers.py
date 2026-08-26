from fastapi import APIRouter, HTTPException, Query

from app.models.customer import Customer, CustomerDetail, InsightResponse
from app.services.neo4j_service import neo4j_service
from app.services.openai_service import openai_service

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=list[Customer])
def list_customers(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    q: str = Query(default=""),
) -> list[Customer]:
    return neo4j_service.list_customers(limit=limit, offset=offset, q=q)


@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: str) -> CustomerDetail:
    customer = neo4j_service.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/graph")
def get_customer_graph(customer_id: str) -> dict:
    graph = neo4j_service.get_graph(customer_id)
    if not graph["nodes"]:
        raise HTTPException(status_code=404, detail="Customer not found")
    return graph


@router.post("/{customer_id}/insight", response_model=InsightResponse)
def get_customer_insight(customer_id: str) -> InsightResponse:
    customer = neo4j_service.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return openai_service.customer_insight(customer)
