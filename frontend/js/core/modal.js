export function setDefaultDateInputs() {
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  document.querySelectorAll('input[type="date"]').forEach((input) => {
    if (!input.value) input.value = today;
  });
}

export function initModal(openButtonId, modalId) {
  const openButton = document.getElementById(openButtonId);
  const modal = document.getElementById(modalId);
  if (!openButton || !modal) return;

  openButton.addEventListener("click", () => {
    modal.classList.remove("hidden");
  });
}

export function bindModalClose() {
  document.querySelectorAll("[data-close]").forEach((button) => {
    button.addEventListener("click", () => {
      const modal = document.getElementById(button.dataset.close);
      modal?.classList.add("hidden");
    });
  });

  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        modal.classList.add("hidden");
      }
    });
  });
}
