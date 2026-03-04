const TOKEN_KEY = "spendsmart_token";
const API_BASE = window.SPENDSMART_API_BASE || "http://127.0.0.1:8000/api/v1";

const PROTECTED_PATHS = new Set([
  "/html/dashboard.html",
  "/html/transactions.html",
  "/html/income.html",
  "/html/expenses.html",
  "/html/bills.html",
  "/html/goals.html"
]);

const AUTH_PATHS = new Set([
  "/html/login.html",
  "/html/register.html"
]);

let isLogoutBindingAttached = false;
let currentUserCache = null;

function normalizePath(pathname = window.location.pathname) {
  if (!pathname) return "/";
  if (pathname.length > 1 && pathname.endsWith("/")) return pathname.slice(0, -1);
  return pathname;
}

function redirectToLogin() {
  if (normalizePath() !== "/html/login.html") {
    window.location.replace("/html/login.html");
  }
}

function redirectToDashboard() {
  if (normalizePath() !== "/html/dashboard.html") {
    window.location.replace("/html/dashboard.html");
  }
}

function isProtectedPath(pathname = normalizePath()) {
  return PROTECTED_PATHS.has(pathname);
}

function isAuthPath(pathname = normalizePath()) {
  return AUTH_PATHS.has(pathname);
}

export function setToken(token) {
  const normalized = typeof token === "string" ? token.trim() : "";
  if (!normalized) {
    localStorage.removeItem(TOKEN_KEY);
    currentUserCache = null;
    return;
  }
  localStorage.setItem(TOKEN_KEY, normalized);
  currentUserCache = null;
}

export function getToken() {
  const token = localStorage.getItem(TOKEN_KEY);
  const normalized = typeof token === "string" ? token.trim() : "";
  return normalized || null;
}

export function isAuthenticated() {
  return Boolean(getToken());
}

export function logout({ redirect = true } = {}) {
  localStorage.removeItem(TOKEN_KEY);
  currentUserCache = null;
  if (redirect) redirectToLogin();
}

export function ensureAuthRouteAccess() {
  const pathname = normalizePath();

  if (isProtectedPath(pathname) && !isAuthenticated()) {
    redirectToLogin();
    return false;
  }

  if (isAuthPath(pathname) && isAuthenticated()) {
    redirectToDashboard();
    return false;
  }

  return true;
}

export function handleUnauthorized() {
  logout({ redirect: true });
}

export function getUserInitial(name) {
  const normalized = String(name || "").trim();
  if (!normalized) return "?";
  return normalized.charAt(0).toUpperCase();
}

export async function getCurrentUser({ force = false } = {}) {
  if (!force && currentUserCache) {
    return currentUserCache;
  }

  const token = getToken();
  if (!token) {
    handleUnauthorized();
    return null;
  }

  try {
    const response = await fetch(`${API_BASE}/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (response.status === 401) {
      handleUnauthorized();
      return null;
    }

    if (!response.ok) {
      throw new Error(`GET /auth/me failed (${response.status})`);
    }

    const data = await response.json();
    if (!data || typeof data.name !== "string") {
      throw new Error("Invalid /auth/me response shape");
    }

    currentUserCache = {
      id: data.id,
      name: data.name,
      email: data.email,
      created_at: data.created_at
    };
    return currentUserCache;
  } catch (error) {
    console.error("Unable to fetch current user.", error);
    return null;
  }
}

function bindLogoutButton() {
  if (isLogoutBindingAttached) return;
  isLogoutBindingAttached = true;

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const logoutButton = event.target.closest(".sidebar-footer .ghost-btn");
    if (!logoutButton) return;
    event.preventDefault();
    logout({ redirect: true });
  });
}

export function bootstrapAuth() {
  bindLogoutButton();
  return ensureAuthRouteAccess();
}
