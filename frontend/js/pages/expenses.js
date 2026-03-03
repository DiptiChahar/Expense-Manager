import { api, describeApiError } from "../core/api.js";
import { renderChart, commonChartOptions } from "../core/charts.js";
import { escapeHtml, formatMoney } from "../core/format.js";
import { initLayout } from "../core/layout.js";

const state = {
  expenses: [],
  monthlyComparison: { labels: [], thisPeriod: [], lastPeriod: [] },
  expenseBreakdown: []
};

async function loadData() {
  const [expenses, monthlyComparison, expenseBreakdown] = await Promise.all([
    api.expenses(),
    api.monthlyComparison(),
    api.expensesBreakdown()
  ]);

  state.expenses = Array.isArray(expenses) ? expenses : [];
  state.monthlyComparison = monthlyComparison;
  state.expenseBreakdown = Array.isArray(expenseBreakdown) ? expenseBreakdown : [];
}

function expenseIconForCategory(category) {
  const c = String(category || "").toLowerCase();
  if (c.includes("housing") || c.includes("rent")) return "⌂";
  if (c.includes("food")) return "⌶";
  if (c.includes("transport")) return "✈";
  if (c.includes("entertain")) return "◉";
  if (c.includes("shop")) return "▢";
  if (c.includes("other")) return "◫";
  return "•";
}

function expenseDetailsForCategory(category) {
  return state.expenses
    .filter((item) => String(item.category || "").toLowerCase() === String(category || "").toLowerCase())
    .slice(0, 2)
    .map((item) => ({
      description: item.description || item.merchant || item.category,
      amount: Number(item.amount || 0),
      entry_date: item.entry_date
    }));
}

function renderMonthlyComparison() {
  renderChart("expensesComparisonChart", {
    type: "bar",
    data: {
      labels: state.monthlyComparison.labels || [],
      datasets: [
        {
          label: "This Year",
          data: state.monthlyComparison.thisPeriod || [],
          backgroundColor: "#22a79e",
          borderRadius: 8,
          barThickness: 12
        },
        {
          label: "Last Year",
          data: state.monthlyComparison.lastPeriod || [],
          backgroundColor: "#d0d5df",
          borderRadius: 8,
          barThickness: 12
        }
      ]
    },
    options: commonChartOptions("bar")
  });
}

function renderBreakdown() {
  const holder = document.getElementById("expenseBreakdown");

  holder.innerHTML = state.expenseBreakdown
    .slice(0, 6)
    .map((item) => {
      const change = Number(item.change_percent || 0);
      const trendCls = change >= 0 ? "up" : "down";
      const arrow = change >= 0 ? "↑" : "↓";
      const details = expenseDetailsForCategory(item.category);

      const detailRows = details
        .map((line) => {
          return `
          <div class="expense-line">
            <div>
              <strong>${escapeHtml(line.description)}</strong><br />
              <small>${escapeHtml(line.entry_date || "")}</small>
            </div>
            <div>${formatMoney(line.amount)}</div>
          </div>
          `;
        })
        .join("");

      return `
      <article class="expense-card">
        <div class="expense-card-head">
          <div class="expense-info">
            <span class="expense-icon">${escapeHtml(expenseIconForCategory(item.category))}</span>
            <div>
              <h4>${escapeHtml(item.category)}</h4>
              <div class="expense-total">${formatMoney(item.total)}</div>
            </div>
          </div>
          <div class="expense-trend ${trendCls}">${Math.abs(change).toFixed(0)}% ${arrow}</div>
        </div>
        <div class="expense-lines">
          ${detailRows || "<small>No transaction lines</small>"}
        </div>
      </article>
      `;
    })
    .join("");
}

async function initPage() {
  try {
    await initLayout("expenses");
    await loadData();
    renderMonthlyComparison();
    renderBreakdown();
  } catch (error) {
    document.getElementById("expenseBreakdown").innerHTML = "<p>Unable to load expenses data. Check backend connection.</p>";
    window.alert(describeApiError(error, "load expenses"));
  }
}

initPage();
