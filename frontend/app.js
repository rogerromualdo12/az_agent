const API = "http://localhost:8000";

const listEl = document.getElementById("customer-list");
const detailEl = document.getElementById("customer-detail");
const insightEl = document.getElementById("insight");
const insightBtn = document.getElementById("insight-btn");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search");

let selectedId = null;

async function fetchCustomers(q = "") {
  const response = await fetch(`${API}/api/customers?limit=40&q=${encodeURIComponent(q)}`);
  if (!response.ok) {
    throw new Error("No se pudieron cargar los clientes. ¿Está Neo4j y el backend arriba?");
  }
  return response.json();
}

function renderList(customers) {
  if (!customers.length) {
    listEl.textContent = "Sin resultados";
    return;
  }

  listEl.innerHTML = "";
  customers.forEach((customer) => {
    const button = document.createElement("button");
    button.type = "button";
    button.innerHTML = `<span>${customer.name}</span><span class="muted">${customer.customer_id}</span>`;
    button.addEventListener("click", () => showCustomer(customer.customer_id));
    listEl.appendChild(button);
  });
}

async function showCustomer(customerId) {
  selectedId = customerId;
  insightEl.textContent = "";
  const response = await fetch(`${API}/api/customers/${customerId}`);
  if (!response.ok) {
    detailEl.textContent = "Cliente no encontrado";
    return;
  }

  const customer = await response.json();
  const products = customer.products.join(", ") || "Ninguno";
  const events = customer.life_events.map((event) => event.event_type).join(", ") || "Ninguno";
  const txs = customer.transactions
    .slice(0, 8)
    .map((tx) => `${tx.transaction_type} · ${tx.amount} · ${tx.timestamp}`)
    .join("\n") || "Sin transacciones";

  detailEl.innerHTML = `
    <h3>${customer.name}</h3>
    <p class="muted">${customer.customer_id} · ${customer.age} años · score ${customer.credit_score}</p>
    <div class="metrics">
      <div class="metric"><p class="muted">Ingreso</p><strong>${customer.income}</strong></div>
      <div class="metric"><p class="muted">Default</p><strong>${customer.default_risk}</strong></div>
      <div class="metric"><p class="muted">Churn</p><strong>${customer.churn_risk}</strong></div>
    </div>
    <div class="card"><p class="muted">Productos</p><p>${products}</p></div>
    <div class="card"><p class="muted">Life events</p><p>${events}</p></div>
    <div class="card"><p class="muted">Transacciones recientes</p><pre>${txs}</pre></div>
  `;
  insightBtn.hidden = false;
}

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  listEl.textContent = "Buscando...";
  renderList(await fetchCustomers(searchInput.value.trim()));
});

insightBtn.addEventListener("click", async () => {
  if (!selectedId) return;
  insightEl.textContent = "Generando insight...";
  const response = await fetch(`${API}/api/customers/${selectedId}/insight`, { method: "POST" });
  const payload = await response.json();
  insightEl.textContent = payload.insight || payload.detail || "Sin insight";
});

fetchCustomers()
  .then(renderList)
  .catch((error) => {
    listEl.textContent = error.message;
  });
