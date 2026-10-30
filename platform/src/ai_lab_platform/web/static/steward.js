/* Steward Desk: Chief of Staff Conversational Desk & Autonomous Companion */
(function () {
  "use strict";

  const GROUPS = [
    { label: "Memory", icon: "🧠", tools: ["vault_list", "vault_grep", "vault_read"] },
    { label: "Notes", icon: "📝", tools: ["files_list", "files_grep", "files_read"] },
    { label: "Reports", icon: "📊", tools: ["report_list", "report_read"] },
    { label: "Nexus", icon: "📚", tools: ["nexus_search"] },
    { label: "The web", icon: "🌐", tools: ["web_search"] },
    { label: "Schedules", icon: "⏰", tools: ["schedule_list"] },
    { label: "Presentations", icon: "📽️", tools: ["presentation_list", "presentation_read"] },
    { label: "Skills", icon: "⚡", tools: ["skill_list", "skill_read"] },
    { label: "Lab health", icon: "🛡️", tools: ["health_read"] },
  ];
  const RHYTHM = {
    "0 9 * * *": "Each morning",
    "0 * * * *": "Hourly",
    "*/15 * * * *": "Every 15 minutes",
  };

  const TEMPLATES = {
    morning: {
      title: "Morning Lab & Vault Briefing",
      intent: "Inspect memory vault for overnight notes, summarize recent reports, and check lab health status.",
      cron: "0 9 * * *",
      tools: ["vault_list", "vault_read", "report_list", "report_read", "health_read"],
    },
    research: {
      title: "AI Research & Paper Sentinel",
      intent: "Search arXiv and the web for recent LLM reasoning, distillation, and architecture breakthroughs.",
      cron: "0 9 * * *",
      tools: ["web_search", "nexus_search"],
    },
    health: {
      title: "Lab Health & Host Watch",
      intent: "Verify health endpoints, active cron schedules, and report any system degradation or errors.",
      cron: "0 * * * *",
      tools: ["health_read", "schedule_list"],
    },
    journal: {
      title: "Vault & Personal Notes Sync",
      intent: "Check personal files and vault memory for new documents and maintain thread continuity.",
      cron: "*/15 * * * *",
      tools: ["vault_list", "vault_read", "files_list", "files_read"],
    },
  };

  // DOM Elements
  const form = document.getElementById("goal-form");
  const titleInput = document.getElementById("goal-title");
  const intentInput = document.getElementById("goal-intent");
  const preset = document.getElementById("wake-preset");
  const cronInput = document.getElementById("wake-cron");
  const cronRow = document.getElementById("cron-row");
  const rhythm = document.getElementById("rhythm");
  const seeTools = document.getElementById("see-tools");
  const goalsEl = document.getElementById("goals");
  const activityEl = document.getElementById("activity");
  const statusEl = document.getElementById("status");
  const saveBtn = document.getElementById("save-goal");
  const presence = document.getElementById("presence");
  const presenceDetail = document.getElementById("presence-detail");
  const presenceMark = document.getElementById("presence-mark");
  const tabActiveCount = document.getElementById("steward-tab-count");

  // Chat Elements
  const chatMessagesEl = document.getElementById("steward-chat-messages");
  const emptyChatEl = document.getElementById("steward-empty-chat");
  const chatInput = document.getElementById("steward-chat-input");
  const sendBtn = document.getElementById("steward-send-btn");
  const newChatBtn = document.getElementById("steward-new-chat-btn");
  const thinkingBanner = document.getElementById("steward-thinking");
  const btnToggleComposer = document.getElementById("btn-toggle-composer");
  const btnRefreshFeed = document.getElementById("btn-refresh-feed");

  // State
  let newestId = "";
  let activeTab = "chat";
  let activeConvId = null;
  let isThinking = false;
  let pollInterval = null;

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text || "";
  }

  function headers() {
    const extra = window.aiLabHeaders ? window.aiLabHeaders() : {};
    return Object.assign({ "Content-Type": "application/json" }, extra);
  }

  function readJson(response) {
    return response.text().then(function (text) {
      let body = {};
      if (text) {
        try {
          body = JSON.parse(text);
        } catch (err) {
          body = { detail: text };
        }
      }
      if (!response.ok) {
        const detail = body && body.detail;
        const message = typeof detail === "string" && detail
          ? detail
          : (response.status === 401 ? "Sign in from the header, then try again." : "The lab could not do that.");
        const error = new Error(message);
        error.status = response.status;
        throw error;
      }
      return body;
    });
  }

  function clear(node) {
    while (node && node.firstChild) node.removeChild(node.firstChild);
  }

  function add(parent, tag, text, className) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text == null ? "" : String(text);
    parent.appendChild(el);
    return el;
  }

  function appendFormattedText(container, text) {
    if (!text) return;
    const lines = String(text).split("\n");
    let currentList = null;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (/^[-*]\s+/.test(line)) {
        if (!currentList) {
          currentList = document.createElement("ul");
          container.appendChild(currentList);
        }
        const li = document.createElement("li");
        li.textContent = line.replace(/^[-*]\s+/, "");
        currentList.appendChild(li);
      } else {
        currentList = null;
        if (line) {
          const p = document.createElement("p");
          p.textContent = line;
          container.appendChild(p);
        }
      }
    }
  }

  function checkedTools() {
    if (!seeTools) return [];
    return Array.prototype.map.call(
      seeTools.querySelectorAll("input[type=checkbox]:checked"),
      function (box) { return box.value; }
    );
  }

  function chip(label, toolNames, isMcp, icon) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = isMcp ? "chip mcp-chip" : "chip";
    button.setAttribute("aria-pressed", "true");
    button.textContent = (icon ? icon + " " : "") + label;
    toolNames.forEach(function (name) {
      const box = document.createElement("input");
      box.type = "checkbox";
      box.value = name;
      box.checked = true;
      box.hidden = true;
      box.tabIndex = -1;
      item.appendChild(box);
    });
    button.addEventListener("click", function () {
      const on = button.getAttribute("aria-pressed") !== "true";
      button.setAttribute("aria-pressed", on ? "true" : "false");
      Array.prototype.forEach.call(item.querySelectorAll("input"), function (box) {
        box.checked = on;
      });
    });
    item.appendChild(button);
    return item;
  }

  function renderTools(names) {
    if (!seeTools) return;
    clear(seeTools);
    const known = {};
    GROUPS.forEach(function (group) {
      const present = group.tools.filter(function (name) { return names.indexOf(name) !== -1; });
      if (!present.length) return;
      present.forEach(function (name) { known[name] = group.label; });
      seeTools.appendChild(chip(group.label, present, false, group.icon));
    });
    names.forEach(function (name) {
      if (!known[name]) {
        let label = name;
        let isMcp = false;
        if (name.indexOf("mcp/") === 0) {
          isMcp = true;
          const parts = name.split("/");
          const sName = parts[1] || "";
          const tName = parts.slice(2).join("/");
          label = tName + " (" + sName + ")";
        }
        seeTools.appendChild(chip(label, [name], isMcp, isMcp ? "🔌" : "⚙️"));
      }
    });
  }

  function sourceLabels(tools) {
    const labels = [];
    const seen = {};
    (tools || []).forEach(function (name) {
      let label = name;
      GROUPS.forEach(function (group) {
        if (group.tools.indexOf(name) !== -1) label = group.label;
      });
      if (name.indexOf("mcp/") === 0) {
        const parts = name.split("/");
        label = "MCP " + (parts[1] || "service");
      }
      if (!seen[label]) {
        seen[label] = true;
        labels.push(label);
      }
    });
    if (!labels.length) return "";
    if (labels.length >= 5) return "the lab & MCPs";
    if (labels.length === 1) return labels[0];
    if (labels.length === 2) return labels[0] + " and " + labels[1];
    return labels.slice(0, -1).join(", ") + ", and " + labels[labels.length - 1];
  }

  function rhythmWords(cron) {
    return RHYTHM[cron] || cron || "On its schedule";
  }

  function friendlyWhen(iso) {
    if (!iso) return "";
    const when = new Date(iso);
    if (Number.isNaN(when.getTime())) return String(iso);
    const diffMs = Date.now() - when.getTime();
    if (diffMs >= 0) {
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return diffMins + "m ago";
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return diffHours + "h ago";
    }
    return when.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function stateWord(status) {
    if (status === "active") return { text: "Watching", className: "state awake" };
    if (status === "paused") return { text: "Paused", className: "state rest" };
    if (status === "done") return { text: "Closed", className: "state closed" };
    if (status === "queued") return { text: "Waiting", className: "state" };
    if (status === "completed") return { text: "Brought back", className: "state awake" };
    if (status === "failed" || status === "error") return { text: "Stopped", className: "state bad" };
    if (status === "skipped") return { text: "Nothing to read", className: "state" };
    return { text: status || "", className: "state" };
  }

  function renderPresence(goals) {
    const active = goals.filter(function (goal) { return goal.status === "active"; }).length;
    const paused = goals.filter(function (goal) { return goal.status === "paused"; }).length;
    const statActive = document.getElementById("stat-active-count");
    if (statActive) statActive.textContent = String(active);
    if (tabActiveCount) tabActiveCount.textContent = String(active);

    if (!presence || !presenceDetail || !presenceMark) return;

    if (!goals.length) {
      presence.textContent = "Quiet";
      presenceDetail.textContent = "Nothing is in its care. Talk with Steward or hand off a responsibility below.";
      presenceMark.dataset.state = "quiet";
      return;
    }
    if (active) {
      presence.textContent = active === 1 ? "Watching 1 responsibility" : "Watching " + active + " responsibilities";
      presenceDetail.textContent = "It wakes autonomously on the mini and reports back findings over Ollama on the Studio.";
      presenceMark.dataset.state = "awake";
      return;
    }
    if (paused) {
      presence.textContent = "Resting";
      presenceDetail.textContent = "Every open goal is paused. Wake one when you want it looking again.";
      presenceMark.dataset.state = "paused";
      return;
    }
    presence.textContent = "At rest";
    presenceDetail.textContent = "The closed goals stay here as a permanent audit record.";
    presenceMark.dataset.state = "quiet";
  }

  function textButton(label, onClick, className) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className ? "text-btn " + className : "text-btn";
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
  }

  // --- TAB NAVIGATION ---
  function switchTab(targetTab) {
    activeTab = targetTab;
    const tabs = document.querySelectorAll(".steward-tab");
    tabs.forEach(function (tab) {
      const isTarget = tab.getAttribute("data-tab") === targetTab;
      tab.classList.toggle("active", isTarget);
      tab.setAttribute("aria-selected", isTarget ? "true" : "false");
    });

    const views = {
      chat: document.getElementById("steward-view-chat"),
      watches: document.getElementById("steward-view-watches"),
      feed: document.getElementById("steward-view-feed"),
    };

    Object.keys(views).forEach(function (key) {
      const el = views[key];
      if (el) {
        if (key === targetTab) {
          el.hidden = false;
          el.classList.add("active");
        } else {
          el.hidden = true;
          el.classList.remove("active");
        }
      }
    });

    if (targetTab === "chat" && chatInput) {
      chatInput.focus();
    }
  }

  // --- GOALS / STANDING WATCHES ---
  function renderGoals(goals) {
    if (!goalsEl) return;
    clear(goalsEl);
    renderPresence(goals);
    if (!goals.length) {
      add(goalsEl, "p", "The first responsibility will sit here. Choose a quick template above or create one below.", "empty");
      return;
    }
    goals.slice().reverse().forEach(function (goal) {
      const card = document.createElement("article");
      card.className = "goal" + (goal.id === newestId ? " arrived" : "");
      const top = document.createElement("div");
      top.className = "goal-top";
      add(top, "h3", goal.title || "Untitled");
      const word = stateWord(goal.status);
      add(top, "span", word.text, word.className);
      card.appendChild(top);
      if (goal.intent) add(card, "p", goal.intent, "intent");
      const when = rhythmWords(goal.wake_cron);
      const due = goal.last_due_at ? "Last looked " + friendlyWhen(goal.last_due_at) : "Not looked yet";
      add(card, "p", "⏰ " + when + " · " + due, "meta");
      const sources = sourceLabels(goal.see_tools);
      if (sources) add(card, "p", "🔍 Reading: " + sources, "meta");

      const actions = document.createElement("div");
      actions.className = "goal-actions";
      if (goal.status === "active") {
        actions.appendChild(textButton("⚡ Wake now", function () { act(goal.id, "wake"); }, "btn-wake"));
        actions.appendChild(textButton("⏸️ Pause", function () { act(goal.id, "pause"); }));
      }
      if (goal.status === "paused") {
        actions.appendChild(textButton("▶️ Wake again", function () { act(goal.id, "resume"); }, "btn-wake"));
      }
      if (goal.status !== "done") {
        const confirm = document.createElement("div");
        confirm.className = "confirm";
        confirm.hidden = true;
        add(confirm, "p", "This stops scheduled wakes. The record stays.");
        confirm.appendChild(textButton("Stop waking", function () { act(goal.id, "close"); }, "danger"));
        confirm.appendChild(textButton("Keep watching", function () {
          confirm.hidden = true;
          delete actions.dataset.mode;
        }));
        const close = textButton("✕ Close", function () {
          actions.dataset.mode = "confirm";
          confirm.hidden = false;
        });
        actions.appendChild(close);
        actions.appendChild(confirm);
      }
      if (actions.childNodes.length) card.appendChild(actions);
      goalsEl.appendChild(card);
    });
    newestId = "";
  }

  // --- INTELLIGENCE FEED / ACTIVITY ---
  function renderActivity(entries) {
    if (!activityEl) return;
    clear(activityEl);
    if (!entries || !entries.length) {
      add(activityEl, "p", "Notes from autonomous wakes will show up here.", "empty");
      return;
    }

    entries.forEach(function (entry) {
      const card = document.createElement("article");
      card.className = "feed-card";

      const top = document.createElement("div");
      top.className = "feed-card-top";

      const title = add(top, "div", entry.goal_title || "Autonomous Wake", "feed-card-title");
      const word = stateWord(entry.status);
      add(top, "span", word.text, word.className);
      card.appendChild(top);

      const time = document.createElement("div");
      time.className = "feed-card-time";
      time.textContent = "Woke " + friendlyWhen(entry.at);
      card.appendChild(time);

      const body = document.createElement("div");
      body.className = "feed-card-body";
      appendFormattedText(body, entry.note || "Quiet check completed — no immediate operator action needed.");
      card.appendChild(body);

      const footer = document.createElement("div");
      footer.className = "feed-card-footer";
      const sources = sourceLabels(entry.see_tools);
      if (sources) {
        add(footer, "span", "🔍 Consulted: " + sources);
      } else {
        add(footer, "span", "");
      }

      if (entry.goal_id) {
        const rewakeBtn = textButton("⚡ Wake Now", function () {
          act(entry.goal_id, "wake");
        }, "btn-wake");
        footer.appendChild(rewakeBtn);
      }

      card.appendChild(footer);
      activityEl.appendChild(card);
    });
  }

  // --- CONVERSATION / CHIEF OF STAFF DESK ---
  function loadConversations() {
    return fetch("/v1/conversations?limit=40", { headers: headers() })
      .then(readJson)
      .then(function (res) {
        const list = res.conversations || [];
        const personal = list.filter(function (c) { return c.agent === "personal"; });
        if (personal.length > 0) {
          activeConvId = personal[0].id;
          return loadMessages(activeConvId);
        } else {
          activeConvId = null;
          renderMessages([]);
        }
      })
      .catch(function () {
        // Silently tolerate if no conversations yet
      });
  }

  function loadMessages(convId) {
    if (!convId) return;
    return fetch("/v1/conversations/" + encodeURIComponent(convId) + "/messages", { headers: headers() })
      .then(readJson)
      .then(function (res) {
        renderMessages(res.messages || []);
      })
      .catch(function () {
        renderMessages([]);
      });
  }

  function renderMessages(messages) {
    if (!chatMessagesEl) return;
    clear(chatMessagesEl);

    if (!messages || !messages.length) {
      if (emptyChatEl) {
        chatMessagesEl.appendChild(emptyChatEl);
      }
      return;
    }

    messages.forEach(function (msg) {
      const row = document.createElement("div");
      row.className = "steward-msg " + (msg.role === "user" ? "user" : "assistant");

      if (msg.role !== "user") {
        const avatar = document.createElement("img");
        avatar.className = "steward-msg-avatar";
        avatar.src = "/static/ai-lab-orb.jpg";
        avatar.alt = "Steward";
        row.appendChild(avatar);
      }

      const bubbleWrap = document.createElement("div");
      const bubble = document.createElement("div");
      bubble.className = "steward-msg-bubble";
      appendFormattedText(bubble, msg.content);
      bubbleWrap.appendChild(bubble);

      if (msg.created_at) {
        const time = document.createElement("div");
        time.className = "steward-msg-time";
        time.textContent = friendlyWhen(msg.created_at);
        bubbleWrap.appendChild(time);
      }

      row.appendChild(bubbleWrap);
      chatMessagesEl.appendChild(row);
    });

    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
  }

  function sendMessage(text) {
    const content = (text || (chatInput ? chatInput.value : "")).trim();
    if (!content || isThinking) return;

    if (chatInput) {
      chatInput.value = "";
      chatInput.style.height = "auto";
    }

    isThinking = true;
    if (thinkingBanner) thinkingBanner.hidden = false;
    if (presenceMark) presenceMark.dataset.state = "awake";

    // Optimistic user message
    const tempMsg = {
      role: "user",
      content: content,
      created_at: new Date().toISOString(),
    };
    const currentMessages = Array.prototype.map.call(
      chatMessagesEl.querySelectorAll(".steward-msg"),
      function (el) {
        return {
          role: el.classList.contains("user") ? "user" : "assistant",
          content: el.querySelector(".steward-msg-bubble").innerText,
        };
      }
    );
    currentMessages.push(tempMsg);
    renderMessages(currentMessages);

    // Ensure conversation exists
    const convPromise = activeConvId
      ? Promise.resolve(activeConvId)
      : fetch("/v1/conversations", {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({
            agent: "personal",
            title: content.slice(0, 48),
          }),
        })
          .then(readJson)
          .then(function (c) {
            activeConvId = c.id;
            return activeConvId;
          });

    convPromise
      .then(function (cid) {
        // 1. Post user turn
        return fetch("/v1/conversations/" + encodeURIComponent(cid) + "/messages", {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({
            content: content,
            role: "user",
            reply: false,
          }),
        }).then(function () { return cid; });
      })
      .then(function (cid) {
        // 2. Post agent run
        return fetch("/v1/conversations/" + encodeURIComponent(cid) + "/runs", {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({
            agent: "personal",
            objective: content,
            execute: true,
            backend: "ollama",
            model: "auto",
            billing_class: "local",
            max_steps: 24,
          }),
        }).then(function () { return cid; });
      })
      .then(function (cid) {
        // 3. Drain via tick if available
        fetch("/v1/agent-runs/worker/tick", { method: "POST", headers: headers() }).catch(function () {});

        // 4. Poll for assistant message
        let attempts = 0;
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(function () {
          attempts++;
          fetch("/v1/conversations/" + encodeURIComponent(cid) + "/messages", { headers: headers() })
            .then(readJson)
            .then(function (res) {
              const msgs = res.messages || [];
              const last = msgs[msgs.length - 1];
              if (last && last.role === "assistant" && msgs.length > currentMessages.length) {
                clearInterval(pollInterval);
                pollInterval = null;
                isThinking = false;
                if (thinkingBanner) thinkingBanner.hidden = true;
                renderMessages(msgs);
                load(); // Refresh watches in case Steward created one
              } else if (attempts >= 20) {
                clearInterval(pollInterval);
                pollInterval = null;
                isThinking = false;
                if (thinkingBanner) thinkingBanner.hidden = true;
                renderMessages(msgs);
              }
            })
            .catch(function () {
              if (attempts >= 20) {
                clearInterval(pollInterval);
                pollInterval = null;
                isThinking = false;
                if (thinkingBanner) thinkingBanner.hidden = true;
              }
            });
        }, 1100);
      })
      .catch(function (err) {
        isThinking = false;
        if (thinkingBanner) thinkingBanner.hidden = true;
        setStatus(err.message || "Failed to complete conversation turn.");
      });
  }

  // --- TEMPLATE CLICK HANDLER ---
  function applyTemplate(key) {
    const tpl = TEMPLATES[key];
    if (!tpl) return;

    if (titleInput) titleInput.value = tpl.title;
    if (intentInput) intentInput.value = tpl.intent;

    if (preset) preset.value = tpl.cron;
    if (cronInput) cronInput.value = tpl.cron;
    if (cronRow) cronRow.hidden = tpl.cron !== "custom";

    if (rhythm) {
      Array.prototype.forEach.call(rhythm.querySelectorAll("button"), function (b) {
        const match = b.getAttribute("data-cron") === tpl.cron;
        b.setAttribute("aria-pressed", match ? "true" : "false");
      });
    }

    if (seeTools) {
      Array.prototype.forEach.call(seeTools.querySelectorAll("li"), function (item) {
        const btn = item.querySelector("button");
        const inputs = item.querySelectorAll("input");
        let hasMatch = false;
        Array.prototype.forEach.call(inputs, function (inp) {
          if (tpl.tools.indexOf(inp.value) !== -1) hasMatch = true;
        });
        if (btn) btn.setAttribute("aria-pressed", hasMatch ? "true" : "false");
        Array.prototype.forEach.call(inputs, function (inp) {
          inp.checked = hasMatch;
        });
      });
    }

    switchTab("watches");
    if (form) {
      form.scrollIntoView({ behavior: "smooth", block: "start" });
      if (titleInput) titleInput.focus();
    }
  }

  // --- ACTIONS ---
  function load() {
    return fetch("/v1/steward/access", { headers: headers() })
      .then(readJson)
      .then(function (access) {
        const see = access.classes && access.classes.see ? access.classes.see : [];
        if (seeTools && !seeTools.childNodes.length) renderTools(see);
        return Promise.all([
          fetch("/v1/steward/goals", { headers: headers() }).then(readJson),
          fetch("/v1/steward/activity", { headers: headers() }).then(readJson),
        ]);
      })
      .then(function (pair) {
        renderGoals(pair[0].goals || []);
        renderActivity(pair[1].activity || []);
        return loadConversations();
      })
      .catch(function (err) {
        setStatus(err.message || "The lab could not load the Steward.");
      });
  }

  function act(id, name) {
    setStatus(name === "wake" ? "⚡ Triggering on-demand wake run..." : "");
    fetch("/v1/steward/goals/" + encodeURIComponent(id) + "/" + name, {
      method: "POST",
      headers: headers(),
    })
      .then(readJson)
      .then(function () {
        if (name === "pause") setStatus("Paused. It will sit until you wake it.");
        else if (name === "resume") setStatus("Watching again.");
        else if (name === "wake") setStatus("⚡ Woken now. Findings recorded in Intelligence Feed.");
        else setStatus("Closed. The record stays.");
        return load();
      })
      .catch(function (err) {
        setStatus(err.message || "The lab could not update that goal.");
      });
  }

  // --- LISTENERS ---
  // Tab Switcher
  document.addEventListener("click", function (event) {
    const tabBtn = event.target.closest(".steward-tab");
    if (tabBtn) {
      const target = tabBtn.getAttribute("data-tab");
      if (target) switchTab(target);
      return;
    }

    const tplBtn = event.target.closest(".template-card");
    if (tplBtn) {
      const key = tplBtn.getAttribute("data-template");
      if (key) applyTemplate(key);
      return;
    }

    const promptBtn = event.target.closest(".steward-prompt-card");
    if (promptBtn) {
      const prompt = promptBtn.getAttribute("data-prompt");
      if (prompt) sendMessage(prompt);
      return;
    }
  });

  if (rhythm) {
    rhythm.addEventListener("click", function (event) {
      const button = event.target.closest("button[data-cron]");
      if (!button) return;
      const value = button.getAttribute("data-cron");
      if (preset) preset.value = value;
      Array.prototype.forEach.call(rhythm.querySelectorAll("button"), function (item) {
        item.setAttribute("aria-pressed", item === button ? "true" : "false");
      });
      if (value === "custom") {
        if (cronRow) cronRow.hidden = false;
        if (cronInput) cronInput.focus();
        return;
      }
      if (cronInput) cronInput.value = value;
      if (cronRow) cronRow.hidden = true;
    });
  }

  if (preset) {
    preset.addEventListener("change", function () {
      if (preset.value !== "custom" && cronInput) cronInput.value = preset.value;
    });
  }

  if (btnToggleComposer) {
    btnToggleComposer.addEventListener("click", function () {
      if (form) {
        form.scrollIntoView({ behavior: "smooth", block: "start" });
        if (titleInput) titleInput.focus();
      }
    });
  }

  if (btnRefreshFeed) {
    btnRefreshFeed.addEventListener("click", function () {
      load();
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener("click", function () {
      sendMessage();
    });
  }

  if (chatInput) {
    chatInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    chatInput.addEventListener("input", function () {
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + "px";
    });
  }

  if (newChatBtn) {
    newChatBtn.addEventListener("click", function () {
      fetch("/v1/conversations", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          agent: "personal",
          title: "Steward Companion",
        }),
      })
        .then(readJson)
        .then(function (c) {
          activeConvId = c.id;
          renderMessages([]);
          if (chatInput) chatInput.focus();
        })
        .catch(function (err) {
          setStatus(err.message || "Could not start new chat.");
        });
    });
  }

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const tools = checkedTools();
      if (!tools.length) {
        setStatus("Leave it at least one thing to read.");
        return;
      }
      if (saveBtn) saveBtn.disabled = true;
      setStatus("");
      fetch("/v1/steward/goals", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          title: titleInput ? titleInput.value : "",
          intent: intentInput ? intentInput.value : "",
          wake_cron: cronInput ? cronInput.value : "0 9 * * *",
          see_tools: tools,
        }),
      })
        .then(readJson)
        .then(function (goal) {
          newestId = goal.id || "";
          if (titleInput) titleInput.value = "";
          if (intentInput) intentInput.value = "";
          setStatus("It has this in its care now.");
          if (titleInput) titleInput.focus();
          return load();
        })
        .catch(function (err) {
          setStatus(err.message || "The lab could not save that goal.");
        })
        .then(function () {
          if (saveBtn) saveBtn.disabled = false;
        });
    });
  }

  document.addEventListener("ai-lab-auth-ready", load);
  if (form || chatMessagesEl) load();
  window.loadSteward = load;
  window.mountSteward = load;
  window.switchStewardTab = switchTab;
})();
