import { authApi } from "../core/api.js";
import { isAuthenticated, setToken } from "../core/auth.js";

const DASHBOARD_PATH = "/html/dashboard.html";

const ERROR_MESSAGES = {
  UNAUTHORIZED: "Invalid email or password"
};

function redirectToDashboard() {
  window.location.replace(DASHBOARD_PATH);
}

function getErrorCode(error) {
  if (!error || typeof error !== "object") return "";
  return typeof error.code === "string" ? error.code : "";
}

function getReadableMessage(error) {
  if (!error || typeof error !== "object") return "";
  if (typeof error.uiMessage === "string" && error.uiMessage) return error.uiMessage;
  return "";
}

function mapAuthError(error) {
  const code = getErrorCode(error);
  if (code && ERROR_MESSAGES[code]) return ERROR_MESSAGES[code];
  return getReadableMessage(error) || "Unable to sign in right now. Please try again.";
}

function setSubmitting(button, isSubmitting) {
  if (!button) return;
  if (!button.dataset.defaultText) button.dataset.defaultText = button.textContent || "Sign In";
  button.disabled = isSubmitting;
  button.textContent = isSubmitting ? "Signing In..." : button.dataset.defaultText;
}

function showError(node, message) {
  if (!node) return;
  if (!message) {
    node.textContent = "";
    node.classList.add("hidden");
    return;
  }
  node.textContent = message;
  node.classList.remove("hidden");
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const submitButton = document.getElementById("submitButton");
  const errorNode = document.getElementById("authError");

  showError(errorNode, "");
  setSubmitting(submitButton, true);

  try {
    const payload = {
      email: form.email.value.trim(),
      password: form.password.value
    };

    const response = await authApi.login(payload);
    if (!response || !response.access_token) {
      throw new Error("Authentication token was not returned.");
    }

    setToken(response.access_token);
    redirectToDashboard();
  } catch (error) {
    showError(errorNode, mapAuthError(error));
  } finally {
    setSubmitting(submitButton, false);
  }
}

function initPage() {
  if (isAuthenticated()) {
    redirectToDashboard();
    return;
  }

  const form = document.getElementById("loginForm");
  if (!form) return;

  form.addEventListener("submit", handleSubmit);
}

initPage();
