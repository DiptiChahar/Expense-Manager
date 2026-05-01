import { api, describeApiError, postJson } from "../core/api.js";
import { capitalize, dayOfMonth, escapeHtml, formatDueDate, formatMoneyHtml, parseDateValue, shortMonth, textOrNull } from "../core/format.js?v=money-v4";
import { initLayout } from "../core/layout.js?v=layout-v2";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const state = {
  bills: []
};

async function loadData() {
  const bills = await api.bills();
  state.bills = Array.isArray(bills) ? bills : [];
}

function renderBills() {
  const body = document.getElementById("billsTableBody");

  const rows = state.bills
    .slice()
    .sort((a, b) => {
      const aTime = parseDateValue(a.due_date)?.getTime() ?? 0;
      const bTime = parseDateValue(b.due_date)?.getTime() ?? 0;
      return aTime - bTime;
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
        <td><span class="bill-amount">${formatMoneyHtml(bill.amount)}</span></td>
      </tr>
      `;
    });

  body.innerHTML = rows.length ? rows.join("") : `<tr><td colspan="5">No bills yet.</td></tr>`;
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
      renderBills();

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
    bindForm();
  } catch (error) {
    document.getElementById("billsTableBody").innerHTML = `<tr><td colspan="5">Unable to load bills. Check backend connection.</td></tr>`;
    window.alert(describeApiError(error, "load bills"));
  }
}

initPage();
