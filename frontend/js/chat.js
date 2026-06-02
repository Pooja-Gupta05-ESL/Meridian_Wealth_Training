const form = document.getElementById("chat-form");
const chatLog = document.getElementById("chat-log");
const clientNameEl = document.getElementById("client-name");
const messageEl = document.getElementById("message");
const sendBtn = document.getElementById("send-btn");
const statusLabel = document.getElementById("api-status-label");
const statusDot = document.getElementById("api-status-dot");
const agentNameEl = document.getElementById("agent-name");
const agentVersionEl = document.getElementById("agent-version");
const toolsEl = document.getElementById("agent-tools");

// Improved scroll function with smooth scrolling
function scrollToBottom() {
  requestAnimationFrame(() => {
    if (chatLog) {
      chatLog.scrollTop = chatLog.scrollHeight;
    }
  });
}

function addMessage(kind, text) {
  const block = document.createElement("div");
  block.className = `msg ${kind}`;
  
  const content = document.createElement("div");
  content.className = "msg-content";
  content.textContent = text;
  
  block.appendChild(content);
  chatLog.appendChild(block);
  
  // Use setTimeout to ensure DOM is updated before scrolling
  setTimeout(() => scrollToBottom(), 0);
  return block;
}

function addLoadingMessage() {
  const block = document.createElement("div");
  block.className = "msg agent";
  
  const content = document.createElement("div");
  content.className = "msg-content";
  content.innerHTML = `
    <div class="loading">
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
    </div>
    <div style="margin-top: 6px;">Processing your request...</div>
  `;
  
  block.appendChild(content);
  block.id = "loading-msg";
  chatLog.appendChild(block);
  
  // Use setTimeout to ensure DOM is updated before scrolling
  setTimeout(() => scrollToBottom(), 0);
  return block;
}

function removeLoadingMessage() {
  const loading = document.getElementById("loading-msg");
  if (loading) loading.remove();
}

function setSendingState(isSending) {
  sendBtn.disabled = isSending;
  if (isSending) {
    sendBtn.innerHTML = '<span class="loading"><span class="loading-dot"></span><span class="loading-dot"></span><span class="loading-dot"></span></span>';
  } else {
    sendBtn.innerHTML = '<span>Send Message</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
  }
  messageEl.disabled = isSending;
}

function setApiStatus(isHealthy) {
  if (isHealthy) {
    statusLabel.textContent = "API healthy";
    statusDot.classList.add("up");
    statusDot.classList.remove("down");
  } else {
    statusLabel.textContent = "API unavailable";
    statusDot.classList.add("down");
    statusDot.classList.remove("up");
  }
}

function renderTools(items) {
  toolsEl.innerHTML = "";
  (items || []).forEach((tool) => {
    const li = document.createElement("li");
    li.textContent = tool;
    toolsEl.appendChild(li);
  });
}

async function getHealth() {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return response.json();
}

async function getAgentInfo() {
  const response = await fetch("/agentinfo");
  if (!response.ok) {
    throw new Error("Agent info endpoint failed");
  }
  return response.json();
}

async function sendChat(message, clientName) {
  const response = await fetch("/main/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, client_name: clientName || null }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Request failed");
  }

  return response.json();
}

async function boot() {
  addMessage(
    "agent",
    "Welcome to Meridian Wealth AI Advisor 👋\n\nI'm your intelligent financial assistant. I can help you with:\n\n• Portfolio analysis and performance\n• Risk assessment and rebalancing\n• Policy compliance checks\n• Market trends and sector analysis\n• Client suitability analysis\n\nJust describe what you'd like to explore!"
  );

  try {
    await getHealth();
    setApiStatus(true);
  } catch {
    setApiStatus(false);
  }

  try {
    const info = await getAgentInfo();
    agentNameEl.textContent = info.name || "Financial Analyst Agent";
    agentVersionEl.textContent = info.version || "unknown";
    renderTools(info.tools || []);
  } catch {
    agentNameEl.textContent = "Financial Analyst Agent";
    agentVersionEl.textContent = "unavailable";
    renderTools([]);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageEl.value.trim();
  const clientName = clientNameEl.value.trim();

  if (!message) {
    return;
  }

  addMessage("user", message);
  messageEl.value = "";
  setSendingState(true);
  addLoadingMessage();

  try {
    const result = await sendChat(message, clientName);
    removeLoadingMessage();
    
    // Check if response is scaffold or startup error (agent not initialized)
    if (
      result.answer &&
      (
        result.answer.includes("Agent not initialized") ||
        result.answer.includes("Falling back to scaffold response") ||
        result.answer.includes("Agent startup error")
      )
    ) {
      const dbMatch = result.answer.match(/clients=(\d+), holdings=(\d+)/);
      const clientCount = dbMatch ? dbMatch[1] : "0";
      const holdingCount = dbMatch ? dbMatch[2] : "0";
      
      addMessage("error", 
        "⚠️ Agent not initialized.\n\n" +
        "To enable live agent responses:\n\n" +
        "1. Set API Keys in .env:\n" +
        "   OPENAI_API_KEY=sk-...\n" +
        "   TAVILY_API_KEY=tvly-...\n\n" +
        "2. Add Policy PDFs:\n" +
        "   Extract policy_documents.zip from Lab_6.4\n" +
        "   Place in: data/policy_document/\n\n" +
        "3. Seed Database:\n" +
        "   Current state: " + clientCount + " clients, " + holdingCount + " holdings\n" +
        "   Run Lab_4.1 to populate data/meridian_wealth.db\n\n" +
        "4. Install LangChain:\n" +
        "   pip install langchain langchain-openai langchain-community langchain-tavily\n\n" +
        "5. Restart server"
      );
    } else {
      addMessage("agent", result.answer || "No response received.");
    }

    if (Array.isArray(result.tools_used) && result.tools_used.length > 0) {
      renderTools(result.tools_used);
    }
  } catch (error) {
    removeLoadingMessage();
    addMessage("error", `❌ Error: ${error.message}`);
  } finally {
    setSendingState(false);
    messageEl.focus();
  }
});

boot();
