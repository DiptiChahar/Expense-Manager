import { api, deleteJson, describeApiError, postJson, putJson } from "../core/api.js";
import { renderChart, commonChartOptions } from "../core/charts.js";
import { escapeHtml, formatDueDate, formatMoney, parseDateValue, textOrNull } from "../core/format.js";
import { initLayout } from "../core/layout.js";
import { bindModalClose, initModal, setDefaultDateInputs } from "../core/modal.js";

const state = {
  goals: [],
  isEditing: false,
  editingGoalId: null
};

async function loadData() {
  const goals = await api.goals();
  state.goals = Array.isArray(goals) ? goals : [];
}

function goalTitle(goal) {
  return goal.name || goal.category || "Goal";
}

function goalProgress(goal) {
  const target = Number(goal.target_amount || 0);
  const achieved = Number(goal.achieved_amount || 0);
  return target ? Math.min(100, Math.max(0, (achieved / target) * 100)) : 0;
}

function goalStatus(targetAmount, achievedAmount) {
  const target = Number(targetAmount || 0);
  const achieved = Number(achievedAmount || 0);
  return target > 0 && achieved >= target ? "completed" : "active";
}

function formatDateInputValue(value) {
  const parsed = parseDateValue(value);
  if (!parsed) return "";
  const yyyy = parsed.getFullYear();
  const mm = String(parsed.getMonth() + 1).padStart(2, "0");
  const dd = String(parsed.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function sortedGoals() {
  return state.goals
    .slice()
    .sort((a, b) => {
      const aDate = parseDateValue(a.due_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
      const bDate = parseDateValue(b.due_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
      return aDate - bDate;
    });
}

function primaryGoal() {
  const goals = sortedGoals();
  return goals.find((goal) => goal.status !== "completed") || goals[0] || null;
}

function renderGoalSummary() {
  const summary = document.getElementById("goalSummary");
  const primary = primaryGoal();

  if (!primary) {
    summary.innerHTML = `<p class="empty-state">No goals added yet.</p>`;
    return;
  }

  const target = Number(primary.target_amount || 0);
  const achieved = Number(primary.achieved_amount || 0);
  const progress = goalProgress(primary);

  summary.innerHTML = `
    <div class="goal-main">
      <div>
        <p class="goal-label">${escapeHtml(primary.status === "completed" ? "Completed Goal" : "Target Achieved")}</p>
        <strong>${formatMoney(achieved)}</strong>
        <p class="goal-sub">${escapeHtml(goalTitle(primary))} target ${formatMoney(target)}</p>
        <p class="goal-sub">Due ${escapeHtml(formatDueDate(primary.due_date))}</p>
      </div>
      <div class="goal-meter" style="--progress:${(progress * 3.6).toFixed(0)}deg">
        <span>${progress.toFixed(0)}%</span>
      </div>
    </div>
    <button class="goal-adjust" type="button" data-action="edit-goal" data-id="${escapeHtml(primary.id)}">Adjust Goal</button>
  `;
}

function renderGoalCards() {
  const cards = document.getElementById("goalCards");
  const goals = sortedGoals();

  if (!goals.length) {
    cards.innerHTML = `<p class="empty-state">Create a goal to start tracking target progress.</p>`;
    return;
  }

  cards.innerHTML = goals
    .slice(0, 6)
    .map((goal) => {
      const progress = goalProgress(goal);
      return `
      <article class="goal-card">
        <div class="goal-card-main">
          <div>
            <h4>${escapeHtml(goalTitle(goal))}</h4>
            <small>${escapeHtml(goal.category || "Savings")} &middot; Due ${escapeHtml(formatDueDate(goal.due_date))}</small>
          </div>
          <p>${formatMoney(goal.achieved_amount)} <span>/ ${formatMoney(goal.target_amount)}</span></p>
          <div class="goal-progress" aria-label="${progress.toFixed(0)}% complete">
            <span style="width:${progress.toFixed(2)}%"></span>
          </div>
        </div>
        <div class="goal-card-actions">
          <button class="goal-adjust" type="button" data-action="edit-goal" data-id="${escapeHtml(goal.id)}">Adjust</button>
          <button class="goal-delete" type="button" data-action="delete-goal" data-id="${escapeHtml(goal.id)}">Delete</button>
        </div>
      </article>
      `;
    })
    .join("");
}

function renderGoalChart() {
  const points = sortedGoals().slice(0, 8);
  const labels = points.length ? points.map((goal) => goal.name || goal.category || "Goal") : ["No data"];
  const targetValues = points.length ? points.map((goal) => Number(goal.target_amount || 0)) : [0];
  const savedValues = points.length ? points.map((goal) => Number(goal.achieved_amount || 0)) : [0];

  renderChart("goalChart", {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Saved",
          data: savedValues,
          backgroundColor: "#22a79e",
          borderRadius: 8,
          barThickness: 14
        },
        {
          label: "Target",
          data: targetValues,
          backgroundColor: "#d0d5df",
          borderRadius: 8,
          barThickness: 14
        }
      ]
    },
    options: commonChartOptions("bar"),
    emptyMessage: "Add a goal to see progress."
  });
}

function setModalCopy() {
  const title = document.getElementById("goalModalTitle");
  if (title) title.textContent = state.isEditing ? "Adjust Goal" : "Add Goal";

  const submitButton = document.getElementById("goalSubmitButton");
  if (submitButton) submitButton.textContent = state.isEditing ? "Save Changes" : "Save Goal";
}

function resetEditState() {
  state.isEditing = false;
  state.editingGoalId = null;
  setModalCopy();
}

function openGoalModal() {
  document.getElementById("goalModal")?.classList.remove("hidden");
}

function closeGoalModal() {
  document.getElementById("goalModal")?.classList.add("hidden");
}

function fillGoalForm(goal) {
  const form = document.getElementById("goalForm");
  if (!(form instanceof HTMLFormElement)) return;

  const nameInput = form.elements.namedItem("name");
  if (nameInput instanceof HTMLInputElement) nameInput.value = goal.name || "";

  const categoryInput = form.elements.namedItem("category");
  if (categoryInput instanceof HTMLInputElement) categoryInput.value = goal.category || "";

  const targetInput = form.elements.namedItem("target_amount");
  if (targetInput instanceof HTMLInputElement) targetInput.value = String(Number(goal.target_amount || 0));

  const achievedInput = form.elements.namedItem("achieved_amount");
  if (achievedInput instanceof HTMLInputElement) achievedInput.value = String(Number(goal.achieved_amount || 0));

  const dueDateInput = form.elements.namedItem("due_date");
  if (dueDateInput instanceof HTMLInputElement) dueDateInput.value = formatDateInputValue(goal.due_date);
}

function beginCreateFlow() {
  const form = document.getElementById("goalForm");
  if (form instanceof HTMLFormElement) form.reset();
  resetEditState();
  setDefaultDateInputs();
}

function beginEditFlow(goalId) {
  const goal = state.goals.find((item) => item.id === goalId);
  if (!goal) {
    window.alert("Goal not found.");
    return;
  }

  state.isEditing = true;
  state.editingGoalId = goalId;
  setModalCopy();
  fillGoalForm(goal);
  openGoalModal();
}

function renderGoals() {
  renderGoalSummary();
  renderGoalCards();
  renderGoalChart();
}

function upsertGoal(goal) {
  const existing = state.goals.some((item) => item.id === goal.id);
  state.goals = existing
    ? state.goals.map((item) => (item.id === goal.id ? goal : item))
    : [goal, ...state.goals];
}

function buildGoalPayload(formData) {
  const targetAmount = Number(formData.get("target_amount"));
  const achievedAmount = Number(formData.get("achieved_amount"));
  return {
    name: textOrNull(formData.get("name")),
    category: textOrNull(formData.get("category")),
    target_amount: targetAmount,
    achieved_amount: achievedAmount,
    due_date: formData.get("due_date"),
    status: goalStatus(targetAmount, achievedAmount)
  };
}

async function deleteGoal(goalId) {
  const goal = state.goals.find((item) => item.id === goalId);
  if (!goal) return;

  const shouldDelete = window.confirm(`Delete "${goalTitle(goal)}"?`);
  if (!shouldDelete) return;

  try {
    await deleteJson(`/goals/${goalId}`);
    state.goals = state.goals.filter((item) => item.id !== goalId);
    renderGoals();
  } catch (error) {
    window.alert(describeApiError(error, "delete goal"));
  }
}

function bindGoalActions() {
  document.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const button = target.closest("[data-action][data-id]");
    if (!(button instanceof HTMLButtonElement)) return;

    const action = button.dataset.action;
    const goalId = button.dataset.id;
    if (!action || !goalId) return;

    if (action === "edit-goal") {
      beginEditFlow(goalId);
      return;
    }

    if (action === "delete-goal") {
      await deleteGoal(goalId);
    }
  });
}

function bindModalStateSync() {
  document.getElementById("openGoalModal")?.addEventListener("click", () => {
    beginCreateFlow();
  });

  const modal = document.getElementById("goalModal");
  if (!(modal instanceof HTMLElement)) return;

  modal.querySelectorAll("[data-close='goalModal']").forEach((button) => {
    button.addEventListener("click", () => {
      resetEditState();
    });
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) resetEditState();
  });
}

function bindForm() {
  const form = document.getElementById("goalForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const payload = buildGoalPayload(data);

    try {
      if (state.isEditing && !state.editingGoalId) {
        throw new Error("Missing goal id for edit.");
      }

      const saved = state.isEditing
        ? await putJson(`/goals/${state.editingGoalId}`, payload)
        : await postJson("/goals", payload);

      upsertGoal(saved);
      renderGoals();
      form.reset();
      closeGoalModal();
      resetEditState();
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
    bindModalStateSync();
    bindGoalActions();
    resetEditState();
    setDefaultDateInputs();

    await loadData();
    renderGoals();
    bindForm();
  } catch (error) {
    document.getElementById("goalSummary").innerHTML = "<p>Unable to load goals. Check backend connection.</p>";
    document.getElementById("goalCards").innerHTML = "";
    window.alert(describeApiError(error, "load goals"));
  }
}

initPage();
