/**
 * dashboard.js
 * Page-specific interactivity, split by feature-detecting DOM elements so
 * a single file can be safely included on every page.
 */
(function () {
  "use strict";

  const cfg = window.__DASHBOARD_CONFIG__ || {};

  // =====================================================================
  // Shared helpers
  // =====================================================================
  function formatCurrency(value) {
    return `${cfg.currencySymbol || "$"}${Number(value).toFixed(5)}`;
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // =====================================================================
  // Sidebar usage mini-card (all pages)
  // =====================================================================
  async function loadSidebarUsage() {
    const costEl = document.getElementById("sidebarMonthCost");
    const barEl = document.getElementById("sidebarUsageBar");
    if (!costEl || !barEl) return;
    try {
      const res = await fetch("/api/dashboard/summary");
      const data = await res.json();
      const monthCost = data.month.cost || 0;
      costEl.textContent = `${cfg.currencySymbol || "$"}${monthCost.toFixed(2)}`;
      // Visualize against an illustrative $20 soft budget ceiling.
      const pct = Math.min(100, (monthCost / 20) * 100);
      barEl.style.width = `${pct}%`;
    } catch (err) {
      /* non-fatal */
    }
  }
  loadSidebarUsage();

  // =====================================================================
  // DASHBOARD PAGE — most used prompts
  // =====================================================================
  const mostUsedList = document.getElementById("mostUsedPrompts");
  if (mostUsedList) {
    fetch("/api/dashboard/most-used-prompts?limit=6")
      .then((res) => res.json())
      .then((items) => {
        if (!items.length) {
          mostUsedList.innerHTML = '<li class="ranked-empty">No prompt activity recorded yet.</li>';
          return;
        }
        mostUsedList.innerHTML = items
          .map(
            (item) => `
            <li>
              <span class="prompt-snippet" title="${escapeHtml(item.prompt)}">${escapeHtml(item.prompt)}</span>
              <span class="prompt-count">${item.count}×</span>
            </li>`
          )
          .join("");
      })
      .catch(() => {
        mostUsedList.innerHTML = '<li class="ranked-empty">Could not load prompt statistics.</li>';
      });
  }

  // =====================================================================
  // SETTINGS PAGE
  // =====================================================================
  const profileForm = document.getElementById("profileForm");
  if (profileForm) {
    profileForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(profileForm);
      const payload = Object.fromEntries(formData.entries());
      const btn = profileForm.querySelector("button[type=submit]");
      const original = btn.textContent;
      btn.textContent = "Saving…";
      btn.disabled = true;
      try {
        await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        btn.textContent = "Saved ✓";
      } catch {
        btn.textContent = "Error saving";
      } finally {
        setTimeout(() => {
          btn.textContent = original;
          btn.disabled = false;
        }, 1400);
      }
    });
  }

  const aiSettingsForm = document.getElementById("aiSettingsForm");
  const tempSlider = document.getElementById("tempSlider");
  const tempOutput = document.getElementById("tempOutput");
  if (tempSlider && tempOutput) {
    tempSlider.addEventListener("input", () => (tempOutput.textContent = tempSlider.value));
  }
  if (aiSettingsForm) {
    aiSettingsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(aiSettingsForm);
      const payload = Object.fromEntries(formData.entries());
      payload.default_temperature = parseFloat(payload.default_temperature);
      const btn = aiSettingsForm.querySelector("button[type=submit]");
      const original = btn.textContent;
      btn.textContent = "Saving…";
      btn.disabled = true;
      try {
        await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        btn.textContent = "Saved ✓";
      } catch {
        btn.textContent = "Error saving";
      } finally {
        setTimeout(() => {
          btn.textContent = original;
          btn.disabled = false;
        }, 1400);
      }
    });
  }

  // =====================================================================
  // CHAT & PLAYGROUND PAGE
  // =====================================================================
  const conversation = document.getElementById("conversation");
  if (!conversation) return; // Not on the chat page — stop here.

  const state = {
    chatHistory: [],
    history: [], // { prompt, model, tokens, cost, time, response }
  };

  // ---------------------------- Tabs (Chat / Playground) ----------------------------
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => {
        b.classList.toggle("active", b === btn);
        b.setAttribute("aria-selected", b === btn ? "true" : "false");
      });
      document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
        panel.classList.toggle("hidden", panel.dataset.tabPanel !== btn.dataset.tab);
      });
    });
  });

  // ---------------------------- Run settings ----------------------------
  const modelSelect = document.getElementById("modelSelect");
  const temperatureSlider = document.getElementById("temperatureSlider");
  const playgroundTempOutput = document.getElementById("playgroundTempOutput");
  const streamToggle = document.getElementById("streamToggle");
  const systemPromptEditor = document.getElementById("systemPromptEditor");

  temperatureSlider?.addEventListener("input", () => {
    playgroundTempOutput.textContent = temperatureSlider.value;
  });

  function currentSettings() {
    return {
      model: modelSelect ? modelSelect.value : cfg.defaultModel,
      temperature: temperatureSlider ? parseFloat(temperatureSlider.value) : cfg.defaultTemperature,
      systemPrompt: systemPromptEditor ? systemPromptEditor.value : cfg.systemPrompt,
      stream: streamToggle ? streamToggle.checked : true,
    };
  }

  // ---------------------------- Stats + history ----------------------------
  const statPromptTokens = document.getElementById("statPromptTokens");
  const statCompletionTokens = document.getElementById("statCompletionTokens");
  const statResponseTime = document.getElementById("statResponseTime");
  const statCost = document.getElementById("statCost");
  const promptHistoryList = document.getElementById("promptHistory");

  function updateStats({ promptTokens, completionTokens, responseTimeMs, model }) {
    statPromptTokens.textContent = promptTokens;
    statCompletionTokens.textContent = completionTokens;
    statResponseTime.textContent = `${responseTimeMs} ms`;
    // Client-side cost estimate mirrors the server's pricing table roughly;
    // exact figures are recorded server-side for the analytics dashboard.
    statCost.textContent = formatCurrency(0); // Refreshed from server summary below.
    refreshCostEstimate();
  }

  async function refreshCostEstimate() {
    try {
      const res = await fetch("/api/dashboard/summary");
      const data = await res.json();
      statCost.textContent = formatCurrency(data.today.cost);
    } catch {
      /* ignore */
    }
  }

  function pushHistory(entry) {
    state.history.unshift(entry);
    state.history = state.history.slice(0, 12);
    renderHistory();
  }

  function renderHistory() {
    if (!state.history.length) {
      promptHistoryList.innerHTML = '<li class="history-empty">No requests yet this session.</li>';
      return;
    }
    promptHistoryList.innerHTML = state.history
      .map(
        (item, idx) => `
        <li class="history-item" data-history-index="${idx}">
          <span class="history-prompt">${escapeHtml(item.prompt)}</span>
          <span class="history-meta">${item.model} · ${item.tokens} tok · ${item.time} ms</span>
        </li>`
      )
      .join("");
  }

  promptHistoryList?.addEventListener("click", (e) => {
    const li = e.target.closest("[data-history-index]");
    if (!li) return;
    const entry = state.history[Number(li.dataset.historyIndex)];
    if (!entry) return;
    document.getElementById("playgroundInput").value = entry.prompt;
    renderOutput(entry.response, entry.jsonMode);
    document.querySelector('.tab-btn[data-tab="playground"]').click();
  });

  // ---------------------------- Chat tab (streaming) ----------------------------
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");

  function appendChatBubble(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `chat-msg chat-msg-${role}`;
    const p = document.createElement("p");
    p.textContent = text;
    bubble.appendChild(p);
    conversation.appendChild(bubble);
    conversation.scrollTop = conversation.scrollHeight;
    return { bubble, textEl: p };
  }

  async function streamChat(userText) {
    const settings = currentSettings();
    const { textEl } = appendChatBubble("assistant", "");
    let fullText = "";

    const response = await fetch("/api/ai/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userText,
        history: state.chatHistory,
        system_prompt: settings.systemPrompt,
        model: settings.model,
        temperature: settings.temperature,
      }),
    });

    if (!response.ok || !response.body) {
      const data = await response.json().catch(() => ({}));
      textEl.textContent = data.error || "Something went wrong while streaming the response.";
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop(); // keep the last, possibly incomplete, chunk

      for (const evt of events) {
        const line = evt.replace(/^data:\s*/, "").trim();
        if (!line) continue;
        let payload;
        try {
          payload = JSON.parse(line);
        } catch {
          continue;
        }
        if (payload.delta) {
          fullText += payload.delta;
          textEl.textContent = fullText;
          conversation.scrollTop = conversation.scrollHeight;
        } else if (payload.error) {
          textEl.textContent = `Error: ${payload.error}`;
        } else if (payload.done) {
          updateStats({
            promptTokens: payload.prompt_tokens,
            completionTokens: payload.completion_tokens,
            responseTimeMs: payload.response_time_ms,
            model: settings.model,
          });
        }
      }
    }

    state.chatHistory.push({ role: "user", content: userText });
    state.chatHistory.push({ role: "assistant", content: fullText });
  }

  async function sendChatNonStreaming(userText) {
    const settings = currentSettings();
    const { textEl } = appendChatBubble("assistant", "Thinking…");
    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userText,
          history: state.chatHistory,
          system_prompt: settings.systemPrompt,
          model: settings.model,
          temperature: settings.temperature,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");
      textEl.textContent = data.text;
      state.chatHistory.push({ role: "user", content: userText });
      state.chatHistory.push({ role: "assistant", content: data.text });
      updateStats({
        promptTokens: data.prompt_tokens,
        completionTokens: data.completion_tokens,
        responseTimeMs: data.response_time_ms,
        model: settings.model,
      });
    } catch (err) {
      textEl.textContent = `Error: ${err.message}`;
    }
  }

  chatForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    appendChatBubble("user", text);
    chatInput.value = "";
    chatInput.disabled = true;

    const settings = currentSettings();
    try {
      if (settings.stream) {
        await streamChat(text);
      } else {
        await sendChatNonStreaming(text);
      }
    } finally {
      chatInput.disabled = false;
      chatInput.focus();
    }
  });

  // ---------------------------- Playground tab ----------------------------
  const playgroundInput = document.getElementById("playgroundInput");
  const runPlaygroundBtn = document.getElementById("runPlaygroundBtn");
  const jsonModeToggle = document.getElementById("jsonModeToggle");
  const outputRendered = document.getElementById("outputRendered");
  const outputJson = document.getElementById("outputJson");
  const outputRaw = document.getElementById("outputRaw");

  function renderOutput(text, jsonMode) {
    outputRaw.textContent = text;

    // Rendered / Markdown view
    if (window.marked) {
      outputRendered.innerHTML = window.marked.parse(text || "");
    } else {
      outputRendered.textContent = text;
    }

    // JSON view: try to parse and pretty-print, otherwise show a hint.
    try {
      const parsed = JSON.parse(text);
      outputJson.textContent = JSON.stringify(parsed, null, 2);
    } catch {
      outputJson.textContent = jsonMode
        ? "The model did not return valid JSON."
        : "// Output is not valid JSON.\n// Enable \"Request structured JSON output\" for guaranteed JSON.";
    }
  }

  document.querySelectorAll("[data-output-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-output-view]").forEach((b) => b.classList.toggle("active", b === btn));
      const view = btn.dataset.outputView;
      outputRendered.classList.toggle("hidden", view !== "rendered");
      outputJson.classList.toggle("hidden", view !== "json");
      outputRaw.classList.toggle("hidden", view !== "raw");
    });
  });

  runPlaygroundBtn?.addEventListener("click", async () => {
    const prompt = playgroundInput.value.trim();
    if (!prompt) return;
    const settings = currentSettings();
    const jsonMode = jsonModeToggle.checked;

    runPlaygroundBtn.disabled = true;
    runPlaygroundBtn.textContent = "Running…";
    outputRendered.innerHTML = '<p class="output-placeholder">Waiting for response…</p>';

    try {
      const res = await fetch("/api/ai/playground", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          system_prompt: settings.systemPrompt,
          model: settings.model,
          temperature: settings.temperature,
          json_mode: jsonMode,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");

      renderOutput(data.text, jsonMode);
      updateStats({
        promptTokens: data.prompt_tokens,
        completionTokens: data.completion_tokens,
        responseTimeMs: data.response_time_ms,
        model: settings.model,
      });
      pushHistory({
        prompt,
        model: settings.model,
        tokens: data.total_tokens,
        time: data.response_time_ms,
        response: data.text,
        jsonMode,
      });
    } catch (err) {
      outputRendered.innerHTML = `<p class="output-placeholder">Error: ${escapeHtml(err.message)}</p>`;
    } finally {
      runPlaygroundBtn.disabled = false;
      runPlaygroundBtn.textContent = "Run prompt";
    }
  });

  // ---------------------------- Prompt library ----------------------------
  const promptList = document.getElementById("promptList");
  const savePromptForm = document.getElementById("savePromptForm");

  promptList?.addEventListener("click", async (e) => {
    const useBtn = e.target.closest('[data-action="use-prompt"]');
    const favBtn = e.target.closest('[data-action="toggle-favorite"]');
    const li = e.target.closest(".prompt-list-item");
    if (!li) return;
    const id = li.dataset.id;

    if (useBtn) {
      const title = useBtn.querySelector(".prompt-title").textContent;
      // Fetch full content since the DOM only stores the title.
      const res = await fetch("/api/prompts");
      const prompts = await res.json();
      const match = prompts.find((p) => p.id === id);
      if (match) {
        playgroundInput.value = match.content;
        document.querySelector('.tab-btn[data-tab="playground"]').click();
        playgroundInput.focus();
      }
    }

    if (favBtn) {
      const res = await fetch(`/api/prompts/${id}/favorite`, { method: "POST" });
      const updated = await res.json();
      favBtn.classList.toggle("active", updated.favorite);
      li.dataset.favorite = String(updated.favorite);
      applyLibraryFilter();
    }
  });

  document.querySelectorAll(".library-filters .chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".library-filters .chip").forEach((c) => c.classList.toggle("active", c === chip));
      applyLibraryFilter();
    });
  });

  function applyLibraryFilter() {
    const active = document.querySelector(".library-filters .chip.active");
    const filter = active ? active.dataset.filter : "all";
    document.querySelectorAll(".prompt-list-item").forEach((li) => {
      const show = filter === "all" || (filter === "favorite" && li.dataset.favorite === "true");
      li.style.display = show ? "" : "none";
    });
  }

  savePromptForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("newPromptTitle").value.trim();
    const category = document.getElementById("newPromptCategory").value;
    const content = playgroundInput.value.trim() || chatInput?.value.trim();

    if (!title || !content) {
      alert("Write a prompt in the editor and give it a title before saving.");
      return;
    }

    const res = await fetch("/api/prompts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content, category }),
    });
    const prompt = await res.json();
    if (!res.ok) {
      alert(prompt.error || "Could not save prompt.");
      return;
    }

    const li = document.createElement("li");
    li.className = "prompt-list-item";
    li.dataset.id = prompt.id;
    li.dataset.favorite = "false";
    li.innerHTML = `
      <button class="prompt-list-main" data-action="use-prompt">
        <span class="prompt-title">${escapeHtml(prompt.title)}</span>
        <span class="prompt-category">${escapeHtml(prompt.category)}</span>
      </button>
      <button class="icon-btn fav-btn" data-action="toggle-favorite" aria-label="Toggle favorite">
        <svg viewBox="0 0 24 24" fill="none"><path d="M12 3l2.6 5.9 6.4.6-4.8 4.3 1.4 6.3L12 16.9 6.4 20.1l1.4-6.3-4.8-4.3 6.4-.6L12 3Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>
      </button>`;
    promptList.querySelector(".prompt-empty")?.remove();
    promptList.prepend(li);
    savePromptForm.reset();
  });

  renderHistory();
  refreshCostEstimate();
})();
