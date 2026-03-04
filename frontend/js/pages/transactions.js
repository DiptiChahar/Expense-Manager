import { api, describeApiError, postJson, putJson } from "../core/api.js";
import { handleUnauthorized, getToken } from "../core/auth.js";
import { escapeHtml, formatEntryDate, formatMoney, parseDateValue, textOrNull } from "../core/format.js";
import { initLayout } from "../core/layout.js";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const API_BASE = window.SPENDSMART_API_BASE || "http://127.0.0.1:8000/api/v1";
const CREATE_MODAL_TITLE = "Add Transaction";
const CREATE_SUBMIT_LABEL = "Add Transaction";
const EDIT_MODAL_TITLE = "Edit Transaction";
const EDIT_SUBMIT_LABEL = "Save Changes";
const FILTER_LABELS = {
  all: "All",
  income: "Income",
  expense: "Expense",
  this_month: "This Month",
  last_month: "Last Month"
};

const state = {
  transactions: [],
  visibleTransactions: [],
  activeFilter: "all",
  renderMode: "filter",
  isFilterMenuOpen: false,
  isEditing: false,
  editingTransactionId: null
};

async function loadData() {
  const tx = await api.transactions();
  state.transactions = Array.isArray(tx) ? tx : [];
}

function sortedTransactions(items) {
  return items
    .slice()
    .sort((a, b) => {
      const aTime = parseDateValue(a.entry_date)?.getTime() ?? 0;
      const bTime = parseDateValue(b.entry_date)?.getTime() ?? 0;
      return bTime - aTime;
    });
}

function filterTransactions(items, filterKey = state.activeFilter) {
  const now = new Date();
  const lastMonthDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);

  return items.filter((item) => {
    const entryDate = parseDateValue(item.entry_date);
    if (filterKey === "income") return item.type === "income";
    if (filterKey === "expense") return item.type === "expense";

    if (filterKey === "this_month") {
      if (!entryDate) return false;
      return entryDate.getMonth() === now.getMonth() && entryDate.getFullYear() === now.getFullYear();
    }

    if (filterKey === "last_month") {
      if (!entryDate) return false;
      return (
        entryDate.getMonth() === lastMonthDate.getMonth() &&
        entryDate.getFullYear() === lastMonthDate.getFullYear()
      );
    }

    return true;
  });
}

function matchesSearch(item, queryLower) {
  if (!queryLower) return true;
  return [item.description, item.category, item.merchant, item.source]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()
    .includes(queryLower);
}

function renderRows(items) {
  const body = document.getElementById("transactionsTableBody");
  state.visibleTransactions = items;

  const rows = items.map((item) => {
      const isIncome = item.type === "income";
      const detail = item.description || item.category || "Transaction";
      const side = item.merchant || item.source || "-";
      const category = item.category || "-";
      const typeLabel = isIncome ? "Income" : "Expense";
      const typeIcon = isIncome ? "📈" : "📉";
      const amountPrefix = isIncome ? "+" : "-";

      return `
      <tr>
        <td>
          <div class="tx-detail">
            <div>
              <small>${escapeHtml(formatEntryDate(item.entry_date || ""))}</small>
              <div>${escapeHtml(detail)}</div>
            </div>
          </div>
        </td>
        <td>
          <span class="tx-type ${isIncome ? "income" : "expense"}">${typeIcon} ${typeLabel}</span>
        </td>
        <td>${escapeHtml(side)}</td>
        <td><span class="tx-category">🏷 ${escapeHtml(category)}</span></td>
        <td><span class="tx-amount ${isIncome ? "income" : "expense"}">${amountPrefix} ${formatMoney(item.amount)}</span></td>
        <td>
          <div class="tx-actions">
            <button type="button" class="tx-action-btn edit" data-action="edit" data-id="${escapeHtml(item.id)}" title="Edit">✏</button>
            <button type="button" class="tx-action-btn delete" data-action="delete" data-id="${escapeHtml(item.id)}" title="Delete">🗑</button>
          </div>
        </td>
      </tr>
      `;
    });

  body.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="6">No transactions found.</td></tr>`;
}

function renderTransactionsByActiveFilter() {
  state.renderMode = "filter";
  const rows = filterTransactions(sortedTransactions(state.transactions), state.activeFilter);
  renderRows(rows);
}

function renderTransactionsBySearch(query = "") {
  const queryLower = query.trim().toLowerCase();
  if (!queryLower) {
    renderTransactionsByActiveFilter();
    return;
  }
  state.renderMode = "search";
  const rows = sortedTransactions(state.transactions).filter((item) => matchesSearch(item, queryLower));
  renderRows(rows);
}

function rerenderCurrentView() {
  const query = activeSearchQuery().trim();
  if (state.renderMode === "search" && query) {
    renderTransactionsBySearch(query);
    return;
  }
  renderTransactionsByActiveFilter();
}

function getRowsForCurrentView() {
  const query = activeSearchQuery().trim().toLowerCase();
  if (state.renderMode === "search" && query) {
    return sortedTransactions(state.transactions).filter((item) => matchesSearch(item, query));
  }
  return filterTransactions(sortedTransactions(state.transactions), state.activeFilter);
}

function normalizeStatus(status) {
  return String(status || "").toLowerCase().includes("not") ? "not_submitted" : "submitted";
}

function formatDateInputValue(value) {
  const parsed = parseDateValue(value);
  if (!parsed) return "";
  const yyyy = parsed.getFullYear();
  const mm = String(parsed.getMonth() + 1).padStart(2, "0");
  const dd = String(parsed.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function activeSearchQuery() {
  return document.getElementById("globalSearch")?.value || "";
}

function setFilterMenuOpen(isOpen) {
  state.isFilterMenuOpen = Boolean(isOpen);
  const filterMenu = document.getElementById("transactionsFilterMenu");
  if (filterMenu) {
    filterMenu.classList.toggle("hidden", !state.isFilterMenuOpen);
  }

  const filterButton = document.getElementById("transactionsFilterButton");
  if (filterButton instanceof HTMLButtonElement) {
    filterButton.setAttribute("aria-expanded", state.isFilterMenuOpen ? "true" : "false");
  }
}

function closeFilterMenu() {
  setFilterMenuOpen(false);
}

function setFilterButtonCopy() {
  const label = FILTER_LABELS[state.activeFilter] || FILTER_LABELS.all;
  const button = document.getElementById("transactionsFilterButton");
  if (!(button instanceof HTMLButtonElement)) return;
  button.title = `Filter: ${label}`;
  button.setAttribute("aria-label", `Filter: ${label}`);
}

function syncActiveFilterMenu() {
  document.querySelectorAll("#transactionsFilterMenu .tx-filter-item").forEach((node) => {
    if (!(node instanceof HTMLButtonElement)) return;
    const isActive = node.dataset.filter === state.activeFilter;
    node.classList.toggle("active", isActive);
  });
}

function applyFilter(filterKey) {
  if (!Object.prototype.hasOwnProperty.call(FILTER_LABELS, filterKey)) return;
  state.activeFilter = filterKey;
  setFilterButtonCopy();
  syncActiveFilterMenu();

  const search = document.getElementById("globalSearch");
  if (search instanceof HTMLInputElement) {
    search.value = "";
  }
  renderTransactionsByActiveFilter();
}

function getEditingTransaction() {
  if (!state.editingTransactionId) return null;
  return state.transactions.find((item) => item.id === state.editingTransactionId) || null;
}

function setModalCopy() {
  const title = document.getElementById("transactionModalTitle");
  if (title) title.textContent = state.isEditing ? EDIT_MODAL_TITLE : CREATE_MODAL_TITLE;

  const submitButton = document.getElementById("transactionSubmitButton");
  if (submitButton) submitButton.textContent = state.isEditing ? EDIT_SUBMIT_LABEL : CREATE_SUBMIT_LABEL;
}

function resetEditState() {
  state.isEditing = false;
  state.editingTransactionId = null;
  setModalCopy();
}

function enterEditState(transactionId) {
  state.isEditing = true;
  state.editingTransactionId = transactionId;
  setModalCopy();
}

function closeTransactionModal() {
  document.getElementById("transactionModal")?.classList.add("hidden");
}

function openTransactionModal() {
  document.getElementById("transactionModal")?.classList.remove("hidden");
}

function fillFormForTransaction(transaction) {
  const form = document.getElementById("transactionForm");
  if (!(form instanceof HTMLFormElement)) return;

  const amountInput = form.elements.namedItem("amount");
  if (amountInput instanceof HTMLInputElement) {
    amountInput.value = String(Number(transaction.amount || 0));
  }

  const typeInput = form.elements.namedItem("type");
  if (typeInput instanceof HTMLSelectElement) {
    typeInput.value = transaction.type || "expense";
  }

  const categoryInput = form.elements.namedItem("category");
  if (categoryInput instanceof HTMLInputElement) {
    categoryInput.value = transaction.category || "";
  }

  const partyInput = form.elements.namedItem("merchant_or_source");
  if (partyInput instanceof HTMLInputElement) {
    partyInput.value = transaction.merchant || transaction.source || "";
  }

  const descriptionInput = form.elements.namedItem("description");
  if (descriptionInput instanceof HTMLInputElement) {
    descriptionInput.value = transaction.description || "";
  }

  const entryDateInput = form.elements.namedItem("entry_date");
  if (entryDateInput instanceof HTMLInputElement) {
    entryDateInput.value = formatDateInputValue(transaction.entry_date);
  }

  const paymentMethodInput = form.elements.namedItem("payment_method");
  if (paymentMethodInput instanceof HTMLSelectElement) {
    paymentMethodInput.value = transaction.payment_method || "Cash";
  }
}

function beginCreateFlow() {
  const form = document.getElementById("transactionForm");
  if (!(form instanceof HTMLFormElement)) return;
  form.reset();
  resetEditState();
  setDefaultDateInputs();
}

function beginEditFlow(transactionId) {
  const transaction = state.transactions.find((item) => item.id === transactionId);
  if (!transaction) {
    window.alert("Transaction not found.");
    return;
  }

  enterEditState(transactionId);
  fillFormForTransaction(transaction);
  openTransactionModal();
}

function buildPayload(formData) {
  const type = formData.get("type");
  const party = textOrNull(formData.get("merchant_or_source"));
  const editingTx = getEditingTransaction();

  return {
    type,
    amount: Number(formData.get("amount")),
    category: textOrNull(formData.get("category")),
    merchant: type === "expense" ? party : null,
    source: type === "income" ? party : null,
    description: textOrNull(formData.get("description")),
    entry_date: formData.get("entry_date"),
    payment_method: textOrNull(formData.get("payment_method")),
    status: state.isEditing ? normalizeStatus(editingTx?.status) : "not_submitted"
  };
}

function upsertTransaction(updatedTransaction) {
  state.transactions = state.transactions.map((item) =>
    item.id === updatedTransaction.id ? updatedTransaction : item
  );
}

function csvEscape(value) {
  return `"${String(value ?? "").replaceAll('"', "\"\"")}"`;
}

function buildTransactionsCsv(rows) {
  const header = ["Details", "Type", "Source", "Category", "Amount"];
  const lines = [header.map(csvEscape).join(",")];

  rows.forEach((item) => {
    const isIncome = item.type === "income";
    const detail = item.description || item.category || "Transaction";
    const detailsCell = `${formatEntryDate(item.entry_date || "")} | ${detail}`;
    const typeCell = isIncome ? "Income" : "Expense";
    const sourceCell = item.merchant || item.source || "-";
    const categoryCell = item.category || "-";
    const amountCell = `${isIncome ? "+" : "-"} ${formatMoney(item.amount)}`;
    lines.push([detailsCell, typeCell, sourceCell, categoryCell, amountCell].map(csvEscape).join(","));
  });

  return `${lines.join("\n")}\n`;
}

function todayStamp() {
  const now = new Date();
  const yyyy = String(now.getFullYear());
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function exportVisibleTransactions() {
  let rows = state.visibleTransactions;
  if (!rows.length && state.transactions.length) {
    rows = getRowsForCurrentView();
  }

  if (!rows.length) {
    window.alert("No transactions available to export.");
    return;
  }

  const csv = `\uFEFF${buildTransactionsCsv(rows)}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const activeView = state.renderMode === "search" ? "search" : state.activeFilter;
  const fileName = `transactions_${activeView}_${todayStamp()}.csv`;

  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function parseErrorMessage(body) {
  if (!body) return "";
  if (typeof body === "string") return body;
  if (body.error && typeof body.error.message === "string") return body.error.message;
  if (typeof body.message === "string") return body.message;
  if (typeof body.detail === "string") return body.detail;
  return "";
}

async function deleteTransaction(transactionId) {
  if (!transactionId) return;

  const shouldDelete = window.confirm("Are you sure you want to delete this transaction?");
  if (!shouldDelete) return;

  const token = getToken();
  if (!token) {
    handleUnauthorized();
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/transactions/${transactionId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (response.status === 401) {
      handleUnauthorized();
      return;
    }

    if (!response.ok) {
      let body = null;
      try {
        body = await response.json();
      } catch (_parseError) {
        body = null;
      }
      const message = parseErrorMessage(body);
      const error = new Error(
        message || `DELETE /transactions/${transactionId} failed (${response.status})`
      );
      error.uiMessage = message || "Unable to delete transaction.";
      throw error;
    }

    state.transactions = state.transactions.filter((item) => item.id !== transactionId);
    rerenderCurrentView();
  } catch (error) {
    window.alert(describeApiError(error, "delete transaction"));
  }
}

function bindTableActions() {
  const body = document.getElementById("transactionsTableBody");
  if (!body) return;

  body.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const actionButton = target.closest("[data-action][data-id]");
    if (!(actionButton instanceof HTMLButtonElement)) return;

    const action = actionButton.dataset.action;
    const transactionId = actionButton.dataset.id;
    if (!action || !transactionId) return;

    if (action === "edit") {
      beginEditFlow(transactionId);
      return;
    }

    if (action === "delete") {
      await deleteTransaction(transactionId);
    }
  });
}

function bindModalStateSync() {
  const modal = document.getElementById("transactionModal");
  if (!(modal instanceof HTMLElement)) return;

  document.getElementById("openTransactionModal")?.addEventListener("click", () => {
    beginCreateFlow();
  });

  modal.querySelectorAll("[data-close='transactionModal']").forEach((button) => {
    button.addEventListener("click", () => {
      resetEditState();
    });
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      resetEditState();
    }
  });
}

function bindFilterControls() {
  const filterWrap = document.querySelector(".tx-filter-wrap");
  const filterButton = document.getElementById("transactionsFilterButton");
  const filterMenu = document.getElementById("transactionsFilterMenu");
  if (!(filterWrap instanceof HTMLElement) || !(filterButton instanceof HTMLButtonElement) || !(filterMenu instanceof HTMLElement)) {
    return;
  }

  filterButton.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setFilterMenuOpen(!state.isFilterMenuOpen);
  });

  filterMenu.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const item = target.closest(".tx-filter-item");
    if (!(item instanceof HTMLButtonElement)) return;
    const selected = item.dataset.filter;
    if (!selected) return;
    applyFilter(selected);
    setFilterMenuOpen(false);
  });

  document.addEventListener("pointerdown", (event) => {
    if (!state.isFilterMenuOpen) return;
    const target = event.target;
    if (!(target instanceof Node)) return;
    if (!filterWrap.contains(target)) {
      setFilterMenuOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.isFilterMenuOpen) {
      setFilterMenuOpen(false);
    }
  });
}

function bindExportControl() {
  const exportButton = document.getElementById("transactionsExportButton");
  if (!(exportButton instanceof HTMLButtonElement)) return;
  exportButton.addEventListener("click", () => {
    exportVisibleTransactions();
  });
}

function bindSearch() {
  const search = document.getElementById("globalSearch");
  if (!search) return;
  search.addEventListener("input", () => renderTransactionsBySearch(search.value));
}

function bindForm() {
  const form = document.getElementById("transactionForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = buildPayload(new FormData(form));

    try {
      if (state.isEditing) {
        if (!state.editingTransactionId) {
          throw new Error("Missing transaction id for edit.");
        }

        const shouldSave = window.confirm("Are you sure you want to save these changes?");
        if (!shouldSave) return;

        const updated = await putJson(`/transactions/${state.editingTransactionId}`, payload);
        upsertTransaction(updated);
      } else {
        const created = await postJson("/transactions", payload);
        state.transactions.unshift(created);
      }

      rerenderCurrentView();
      form.reset();
      closeTransactionModal();
      resetEditState();
      setDefaultDateInputs();
    } catch (error) {
      window.alert(describeApiError(error, "save transaction"));
    }
  });
}

async function initPage() {
  try {
    await initLayout("transactions");
    initModal("openTransactionModal", "transactionModal");
    bindModalClose();
    bindModalStateSync();
    bindFilterControls();
    bindExportControl();
    setFilterMenuOpen(false);
    setFilterButtonCopy();
    syncActiveFilterMenu();
    resetEditState();
    setDefaultDateInputs();

    await loadData();
    renderTransactionsByActiveFilter();
    bindSearch();
    bindTableActions();
    bindForm();
  } catch (error) {
    document.getElementById("transactionsTableBody").innerHTML = `<tr><td colspan="6">Unable to load transactions. Check backend connection.</td></tr>`;
    window.alert(describeApiError(error, "load transactions"));
  }
}

initPage();
