const form = document.getElementById("ask-form");
const resultCard = document.getElementById("result-card");
const answerEl = document.getElementById("answer");
const toolsEl = document.getElementById("tools");
const sourcesEl = document.getElementById("sources");

function renderList(target, items) {
  target.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    target.appendChild(li);
  });
}

async function askAgent(question, clientName) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, client_name: clientName || null }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Request failed");
  }

  return response.json();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const question = String(formData.get("question") || "").trim();
  const clientName = String(formData.get("clientName") || "").trim();

  if (!question) {
    return;
  }

  try {
    const data = await askAgent(question, clientName);
    answerEl.textContent = data.answer;
    renderList(toolsEl, data.tools_used || []);
    renderList(sourcesEl, data.sources || []);
    resultCard.hidden = false;
  } catch (error) {
    answerEl.textContent = `Error: ${error.message}`;
    toolsEl.innerHTML = "";
    sourcesEl.innerHTML = "";
    resultCard.hidden = false;
  }
});
