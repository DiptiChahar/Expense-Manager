function prettyDate() {
  const now = new Date();
  const pretty = now.toLocaleDateString("en-US", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
  return `» ${pretty}`;
}

async function mountComponent(path, targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;

  try {
    const res = await fetch(path);
    if (!res.ok) {
      throw new Error(`Component load failed (${res.status})`);
    }
    const html = await res.text();
    target.innerHTML = html;
  } catch (error) {
    console.error(`Unable to mount component ${path}`, error);
    target.innerHTML = "";
  }
}

function bindSidebarMenu() {
  const sidebar = document.getElementById("sidebar");
  const menuBtn = document.getElementById("menuBtn");
  if (!sidebar || !menuBtn) return;

  menuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });

  document.addEventListener("click", (event) => {
    if (window.innerWidth > 1080) return;
    if (!sidebar.contains(event.target) && !menuBtn.contains(event.target)) {
      sidebar.classList.remove("open");
    }
  });
}

function setActiveNav(activeKey) {
  document.querySelectorAll("[data-nav]").forEach((item) => {
    item.classList.toggle("active", item.dataset.nav === activeKey);
  });
}

function setDateChip() {
  const node = document.getElementById("todayDate");
  if (node) node.textContent = prettyDate();
}

export async function initLayout(activeKey) {
  await Promise.all([
    mountComponent("/components/sidebar.html", "sidebarMount"),
    mountComponent("/components/topbar.html", "topbarMount")
  ]);

  setActiveNav(activeKey);
  setDateChip();
  bindSidebarMenu();
}
