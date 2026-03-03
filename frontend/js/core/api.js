const API_BASE = window.SPENDSMART_API_BASE || "http://127.0.0.1:8000";

export const apiState = {
  lastError: null
};

async function parseResponseBody(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return await response.json();
  }

  const text = await response.text();
  return text ? { detail: text } : null;
}

function errorDetail(body) {
  if (!body) return "";
  if (typeof body === "string") return body;
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  return "";
}

function buildRequestError(method, path, response, body) {
  const detail = errorDetail(body);
  const base = `${method} ${path} failed (${response.status})`;
  return new Error(detail ? `${base}: ${detail}` : base);
}

export function describeApiError(error, action = "request") {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return `Unable to ${action}.`;
}

async function requestJson(path, { method = "GET", payload } = {}) {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: payload ? { "Content-Type": "application/json" } : undefined,
      body: payload ? JSON.stringify(payload) : undefined
    });

    if (!response.ok) {
      const body = await parseResponseBody(response);
      throw buildRequestError(method, path, response, body);
    }

    return await parseResponseBody(response);
  } catch (error) {
    apiState.lastError = describeApiError(error, `${method} ${path}`);
    throw error;
  }
}

export async function getJson(path) {
  return requestJson(path, { method: "GET" });
}

export async function postJson(path, payload) {
  return requestJson(path, { method: "POST", payload });
}

export const api = {
  summary: () => getJson("/dashboard/summary"),
  transactions: () => getJson("/transactions"),
  income: () => getJson("/income"),
  expenses: () => getJson("/expenses"),
  bills: () => getJson("/bills"),
  goals: () => getJson("/goals"),
  monthlyExpenseTrend: () => getJson("/statistics/monthly-expense-trend"),
  categoryBreakdown: () => getJson("/statistics/category-breakdown"),
  weeklyComparison: () => getJson("/statistics/weekly-comparison"),
  monthlyComparison: () => getJson("/statistics/monthly-comparison"),
  expensesBreakdown: () => getJson("/expenses/breakdown")
};
