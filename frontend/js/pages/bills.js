import { api, describeApiError, postJson } from "../core/api.js";
import { capitalize, dayOfMonth, escapeHtml, formatDueDate, formatMoney, parseDateValue, shortMonth, textOrNull } from "../core/format.js";
import { initLayout } from "../core/layout.js";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const state = {
  bills: []
};

async function loadData() {
  const bills = await api.bills();
  state.bills = Array.isArray(bills) ? bills : [];
}

function renderBills(query = "") {
  const body = document.getElementById("billsTableBody");
  const q = query.trim().toLowerCase();

  const rows = state.bills
    .slice()
    .sort((a, b) => {
      const aTime = parseDateValue(a.due_date)?.getTime() ?? 0;
      const bTime = parseDateValue(b.due_date)?.getTime() ?? 0;
      return aTime - bTime;
    })
    .filter((bill) => {
      if (!q) return true;
      return [bill.vendor, bill.description, bill.frequency].filter(Boolean).join(" ").toLowerCase().includes(q);
    })
    .map((bill) => {
      const dueMonth = shortMonth(bill.due_date);
      const dueDay = dayOfMonth(bill.due_date);
      const vendorLetter = (bill.vendor || "?").trim().charAt(0).toUpperCase();

      return `
      <tr>
        <td>
          <div class="due-badge">
            <span>${escapeHtml(dueMonth)}</span>
            <strong>${escapeHtml(dueDay)}</strong>
          </div>
        </td>
        <td>
          <div class="vendor-wrap">
            <span class="vendor-logo">${escapeHtml(vendorLetter)}</span>
            <strong>${escapeHtml(bill.vendor || "-")}</strong>
          </div>
        </td>
        <td>
          <div class="bill-item-title">${escapeHtml(bill.description || bill.vendor || "-")}</div>
          <div class="bill-item-note">${escapeHtml(capitalize(bill.frequency || "monthly"))} billing cycle</div>
        </td>
        <td>${escapeHtml(formatDueDate(bill.last_charge_date))}</td>
        <td><span class="bill-amount">${formatMoney(bill.amount)}</span></td>
      </tr>
      `;
    });

  body.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="5">No bills yet.</td></tr>`;
}

function bindSearch() {
  const search = document.getElementById("globalSearch");
  if (!search) return;
  search.addEventListener("input", () => renderBills(search.value));
}

function bindForm() {
  const form = document.getElementById("billForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);

    const payload = {
      vendor: textOrNull(data.get("vendor")),
      amount: Number(data.get("amount")),
      due_date: data.get("due_date"),
      frequency: data.get("frequency"),
      description: textOrNull(data.get("description")),
      status: "pending"
    };

    try {
      const created = await postJson("/bills", payload);

      state.bills.unshift(created);
      renderBills(document.getElementById("globalSearch")?.value || "");

      form.reset();
      document.getElementById("billModal")?.classList.add("hidden");
      setDefaultDateInputs();
    } catch (error) {
      window.alert(describeApiError(error, "save bill"));
    }
  });
}

async function initPage() {
  try {
    await initLayout("bills");
    initModal("openBillModal", "billModal");
    bindModalClose();
    setDefaultDateInputs();

    await loadData();
    renderBills();
    bindSearch();
    bindForm();
  } catch (error) {
    document.getElementById("billsTableBody").innerHTML = `<tr><td colspan="5">Unable to load bills. Check backend connection.</td></tr>`;
    window.alert(describeApiError(error, "load bills"));
  }
}

initPage();
