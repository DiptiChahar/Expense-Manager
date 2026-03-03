export function formatMoney(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(amount);
}

export function parseDateValue(value) {
  if (!value) return null;
  const input = String(value).trim();
  if (!input) return null;

  const dateOnlyMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(input);
  if (dateOnlyMatch) {
    const year = Number(dateOnlyMatch[1]);
    const monthIndex = Number(dateOnlyMatch[2]) - 1;
    const day = Number(dateOnlyMatch[3]);
    const localDate = new Date(year, monthIndex, day);
    return Number.isNaN(localDate.getTime()) ? null : localDate;
  }

  const parsed = new Date(input);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function monthYear(isoDate) {
  const date = parseDateValue(isoDate);
  if (!date) return "-";
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export function formatEntryDate(isoDate) {
  const date = parseDateValue(isoDate);
  if (!date) return "-";
  const dd = String(date.getDate()).padStart(2, "0");
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const yyyy = String(date.getFullYear());
  return `${dd}/${mm}/${yyyy}`;
}

export function formatDueDate(isoDate) {
  const date = parseDateValue(isoDate);
  if (!date) return "-";
  return date.toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric" });
}

export function shortMonth(isoDate) {
  const date = parseDateValue(isoDate);
  if (!date) return "-";
  return date.toLocaleDateString("en-US", { month: "short" });
}

export function dayOfMonth(isoDate) {
  const date = parseDateValue(isoDate);
  if (!date) return "-";
  return String(date.getDate());
}

export function normalizeStatus(status) {
  return String(status || "submitted").toLowerCase().includes("not") ? "not_submitted" : "submitted";
}

export function humanStatus(status) {
  return normalizeStatus(status) === "submitted" ? "Submitted" : "Not Submitted";
}

export function textOrNull(value) {
  const val = String(value || "").trim();
  return val ? val : null;
}

export function capitalize(value) {
  const str = String(value || "");
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
