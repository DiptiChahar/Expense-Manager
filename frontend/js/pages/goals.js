import { api, describeApiError, postJson } from "../core/api.js";
import { renderChart, commonChartOptions } from "../core/charts.js";
import { escapeHtml, formatMoney, textOrNull } from "../core/format.js";
import { initLayout } from "../core/layout.js";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const state = {
  goals: []
};

async function loadData() {
  const goals = await api.goals();
  state.goals = Array.isArray(goals) ? goals : [];
}

function renderGoalSummary() {
  const summary = document.getElementById("goalSummary");
  const primary = state.goals[0];

  if (!primary) {
    summary.innerHTML = "<p>No goals added yet.</p>";
    return;
  }

  const target = Number(primary.target_amount || 0);
  const achieved = Number(primary.achieved_amount || 0);
  const progress = target ? Math.min(100, (achieved / target) * 100) : 0;

  summary.innerHTML = `
    <div class="goal-main">
      <div>
        <p class="goal-label">Target Achieved</p>
        <strong>${formatMoney(achieved)}</strong>
        <p class="goal-sub">This month target ${formatMoney(target)}</p>
        <p class="goal-sub">Target vs Achievement</p>
      </div>
      <div class="goal-meter" style="--progress:${(progress * 3.6).toFixed(0)}deg">
        <span>${progress.toFixed(0)}%</span>
      </div>
    </div>
    <button class="goal-adjust" type="button">Adjust Goal ✎</button>
  `;
}

function renderGoalCards() {
  const cards = document.getElementById("goalCards");

  cards.innerHTML = state.goals
    .slice(0, 6)
    .map((goal) => {
      return `
      <article class="goal-card">
        <div>
          <h4>${escapeHtml(goal.category || goal.name)}</h4>
          <p>${formatMoney(goal.target_amount)}</p>
        </div>
        <button class="goal-adjust" type="button">Adjust</button>
      </article>
      `;
    })
    .join("");
}

function renderGoalChart() {
  const points = state.goals.slice(0, 8);
  const labels = points.length ? points.map((goal) => goal.name || goal.category || "Goal") : ["No data"];
  const values = points.length ? points.map((goal) => Number(goal.achieved_amount || 0)) : [0];

  renderChart("goalChart", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Achieved",
          data: values,
          borderColor: "#20a79e",
          backgroundColor: "rgba(32,167,158,0.14)",
          fill: true,
          pointRadius: 0,
          tension: 0.4
        }
      ]
    },
    options: commonChartOptions("line")
  });
}

function bindForm() {
  const form = document.getElementById("goalForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);

    const payload = {
      name: textOrNull(data.get("name")),
      category: textOrNull(data.get("category")),
      target_amount: Number(data.get("target_amount")),
      achieved_amount: Number(data.get("achieved_amount")),
      due_date: data.get("due_date"),
      status: "active"
    };

    try {
      const created = await postJson("/goals", payload);

      state.goals.unshift(created);
      renderGoalSummary();
      renderGoalCards();
      renderGoalChart();

      form.reset();
      document.getElementById("goalModal")?.classList.add("hidden");
      setDefaultDateInputs();
    } catch (error) {
      window.alert(describeApiError(error, "save goal"));
    }
  });
}

async function initPage() {
  try {
    await initLayout("goals");
    initModal("openGoalModal", "goalModal");
    bindModalClose();
    setDefaultDateInputs();

    await loadData();
    renderGoalSummary();
    renderGoalCards();
    renderGoalChart();
    bindForm();
  } catch (error) {
    document.getElementById("goalSummary").innerHTML = "<p>Unable to load goals. Check backend connection.</p>";
    document.getElementById("goalCards").innerHTML = "";
    window.alert(describeApiError(error, "load goals"));
  }
}

initPage();
