import { api, describeApiError, postJson } from "../core/api.js";
import { escapeHtml, formatEntryDate, formatMoney, humanStatus, monthYear, normalizeStatus, parseDateValue, textOrNull } from "../core/format.js";
import { initLayout } from "../core/layout.js";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const state = {
  transactions: []
};

async function loadData() {
  const tx = await api.transactions();
  state.transactions = Array.isArray(tx) ? tx : [];
}

function renderTransactions(query = "") {
  const body = document.getElementById("transactionsTableBody");
  const q = query.trim().toLowerCase();

  const rows = state.transactions
    .slice()
    .sort((a, b) => {
      const aTime = parseDateValue(a.entry_date)?.getTime() ?? 0;
      const bTime = parseDateValue(b.entry_date)?.getTime() ?? 0;
      return bTime - aTime;
    })
    .filter((item) => {
      if (!q) return true;
      return [item.description, item.category, item.merchant, item.source]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    })
    .map((item, index) => {
      const isIncome = item.type === "income";
      const detail = item.description || item.category || "Transaction";
      const side = item.merchant || item.source || "-";
      const report = monthYear(item.entry_date).replace(" ", "_");
      const checked = index < 2 || normalizeStatus(item.status) === "submitted" ? "✓" : "";

      return `
      <tr>
        <td>
          <div class="tx-detail">
            <span class="tx-check">${checked}</span>
            <span class="tx-dot ${isIncome ? "income" : "expense"}">${isIncome ? "↗" : "↘"}</span>
            <div>
              <small>${escapeHtml(formatEntryDate(item.entry_date || ""))}</small>
              <div>${escapeHtml(detail)}</div>
            </div>
          </div>
        </td>
        <td>${escapeHtml(side)}</td>
        <td>${isIncome ? "+" : "-"}${formatMoney(item.amount)}</td>
        <td>${escapeHtml(report)}</td>
        <td><span class="status-pill ${normalizeStatus(item.status)}">${humanStatus(item.status)}</span></td>
      </tr>
      `;
    });

  body.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="5">No transactions found.</td></tr>`;
}

function bindSearch() {
  const search = document.getElementById("globalSearch");
  if (!search) return;
  search.addEventListener("input", () => renderTransactions(search.value));
}

function bindForm() {
  const form = document.getElementById("transactionForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const type = data.get("type");
    const party = textOrNull(data.get("merchant_or_source"));

    const payload = {
      type,
      amount: Number(data.get("amount")),
      category: textOrNull(data.get("category")),
      merchant: type === "expense" ? party : null,
      source: type === "income" ? party : null,
      description: textOrNull(data.get("description")),
      entry_date: data.get("entry_date"),
      payment_method: textOrNull(data.get("payment_method")),
      status: "not_submitted"
    };

    try {
      const created = await postJson("/transactions", payload);

      state.transactions.unshift(created);
      renderTransactions(document.getElementById("globalSearch")?.value || "");

      form.reset();
      document.getElementById("transactionModal")?.classList.add("hidden");
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
    setDefaultDateInputs();

    await loadData();
    renderTransactions();
    bindSearch();
    bindForm();
  } catch (error) {
    document.getElementById("transactionsTableBody").innerHTML = `<tr><td colspan="5">Unable to load transactions. Check backend connection.</td></tr>`;
    window.alert(describeApiError(error, "load transactions"));
  }
}

initPage();
