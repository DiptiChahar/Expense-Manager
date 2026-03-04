import { bootstrapAuth, getToken, handleUnauthorized } from "./auth.js";

const API_BASE = window.SPENDSMART_API_BASE || "http://127.0.0.1:8000/api/v1";

export const apiState = {
  lastError: null
};

bootstrapAuth();

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
  if (body.error && typeof body.error.message === "string") return body.error.message;
  if (typeof body.message === "string") return body.message;
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  return "";
}

function errorCode(body) {
  if (!body || typeof body === "string") return null;
  if (body.error && typeof body.error.code === "string") return body.error.code;
  if (typeof body.code === "string") return body.code;
  return null;
}

function buildRequestError(method, path, response, body) {
  const detail = errorDetail(body);
  const code = errorCode(body);
  const base = `${method} ${path} failed (${response.status})`;
  const error = new Error(detail ? `${base}: ${detail}` : base);
  error.status = response.status;
  error.code = code;
  error.body = body;
  error.uiMessage = detail || "";
  return error;
}

export function describeApiError(error, action = "request") {
  if (error && typeof error === "object" && typeof error.uiMessage === "string" && error.uiMessage) {
    return error.uiMessage;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return `Unable to ${action}.`;
}

async function requestJson(path, { method = "GET", payload, skipAuth = false, headers = {} } = {}) {
  const requestHeaders = { ...headers };

  if (payload !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
  }

  if (!skipAuth) {
    const token = getToken();
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: Object.keys(requestHeaders).length > 0 ? requestHeaders : undefined,
      body: payload !== undefined ? JSON.stringify(payload) : undefined
    });

    if (!response.ok) {
      const body = await parseResponseBody(response);
      if (response.status === 401 && !skipAuth) {
        handleUnauthorized();
      }
      throw buildRequestError(method, path, response, body);
    }

    return await parseResponseBody(response);
  } catch (error) {
    apiState.lastError = describeApiError(error, `${method} ${path}`);
    throw error;
  }
}

export async function getJson(path, options = {}) {
  return requestJson(path, { method: "GET", ...options });
}

export async function postJson(path, payload, options = {}) {
  return requestJson(path, { method: "POST", payload, ...options });
}

export async function putJson(path, payload, options = {}) {
  return requestJson(path, { method: "PUT", payload, ...options });
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

export const authApi = {
  login: (payload) => postJson("/auth/login", payload, { skipAuth: true }),
  register: (payload) => postJson("/auth/register", payload, { skipAuth: true }),
  me: () => getJson("/auth/me")
};
