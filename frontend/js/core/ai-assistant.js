import { api, deleteJson, describeApiError, postJson, putJson } from "./api.js";
import { escapeHtml, formatMoney } from "./format.js?v=money-v4";

const STARTERS = [
  "Where am I overspending?",
  "How can I save more?",
  "Am I meeting my goals?"
];

let isMounted = false;
let messages = [];
let isBusy = false;
let nextActionId = 1;

function ensureAssistantStyles() {
  if (document.querySelector("link[data-ai-assistant-style]")) return;

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = "/css/components/ai-assistant.css?v=actions-v1";
  link.dataset.aiAssistantStyle = "true";
  document.head.appendChild(link);
}

function assistantMarkup() {
  return `
    <button id="aiAssistantButton" class="ai-assistant-button" type="button" aria-label="Open AI assistant">
      <span class="ai-assistant-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" focusable="false">
          <path d="M5.75 16.5c-1.24 0-2.25-1-2.25-2.24V7.75c0-1.24 1-2.25 2.25-2.25h8.5c1.24 0 2.25 1 2.25 2.25v6.5c0 1.24-1 2.25-2.25 2.25h-3.92l-3.45 2.35c-.5.35-1.18-.02-1.18-.63V16.5Z" />
          <path d="M17.7 4.15 18.45 2l.75 2.15 2.15.75-2.15.75-.75 2.15-.75-2.15-2.15-.75 2.15-.75Z" />
          <path d="m13.25 10 1.15-2.9 1.15 2.9 2.9 1.15-2.9 1.15-1.15 2.9-1.15-2.9-2.9-1.15L13.25 10Z" />
        </svg>
      </span>
    </button>

    <aside id="aiAssistantPanel" class="ai-assistant-panel" aria-label="AI financial assistant" aria-hidden="true">
      <div class="ai-panel-head">
        <div>
          <p>SpendSmart AI</p>
          <h2>Financial Assistant</h2>
        </div>
        <button id="aiAssistantClose" class="ai-panel-close" type="button" aria-label="Close AI assistant">&times;</button>
      </div>

      <div id="aiAssistantMessages" class="ai-messages" aria-live="polite"></div>

      <div class="ai-starters" id="aiAssistantStarters">
        ${STARTERS.map((starter) => `<button type="button" data-starter="${escapeHtml(starter)}">${escapeHtml(starter)}</button>`).join("")}
      </div>

      <form id="aiAssistantForm" class="ai-form">
        <textarea id="aiAssistantInput" rows="2" maxlength="1000" placeholder="Ask about spending, saving, or goals"></textarea>
        <button id="aiAssistantSend" type="submit">Send</button>
      </form>
    </aside>
  `;
}

function messagesNode() {
  return document.getElementById("aiAssistantMessages");
}

function scrollMessages() {
  const node = messagesNode();
  if (node) node.scrollTop = node.scrollHeight;
}

function renderMessages({ isLoading = false } = {}) {
  const node = messagesNode();
  if (!node) return;

  const renderedMessages = messages.map((message) => {
    const roleClass = message.role === "user" ? "user" : "assistant";
    const actionMarkup = message.action && message.action.status === "pending"
      ? `
        <div class="ai-action-card">
          <div class="ai-action-meta">
            <span>${escapeHtml(actionLabel(message.action))}</span>
            <strong>${escapeHtml(actionSummary(message.action))}</strong>
          </div>
          <div class="ai-action-buttons">
            <button type="button" data-ai-action="confirm" data-action-id="${escapeHtml(message.action.id)}">Confirm</button>
            <button type="button" data-ai-action="cancel" data-action-id="${escapeHtml(message.action.id)}">Cancel</button>
          </div>
        </div>
      `
      : "";
    return `
      <article class="ai-message ${roleClass}">
        <p>${escapeHtml(message.content)}</p>
        ${actionMarkup}
      </article>
    `;
  });

  if (isLoading) {
    renderedMessages.push(`
      <article class="ai-message assistant loading">
        <p>Analyzing your finances...</p>
      </article>
    `);
  }

  node.innerHTML = renderedMessages.join("");
  scrollMessages();
}

function setPanelOpen(isOpen) {
  const panel = document.getElementById("aiAssistantPanel");
  const button = document.getElementById("aiAssistantButton");
  if (!panel || !button) return;

  panel.classList.toggle("open", isOpen);
  panel.setAttribute("aria-hidden", isOpen ? "false" : "true");
  button.classList.toggle("hidden", isOpen);

  if (isOpen) {
    window.setTimeout(() => document.getElementById("aiAssistantInput")?.focus(), 180);
  }
}

function actionLabel(action) {
  const labels = {
    add_expense: "Add expense",
    add_income: "Add income",
    update: "Update transaction",
    delete: "Delete transaction"
  };
  return labels[action.intent] || "Transaction action";
}

function actionSummary(action) {
  const amount = action.amount !== null && action.amount !== undefined ? formatMoney(action.amount) : "";
  const category = action.category || "transaction";
  const date = action.date ? ` • ${action.date}` : "";
  return `${amount} ${category}${date}`.trim();
}

function addMessage(role, content, options = {}) {
  messages.push({ role, content, ...options });
  if (messages.length > 12) {
    messages = messages.slice(-12);
  }
  renderMessages();
}

function setFormDisabled(isDisabled) {
  const input = document.getElementById("aiAssistantInput");
  const send = document.getElementById("aiAssistantSend");
  if (input instanceof HTMLTextAreaElement) input.disabled = isDisabled;
  if (send instanceof HTMLButtonElement) send.disabled = isDisabled;
}

async function submitMessage(rawMessage) {
  const message = rawMessage.trim();
  if (!message || isBusy) return;

  const input = document.getElementById("aiAssistantInput");
  if (input instanceof HTMLTextAreaElement) input.value = "";

  addMessage("user", message);
  isBusy = true;
  setFormDisabled(true);
  renderMessages({ isLoading: true });

  try {
    const result = await api.aiChat(message);
    const pendingAction = result?.pending_action
      ? { ...result.pending_action, id: String(nextActionId++), status: "pending" }
      : null;
    addMessage("assistant", result?.response || "I could not generate an answer from your data yet.", {
      action: pendingAction
    });
  } catch (error) {
    if (error?.status === 401) {
      addMessage("assistant", "Please sign in first so I can analyze your own transactions, goals, and spending trends.");
    } else {
      addMessage("assistant", describeApiError(error, "ask the AI assistant"));
    }
  } finally {
    isBusy = false;
    setFormDisabled(false);
    document.getElementById("aiAssistantInput")?.focus();
  }
}

function findAction(actionId) {
  return messages.find((message) => message.action?.id === actionId)?.action || null;
}

function updateActionStatus(actionId, status) {
  messages = messages.map((message) => {
    if (message.action?.id !== actionId) return message;
    return {
      ...message,
      action: {
        ...message.action,
        status
      }
    };
  });
  renderMessages();
}

async function executePendingAction(action) {
  if (action.method === "POST") {
    return await postJson(action.endpoint, action.payload);
  }
  if (action.method === "PUT") {
    return await putJson(action.endpoint, action.payload);
  }
  if (action.method === "DELETE") {
    return await deleteJson(action.endpoint);
  }
  throw new Error("Unsupported assistant action.");
}

function successMessageForAction(action) {
  const amount = action.amount !== null && action.amount !== undefined ? formatMoney(action.amount) : "";
  if (action.intent === "delete") {
    return `Deleted ${action.category || "transaction"} ${amount}`.trim();
  }
  if (action.intent === "update") {
    return `Updated ${action.category || "transaction"} to ${amount}`.trim();
  }
  return `Added ${amount} to ${action.category || "transaction"}`.trim();
}

async function confirmPendingAction(actionId) {
  const action = findAction(actionId);
  if (!action || action.status !== "pending" || isBusy) return;

  isBusy = true;
  setFormDisabled(true);
  updateActionStatus(actionId, "working");
  renderMessages({ isLoading: true });

  try {
    await executePendingAction(action);
    updateActionStatus(actionId, "done");
    addMessage("assistant", successMessageForAction(action));
    window.dispatchEvent(new CustomEvent("spendsmart:transactions-changed", { detail: { action } }));
  } catch (error) {
    updateActionStatus(actionId, "pending");
    addMessage("assistant", describeApiError(error, "update transaction from assistant"));
  } finally {
    isBusy = false;
    setFormDisabled(false);
    document.getElementById("aiAssistantInput")?.focus();
  }
}

function cancelPendingAction(actionId) {
  const action = findAction(actionId);
  if (!action || action.status !== "pending") return;
  updateActionStatus(actionId, "cancelled");
  addMessage("assistant", "Cancelled. I did not change any transaction.");
}

function bindAssistantEvents() {
  document.getElementById("aiAssistantButton")?.addEventListener("click", () => {
    setPanelOpen(true);
  });

  document.getElementById("aiAssistantClose")?.addEventListener("click", () => {
    setPanelOpen(false);
  });

  document.getElementById("aiAssistantStarters")?.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const starter = target.dataset.starter;
    if (starter) submitMessage(starter);
  });

  document.getElementById("aiAssistantMessages")?.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const actionType = target.dataset.aiAction;
    const actionId = target.dataset.actionId;
    if (!actionType || !actionId) return;
    if (actionType === "confirm") {
      confirmPendingAction(actionId);
      return;
    }
    if (actionType === "cancel") {
      cancelPendingAction(actionId);
    }
  });

  const form = document.getElementById("aiAssistantForm");
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = document.getElementById("aiAssistantInput");
    if (input instanceof HTMLTextAreaElement) submitMessage(input.value);
  });

  document.getElementById("aiAssistantInput")?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    const input = event.target;
    if (input instanceof HTMLTextAreaElement) submitMessage(input.value);
  });
}

export function initAIAssistant() {
  if (isMounted) return;

  ensureAssistantStyles();
  document.body.insertAdjacentHTML("beforeend", assistantMarkup());
  messages = [
    {
      role: "assistant",
      content: "Ask me about overspending, saving opportunities, or goal progress. I will use your SpendSmart data."
    }
  ];
  renderMessages();
  bindAssistantEvents();
  isMounted = true;
}
