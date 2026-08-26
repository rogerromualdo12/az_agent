from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: str
    name: str
    age: int
    income: float
    credit_score: int
    products: list[str] = Field(default_factory=list)
    default_risk: float
    churn_risk: float
    propensity_to_buy: float


class Transaction(BaseModel):
    customer_id: str
    amount: float
    transaction_type: str
    timestamp: str


class LifeEvent(BaseModel):
    customer_id: str
    event_type: str


class CustomerDetail(Customer):
    transactions: list[Transaction] = Field(default_factory=list)
    life_events: list[LifeEvent] = Field(default_factory=list)


class InsightResponse(BaseModel):
    customer_id: str
    insight: str
