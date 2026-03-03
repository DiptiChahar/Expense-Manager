const chartRegistry = new Map();

export function renderChart(canvasId, config) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined") return;

  const existing = chartRegistry.get(canvasId);
  if (existing) existing.destroy();

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
