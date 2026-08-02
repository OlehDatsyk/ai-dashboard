/**
 * chat.js
 * Floating AI chat widget available on every page except the full
 * Chat & Playground page (which has its own richer implementation in
 * dashboard.js). Uses the non-streaming /api/ai/chat endpoint for
 * simplicity.
 */
(function () {
  "use strict";

  const fab = document.getElementById("chatWidgetFab");
  const panel = document.getElementById("chatWidgetPanel");
  const closeBtn = document.getElementById("chatWidgetClose");
  const form = document.getElementById("chatWidgetForm");
  const input = document.getElementById("chatWidgetInput");
  const messages = document.getElementById("chatWidgetMessages");

  if (!fab || !panel || !form) return;

  const cfg = window.__DASHBOARD_CONFIG__ || {};
  const history = [];

  fab.addEventListener("click", () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) input.focus();
  });

  closeBtn?.addEventListener("click", () => panel.classList.remove("open"));

  function appendMessage(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `chat-msg chat-msg-${role}`;
    const p = document.createElement("p");
    p.textContent = text;
    bubble.appendChild(p);
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text || !cfg.aiConfigured) return;

    appendMessage("user", text);
    history.push({ role: "user", content: text });
    input.value = "";
    input.disabled = true;

    const thinking = appendMessage("assistant", "Thinking…");

    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: history.slice(0, -1),
          system_prompt: cfg.systemPrompt,
          model: cfg.defaultModel,
          temperature: cfg.defaultTemperature,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");

      thinking.querySelector("p").textContent = data.text;
      history.push({ role: "assistant", content: data.text });
    } catch (err) {
      thinking.querySelector("p").textContent = `Something went wrong: ${err.message}`;
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
})();
