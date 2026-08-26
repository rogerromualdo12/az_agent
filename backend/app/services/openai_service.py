import os

from openai import OpenAI

from app.config import settings
from app.models.customer import CustomerDetail, InsightResponse


class OpenAIService:
    def __init__(self) -> None:
        self._client: OpenAI | None = None
        self._api_key = ""

    def _get_client(self) -> OpenAI | None:
        key = (settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        if not key:
            return None
        if self._client is None or self._api_key != key:
            self._client = OpenAI(api_key=key)
            self._api_key = key
        return self._client

    def customer_insight(self, customer: CustomerDetail) -> InsightResponse:
        client = self._get_client()
        if client is None:
            return InsightResponse(
                customer_id=customer.customer_id,
                insight=(
                    "OPENAI_API_KEY no está configurada. "
                    "Agrega la clave en .env para generar un insight del digital twin."
                ),
            )

        recent = customer.transactions[:5]
        events = ", ".join(event.event_type for event in customer.life_events) or "ninguno"
        products = ", ".join(customer.products) or "ninguno"
        prompt = f"""
Eres un analista de un banco. Resume el digital twin de este cliente en 4-6 oraciones
y sugiere una próxima mejor acción comercial.

ID: {customer.customer_id}
Nombre: {customer.name}
Edad: {customer.age}
Ingreso: {customer.income}
Credit score: {customer.credit_score}
Productos: {products}
Riesgo de default: {customer.default_risk}
Riesgo de churn: {customer.churn_risk}
Propensity to buy: {customer.propensity_to_buy}
Eventos de vida: {events}
Últimas transacciones: {[(tx.transaction_type, tx.amount) for tx in recent]}
"""
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.4,
        )
        content = response.choices[0].message.content or "No se pudo generar el insight."
        return InsightResponse(customer_id=customer.customer_id, insight=content)


openai_service = OpenAIService()
