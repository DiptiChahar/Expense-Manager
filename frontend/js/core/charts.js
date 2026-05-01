const chartRegistry = new Map();

function chartFallbackId(canvasId) {
  return `${canvasId}Fallback`;
}

function getFallback(canvas) {
  const canvasId = canvas.id;
  let fallback = document.getElementById(chartFallbackId(canvasId));

  if (!fallback) {
    fallback = document.createElement("div");
    fallback.id = chartFallbackId(canvasId);
    fallback.className = "chart-empty hidden";
    canvas.insertAdjacentElement("afterend", fallback);
  }

  return fallback;
}

function setChartFallback(canvas, message) {
  const fallback = getFallback(canvas);
  const hasMessage = Boolean(message);
  fallback.textContent = message || "";
  fallback.classList.toggle("hidden", !hasMessage);
  canvas.classList.toggle("hidden", hasMessage);
}

function hasRenderableData(config) {
  const datasets = config?.data?.datasets;
  if (!Array.isArray(datasets) || datasets.length === 0) return false;

  return datasets.some((dataset) => {
    if (!Array.isArray(dataset.data)) return false;
    return dataset.data.some((value) => Number(value) > 0);
  });
}

export function renderChart(canvasId, config) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const existing = chartRegistry.get(canvasId);
  if (existing) {
    existing.destroy();
    chartRegistry.delete(canvasId);
  }

  if (!hasRenderableData(config)) {
    setChartFallback(canvas, config?.emptyMessage || "No chart data yet.");
    return;
  }

  if (typeof Chart === "undefined") {
    setChartFallback(canvas, "Charts are unavailable. Check your internet connection and reload.");
    return;
  }

  setChartFallback(canvas, "");
  const chart = new Chart(canvas, config);
  chartRegistry.set(canvasId, chart);
}

export function commonChartOptions(type) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        grid: { display: false }
      },
      y: {
        beginAtZero: true,
        grid: { color: "rgba(93,104,125,0.18)" }
      }
    },
    plugins: {
      legend: {
        position: "top",
        align: "end",
        labels: {
          boxWidth: 14,
          boxHeight: 8,
          useBorderRadius: true,
          borderRadius: 3
        }
      }
    },
    elements: type === "line" ? { line: { borderWidth: 2.2 } } : {}
  };
}
