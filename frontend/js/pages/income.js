import { api, describeApiError, postJson } from "../core/api.js";
import { escapeHtml, formatMoneyHtml, parseDateValue, setMoneyHtml, textOrNull } from "../core/format.js?v=money-v4";
import { initLayout } from "../core/layout.js?v=layout-v2";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const state = {
  income: []
};

async function loadData() {
  const income = await api.income();
  state.income = Array.isArray(income) ? income : [];
}

function renderIncome() {
  const body = document.getElementById("incomeTableBody");

  const rows = state.income
    .slice()
    .sort((a, b) => {
      const aTime = parseDateValue(a.entry_date)?.getTime() ?? 0;
      const bTime = parseDateValue(b.entry_date)?.getTime() ?? 0;
      return bTime - aTime;
    })
    .map((item) => {
      return `
      <tr>
        <td>${escapeHtml(item.entry_date || "")}</td>
        <td>${escapeHtml(item.source || item.category || "Income")}</td>
        <td>${escapeHtml(item.description || "-")}</td>
        <td class="amount-plus">${formatMoneyHtml(item.amount)}</td>
      </tr>
      `;
    });

  body.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="4">No income records yet.</td></tr>`;

  const total = state.income.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  setMoneyHtml(document.getElementById("incomeTotalPage"), total);
}

function bindForm() {
  const form = document.getElementById("incomeForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);

    const payload = {
      amount: Number(data.get("amount")),
      source: textOrNull(data.get("source")),
      description: textOrNull(data.get("description")),
      entry_date: data.get("entry_date")
    };

    try {
      const created = await postJson("/income", payload);

      state.income.unshift(created);
      renderIncome();

      form.reset();
      document.getElementById("incomeModal")?.classList.add("hidden");
      setDefaultDateInputs();
    } catch (error) {
      window.alert(describeApiError(error, "save income"));
    }
  });
}

function bindAssistantRefresh() {
  window.addEventListener("spendsmart:transactions-changed", async () => {
    try {
      await loadData();
      renderIncome();
    } catch (error) {
      console.warn(describeApiError(error, "refresh income"));
    }
  });
}

async function initPage() {
  try {
    await initLayout("income");
    initModal("openIncomeModal", "incomeModal");
    bindModalClose();
    setDefaultDateInputs();

    await loadData();
    renderIncome();
    bindAssistantRefresh();
    bindForm();
  } catch (error) {
    document.getElementById("incomeTableBody").innerHTML = `<tr><td colspan="4">Unable to load income records. Check backend connection.</td></tr>`;
    window.alert(describeApiError(error, "load income"));
  }
}

initPage();
