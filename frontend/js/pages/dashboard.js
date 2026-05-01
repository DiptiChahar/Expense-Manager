import { api, describeApiError } from "../core/api.js";
import { renderChart, commonChartOptions } from "../core/charts.js";
import { escapeHtml, formatMoneyHtml, parseDateValue, setMoneyHtml } from "../core/format.js?v=money-v4";
import { initLayout } from "../core/layout.js?v=layout-v2";

const state = {
  summary: null,
  transactions: [],
  monthlyTrend: { labels: [], values: [] },
  categoryBreakdown: [],
  weeklyComparison: { labels: [], thisWeek: [], lastWeek: [] }
};

async function loadData() {
  const [summary, transactions, monthlyTrend, categoryBreakdown, weeklyComparison] = await Promise.all([
    api.summary(),
    api.transactions(),
    api.monthlyExpenseTrend(),
    api.categoryBreakdown(),
    api.weeklyComparison()
  ]);

  state.summary = summary;
  state.transactions = Array.isArray(transactions) ? transactions : [];
  state.monthlyTrend = monthlyTrend;
  state.categoryBreakdown = Array.isArray(categoryBreakdown) ? categoryBreakdown : [];
  state.weeklyComparison = weeklyComparison;
}

function renderMetrics() {
  setMoneyHtml(document.getElementById("metricIncome"), state.summary?.total_income);
  setMoneyHtml(document.getElementById("metricExpense"), state.summary?.total_expenses);
  setMoneyHtml(document.getElementById("metricBalance"), state.summary?.balance);
  document.getElementById("metricSavings").textContent = `${Number(state.summary?.savings_rate || 0).toFixed(1)}%`;
}

function renderRecentTransactions() {
  const holder = document.getElementById("recentTransactions");
  const recent = state.transactions
    .slice()
    .sort((a, b) => {
      const aTime = parseDateValue(a.entry_date)?.getTime() ?? 0;
      const bTime = parseDateValue(b.entry_date)?.getTime() ?? 0;
      return bTime - aTime;
    })
    .slice(0, 4);

  if (!recent.length) {
    holder.innerHTML = `<p class="empty-state">No transactions yet.</p>`;
    return;
  }

  holder.innerHTML = recent
    .map((item) => {
      const title = item.description || item.category || "Transaction";
      const subtitle = item.merchant || item.source || "Manual entry";
      const amountClass = item.type === "income" ? "amount-plus" : "amount-minus";
      const sign = item.type === "income" ? "+" : "-";
      return `
      <article class="recent-item">
        <div>
          <h4>${escapeHtml(title)}</h4>
          <p>${escapeHtml(subtitle)}</p>
        </div>
        <div class="${amountClass}">${formatMoneyHtml(item.amount, { sign })}</div>
      </article>
      `;
    })
    .join("");
}

function renderExpenseTrendChart() {
  renderChart("expenseTrendChart", {
    type: "line",
    data: {
      labels: state.monthlyTrend.labels || [],
      datasets: [
        {
          label: "Expenses",
          data: state.monthlyTrend.values || [],
          borderColor: "#5a5de5",
          backgroundColor: "rgba(90,93,229,0.12)",
          fill: true,
          tension: 0.32,
          pointRadius: 4
        }
      ]
    },
    options: commonChartOptions("line"),
    emptyMessage: "No expense trend data yet."
  });
}

function renderCategoryChart() {
  renderChart("categoryChart", {
    type: "doughnut",
    data: {
      labels: state.categoryBreakdown.map((item) => item.category),
      datasets: [
        {
          data: state.categoryBreakdown.map((item) => Number(item.total || 0)),
          backgroundColor: ["#5a5de5", "#1fb58f", "#f39c46", "#8b6ee9", "#ea6381", "#2f94dd"],
          borderWidth: 0
        }
      ]
    },
    options: {
      maintainAspectRatio: false,
      cutout: "52%",
      plugins: {
        legend: {
          position: "bottom"
        }
      }
    },
    emptyMessage: "No category spending yet."
  });
}

function renderStatisticsChart() {
  renderChart("statisticsChart", {
    type: "bar",
    data: {
      labels: state.weeklyComparison.labels || [],
      datasets: [
        {
          label: "This week",
          data: state.weeklyComparison.thisWeek || [],
          backgroundColor: "#22a79e",
          borderRadius: 8,
          barThickness: 13
        },
        {
          label: "Last week",
          data: state.weeklyComparison.lastWeek || [],
          backgroundColor: "#ccd1db",
          borderRadius: 8,
          barThickness: 13
        }
      ]
    },
    options: commonChartOptions("bar"),
    emptyMessage: "No weekly spending yet."
  });
}

function renderDashboard() {
  renderMetrics();
  renderRecentTransactions();
  renderExpenseTrendChart();
  renderCategoryChart();
  renderStatisticsChart();
}

function bindAssistantRefresh() {
  window.addEventListener("spendsmart:transactions-changed", async () => {
    try {
      await loadData();
      renderDashboard();
    } catch (error) {
      console.warn(describeApiError(error, "refresh dashboard"));
    }
  });
}

async function initPage() {
  try {
    await initLayout("dashboard");
    await loadData();
    renderDashboard();
    bindAssistantRefresh();
  } catch (error) {
    document.getElementById("recentTransactions").innerHTML = "<p>Unable to load dashboard data. Check backend connection.</p>";
    window.alert(describeApiError(error, "load dashboard"));
  }
}

initPage();
