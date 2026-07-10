/**
 * theme.js
 * Handles dark/light theme toggling, sidebar collapse, and the
 * notifications dropdown. Runs on every page (included from base.html).
 */
(function () {
  "use strict";

  const cfg = window.__DASHBOARD_CONFIG__ || {};
  const root = document.documentElement;
  const body = document.body;

  // ---------------------------------------------------------------------
  // Theme toggle
  // ---------------------------------------------------------------------
  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("ai-dashboard-theme", theme);
  }

  function persistTheme(theme) {
    fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme }),
    }).catch(() => {
      /* non-fatal: theme still applied client-side */
    });
  }

  const storedTheme = localStorage.getItem("ai-dashboard-theme");
  if (storedTheme && storedTheme !== root.getAttribute("data-theme")) {
    applyTheme(storedTheme);
  }

  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      persistTheme(next);
      document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.themeChoice === next);
      });
    });
  }

  // Settings page: explicit theme picker buttons
  document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const theme = btn.dataset.themeChoice;
      applyTheme(theme);
      persistTheme(theme);
      document.querySelectorAll("[data-theme-choice]").forEach((b) => b.classList.toggle("active", b === btn));
    });
  });

  // ---------------------------------------------------------------------
  // Sidebar collapse (persist across reloads, auto-collapse on mobile)
  // ---------------------------------------------------------------------
  const sidebarToggle = document.getElementById("sidebarToggle");
  const collapsedStored = localStorage.getItem("ai-dashboard-sidebar-collapsed") === "true";
  if (collapsedStored && window.innerWidth > 1024) {
    body.classList.add("sidebar-collapsed");
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      body.classList.toggle("sidebar-collapsed");
      localStorage.setItem("ai-dashboard-sidebar-collapsed", body.classList.contains("sidebar-collapsed"));
    });
  }

  // ---------------------------------------------------------------------
  // Notifications dropdown
  // ---------------------------------------------------------------------
  const notifToggle = document.getElementById("notifToggle");
  const notifPanel = document.getElementById("notifPanel");
  const notifBadge = document.getElementById("notifBadge");
  const markAllReadBtn = document.getElementById("markAllReadBtn");

  if (notifToggle && notifPanel) {
    notifToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      notifPanel.classList.toggle("open");
    });

    document.addEventListener("click", (e) => {
      if (!notifPanel.contains(e.target) && e.target !== notifToggle) {
        notifPanel.classList.remove("open");
      }
    });
  }

  if (markAllReadBtn) {
    markAllReadBtn.addEventListener("click", () => {
      fetch("/api/dashboard/notifications/read-all", { method: "POST" })
        .then(() => {
          document.querySelectorAll(".notif-item.unread").forEach((el) => el.classList.remove("unread"));
          if (notifBadge) {
            notifBadge.textContent = "0";
            notifBadge.classList.add("hidden");
          }
        })
        .catch(() => {});
    });
  }
})();
