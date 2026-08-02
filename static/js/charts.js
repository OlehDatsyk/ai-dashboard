/**
 * charts.js
 * Chart.js setup for the dashboard overview page. Each function fetches
 * its data from the Flask analytics API and renders a themed chart.
 * Exposed on window.DashboardCharts so dashboard.js can trigger re-renders
 * (e.g. after the theme changes).
 */
(function () {
  "use strict";

  if (typeof Chart === "undefined") return;

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function baseColors() {
    return {
      primary: cssVar("--primary") || "#7c5cfc",
      accent: cssVar("--accent") || "#22d3b8",
      warning: cssVar("--warning") || "#f5a623",
      danger: cssVar("--danger") || "#f2545b",
      textSecondary: cssVar("--text-secondary") || "#9aa1b8",
      border: cssVar("--border") || "#232838",
      surface: cssVar("--surface") || "#12151f",
    };
  }

  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 11;

  function commonGridOptions() {
    const c = baseColors();
    return {
      grid: { color: c.border, drawTicks: false },
      ticks: { color: c.textSecondary },
      border: { display: false },
    };
  }

  function hexToRgba(hex, alpha) {
    const clean = hex.replace("#", "");
    const bigint = parseInt(clean, 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  const charts = {};

  function upsertChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas) return null;
    if (charts[id]) {
      charts[id].destroy();
    }
    charts[id] = new Chart(canvas.getContext("2d"), config);
    return charts[id];
  }

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Request failed: ${url}`);
    return res.json();
  }

  async function renderRequestsChart() {
    const data = await fetchJSON("/api/dashboard/charts/requests?days=14");
    const c = baseColors();
    upsertChart("chartRequests", {
      type: "line",
      data: {
        labels: data.labels.map(shortDate),
        datasets: [
          {
            label: "Requests",
            data: data.values,
            borderColor: c.primary,
            backgroundColor: hexToRgba(c.primary, 0.15),
            fill: true,
            tension: 0.35,
            pointRadius: 0,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: commonGridOptions(), y: { ...commonGridOptions(), beginAtZero: true } },
      },
    });
  }

  async function renderTokensChart() {
    const data = await fetchJSON("/api/dashboard/charts/tokens?days=14");
    const c = baseColors();
    upsertChart("chartTokens", {
      type: "bar",
      data: {
        labels: data.labels.map(shortDate),
        datasets: [
          { label: "Prompt tokens", data: data.prompt_tokens, backgroundColor: hexToRgba(c.primary, 0.75), stack: "tokens" },
          { label: "Completion tokens", data: data.completion_tokens, backgroundColor: hexToRgba(c.accent, 0.75), stack: "tokens" },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom", labels: { color: c.textSecondary, boxWidth: 10 } } },
        scales: {
          x: { ...commonGridOptions(), stacked: true },
          y: { ...commonGridOptions(), stacked: true, beginAtZero: true },
        },
      },
    });
  }

  async function renderCostsChart() {
    const data = await fetchJSON("/api/dashboard/charts/costs?days=14");
    const c = baseColors();
    upsertChart("chartCosts", {
      type: "line",
      data: {
        labels: data.labels.map(shortDate),
        datasets: [
          {
            label: "Estimated cost",
            data: data.values,
            borderColor: c.warning,
            backgroundColor: hexToRgba(c.warning, 0.15),
            fill: true,
            tension: 0.35,
            pointRadius: 0,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: commonGridOptions(), y: { ...commonGridOptions(), beginAtZero: true } },
      },
    });
  }

  async function renderResponseTimesChart() {
    const data = await fetchJSON("/api/dashboard/charts/response-times?days=14");
    const c = baseColors();
    upsertChart("chartResponseTimes", {
      type: "bar",
      data: {
        labels: data.labels.map(shortDate),
        datasets: [{ label: "Avg. response time (ms)", data: data.values, backgroundColor: hexToRgba(c.danger, 0.65), borderRadius: 4 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: commonGridOptions(), y: { ...commonGridOptions(), beginAtZero: true } },
      },
    });
  }

  async function renderCategoriesChart() {
    const data = await fetchJSON("/api/dashboard/charts/categories");
    const c = baseColors();
    const palette = [c.primary, c.accent, c.warning, c.danger, "#5b8def", "#c084fc"];
    upsertChart("chartCategories", {
      type: "doughnut",
      data: {
        labels: data.labels.length ? data.labels : ["No data yet"],
        datasets: [
          {
            data: data.values.length ? data.values : [1],
            backgroundColor: data.labels.length ? palette : [c.border],
            borderColor: c.surface,
            borderWidth: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: { legend: { position: "bottom", labels: { color: c.textSecondary, boxWidth: 10 } } },
      },
    });
  }

  function shortDate(isoDate) {
    const d = new Date(isoDate + "T00:00:00");
    if (Number.isNaN(d.getTime())) return isoDate;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  async function renderAll() {
    await Promise.allSettled([
      renderRequestsChart(),
      renderTokensChart(),
      renderCostsChart(),
      renderResponseTimesChart(),
      renderCategoriesChart(),
    ]);
  }

  window.DashboardCharts = { renderAll };

  document.addEventListener("DOMContentLoaded", renderAll);
})();
