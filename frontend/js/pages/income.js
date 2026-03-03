import { api, describeApiError, postJson } from "../core/api.js";
import { escapeHtml, formatMoney, parseDateValue, textOrNull } from "../core/format.js";
import { initLayout } from "../core/layout.js";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const state = {
  income: []
};

async function loadData() {
  const income = await api.income();
  state.income = Array.isArray(income) ? income : [];
}

function renderIncome(query = "") {
  const body = document.getElementById("incomeTableBody");
  const q = query.trim().toLowerCase();

  const rows = state.income
    .slice()
    .sort((a, b) => {
      const aTime = parseDateValue(a.entry_date)?.getTime() ?? 0;
      const bTime = parseDateValue(b.entry_date)?.getTime() ?? 0;
      return bTime - aTime;
    })
    .filter((item) => {
      if (!q) return true;
      return [item.source, item.description, item.category].filter(Boolean).join(" ").toLowerCase().includes(q);
    })
    .map((item) => {
      return `
      <tr>
        <td>${escapeHtml(item.entry_date || "")}</td>
        <td>${escapeHtml(item.source || item.category || "Income")}</td>
        <td>${escapeHtml(item.description || "-")}</td>
        <td class="amount-plus">${formatMoney(item.amount)}</td>
      </tr>
      `;
    });

  body.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="4">No income records yet.</td></tr>`;

  const total = state.income.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  document.getElementById("incomeTotalPage").textContent = formatMoney(total);
}

function bindSearch() {
  const search = document.getElementById("globalSearch");
  if (!search) return;
  search.addEventListener("input", () => renderIncome(search.value));
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
      renderIncome(document.getElementById("globalSearch")?.value || "");

      form.reset();
      document.getElementById("incomeModal")?.classList.add("hidden");
      setDefaultDateInputs();
    } catch (error) {
      window.alert(describeApiError(error, "save income"));
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
    bindSearch();
    bindForm();
  } catch (error) {
    document.getElementById("incomeTableBody").innerHTML = `<tr><td colspan="4">Unable to load income records. Check backend connection.</td></tr>`;
    window.alert(describeApiError(error, "load income"));
  }
}

initPage();
