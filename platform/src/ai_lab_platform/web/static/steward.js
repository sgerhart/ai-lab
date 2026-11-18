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
    { label: "Gmail", icon: "✉️", tools: ["gmail_mailbox_stats", "gmail_batch_trash", "gmail_batch_archive", "gmail_list_unread", "gmail_search", "gmail_read_thread", "gmail_create_draft", "gmail_trash_thread", "gmail_trash_message", "gmail_archive_thread"] },
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
      tools: ["vault_list", "vault_read", "report_list", "report_read", "health_read", "gmail_list_unread"],
    },
    inbox: {
      title: "Morning Inbox & VIP Sentinel",
      intent: "Check Gmail inbox for unread priority emails, summarize key requests, and highlight items needing response.",
      cron: "0 9 * * *",
      tools: ["gmail_list_unread", "gmail_read_thread", "vault_write"],
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
    study: {
      title: "Nexus Technical Study Sentinel",
      intent: "Search Knowledge Nexus shelf for key chapters on cybersecurity, network architecture, and AI engineering.",
      cron: "0 9 * * *",
      tools: ["nexus_search", "vault_read"],
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

  // Sentinel Fleet Elements
  const goalsActiveEl = document.getElementById("goals-active");
  const goalsArchivedEl = document.getElementById("goals-archived");
  const sectionArchived = document.getElementById("section-archived-sentinels");
  const archivedCount = document.getElementById("archived-count");
  const fleetActiveCounter = document.getElementById("fleet-active-counter");
  const activeSentinelsBadge = document.getElementById("active-sentinels-badge");
  const composerDrawer = document.getElementById("sentinel-composer-drawer");
  const btnCloseComposer = document.getElementById("btn-close-composer");
  const btnCancelComposer = document.getElementById("btn-cancel-composer");

  // Chat Elements
  const chatMessagesEl = document.getElementById("steward-chat-messages");
  const emptyChatEl = document.getElementById("steward-empty-chat");
  const chatInput = document.getElementById("steward-chat-input");
  const sendBtn = document.getElementById("steward-send-btn");
  const newChatBtn = document.getElementById("steward-new-chat-btn");
  const thinkingBanner = document.getElementById("steward-thinking");
  const btnToggleComposer = document.getElementById("btn-toggle-composer");
  const btnRefreshFeed = document.getElementById("btn-refresh-feed");

  // Flagship Cockpit Elements
  const cockpitMessagesEl = document.getElementById("cockpit-chat-messages");
  const cockpitInput = document.getElementById("cockpit-chat-input");
  const cockpitSendBtn = document.getElementById("cockpit-send-btn");
  const cockpitThinking = document.getElementById("cockpit-thinking");
  const cockpitThinkingText = document.getElementById("cockpit-thinking-text");
  const cockpitThinkingSub = document.getElementById("cockpit-thinking-sub");
  const btnCockpitWake = document.getElementById("btn-cockpit-wake");
  const btnAuthorizeAll = document.getElementById("btn-authorize-all");

  // State
  let newestId = "";
  let activeTab = "cockpit";
  let activeConvId = null;
  let isThinking = false;
  let pollInterval = null;
  let cachedGoals = [];

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
      const rawLine = lines[i].trim();
      if (!rawLine) {
        currentList = null;
        continue;
      }

      // Check if line represents an in-chat guardrail promotion pill
      const cleanLine = rawLine.replace(/^[-*]\s+/, "").replace(/^`+|`+$/g, "").trim();
      const pillMatch = cleanLine.match(/^\[?\+\s*(Auto-Archive|Direct Trash|Whitelist):\s*([^\]]+)\]?$/i);
      if (pillMatch) {
        currentList = null;
        const actionType = pillMatch[1].toLowerCase();
        const itemName = pillMatch[2].trim();

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "guardrail-promote-pill";
        const icon = actionType.indexOf("archive") !== -1 ? "📁 " : (actionType.indexOf("trash") !== -1 ? "🗑️ " : "🛡️ ");
        btn.textContent = icon + "+ " + pillMatch[1] + ": " + itemName;

        btn.addEventListener("click", function () {
          btn.disabled = true;
          btn.textContent = "⏳ Adding...";
          const apiAction = actionType.indexOf("archive") !== -1
            ? "add_auto_archive"
            : (actionType.indexOf("trash") !== -1 ? "add_direct_trash" : "add_whitelist");

          fetch("/v1/steward/policy", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({ action: apiAction, item: itemName }),
          })
            .then(readJson)
            .then(function () {
              btn.textContent = "✓ Added: " + itemName;
              btn.classList.add("pill-saved");
              loadPolicy();
              setStatus("✓ Added " + itemName + " to Executive Guardrails.");
            })
            .catch(function (err) {
              btn.disabled = false;
              btn.textContent = "Failed (Retry)";
              setStatus(err.message || "Failed to update guardrails.");
            });
        });

        container.appendChild(btn);
        continue;
      }

      if (/^#{1,3}\s+/.test(rawLine)) {
        currentList = null;
        const heading = document.createElement("h4");
        heading.className = "feed-section-heading";
        heading.textContent = rawLine.replace(/^#{1,3}\s+/, "");
        container.appendChild(heading);
      } else if (/^[-*]\s+/.test(rawLine)) {
        if (!currentList) {
          currentList = document.createElement("ul");
          currentList.className = "feed-bullet-list";
          container.appendChild(currentList);
        }
        const li = document.createElement("li");
        li.textContent = rawLine.replace(/^[-*]\s+/, "");
        currentList.appendChild(li);
      } else {
        currentList = null;
        const p = document.createElement("p");
        p.textContent = rawLine;
        container.appendChild(p);
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

  function getSentinelIcon(title, tools) {
    const text = ((title || "") + " " + (tools || []).join(" ")).toLowerCase();
    if (text.indexOf("inbox") !== -1 || text.indexOf("mail") !== -1 || text.indexOf("gmail") !== -1) return "📬";
    if (text.indexOf("health") !== -1 || text.indexOf("ci") !== -1 || text.indexOf("host") !== -1) return "🛡️";
    if (text.indexOf("research") !== -1 || text.indexOf("paper") !== -1 || text.indexOf("arxiv") !== -1) return "🔬";
    if (text.indexOf("study") !== -1 || text.indexOf("nexus") !== -1 || text.indexOf("book") !== -1) return "📚";
    if (text.indexOf("vault") !== -1 || text.indexOf("journal") !== -1 || text.indexOf("memory") !== -1) return "🧠";
    return "🛰️";
  }

  function getCapabilityBadges(tools) {
    const badges = [];
    const seen = {};
    (tools || []).forEach(function (name) {
      let icon = "⚙️";
      let label = name;
      GROUPS.forEach(function (group) {
        if (group.tools.indexOf(name) !== -1) {
          icon = group.icon;
          label = group.label;
        }
      });
      if (name.indexOf("mcp/") === 0) {
        const parts = name.split("/");
        icon = "🔌";
        label = "MCP " + (parts[1] || "service");
      }
      if (!seen[label]) {
        seen[label] = true;
        badges.push({ icon: icon, label: label });
      }
    });
    return badges;
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
      cockpit: document.getElementById("steward-view-cockpit"),
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

    if (targetTab === "cockpit" && cockpitInput) {
      cockpitInput.focus();
    } else if (targetTab === "chat" && chatInput) {
      chatInput.focus();
    }
  }

  // --- GOALS / STANDING WATCHES ---
  function renderGoals(goals) {
    cachedGoals = goals || [];
    renderCockpitSentinels(cachedGoals);
    renderPresence(goals);
    if (goalsEl) clear(goalsEl);

    const activeList = cachedGoals.filter(function (g) { return g.status === "active" || g.status === "paused"; });
    const closedList = cachedGoals.filter(function (g) { return g.status === "done" || g.status === "closed"; });

    const activeCount = cachedGoals.filter(function (g) { return g.status === "active"; }).length;
    if (fleetActiveCounter) {
      fleetActiveCounter.textContent = activeCount === 1 ? "1 Active Sentinel" : activeCount + " Active Sentinels";
    }
    if (activeSentinelsBadge) {
      activeSentinelsBadge.textContent = activeCount === 1 ? "1 Active" : activeCount + " Active";
    }
    if (archivedCount) {
      archivedCount.textContent = String(closedList.length);
    }
    if (sectionArchived) {
      sectionArchived.hidden = closedList.length === 0;
    }

    if (goalsActiveEl) {
      clear(goalsActiveEl);
      if (!activeList.length) {
        const empty = document.createElement("div");
        empty.className = "sentinel-empty-state";
        add(empty, "div", "🛰️", "empty-icon");
        add(empty, "h4", "No active sentinels in flight");
        add(empty, "p", "Steward is resting. Select a quick blueprint above or click '＋ Deploy New Sentinel' to keep watch.");
        goalsActiveEl.appendChild(empty);
      } else {
        activeList.slice().reverse().forEach(function (goal) {
          const card = document.createElement("article");
          card.className = "sentinel-fleet-card" + (goal.id === newestId ? " arrived" : "");

          // Header
          const header = document.createElement("div");
          header.className = "fleet-card-header";

          const titleGroup = document.createElement("div");
          titleGroup.className = "fleet-card-title-group";
          const iconSpan = document.createElement("span");
          iconSpan.className = "fleet-card-icon";
          iconSpan.textContent = getSentinelIcon(goal.title, goal.see_tools);
          titleGroup.appendChild(iconSpan);

          const titleText = document.createElement("div");
          add(titleText, "h3", goal.title || "Untitled Sentinel", "fleet-card-title");
          const when = rhythmWords(goal.wake_cron);
          add(titleText, "span", "⏰ " + when + " (" + (goal.wake_cron || "cron") + ")", "fleet-card-cron");
          titleGroup.appendChild(titleText);
          header.appendChild(titleGroup);

          const statusBadge = document.createElement("div");
          const word = stateWord(goal.status);
          statusBadge.className = "fleet-status-badge " + (goal.status === "active" ? "badge-active" : "badge-paused");
          if (goal.status === "active") {
            const pulse = document.createElement("span");
            pulse.className = "beacon-dot";
            statusBadge.appendChild(pulse);
          }
          const badgeText = document.createElement("span");
          badgeText.textContent = word.text.toUpperCase();
          statusBadge.appendChild(badgeText);
          header.appendChild(statusBadge);
          card.appendChild(header);

          // Intent / Mission
          if (goal.intent) {
            add(card, "p", goal.intent, "fleet-card-intent");
          }

          // Capabilities badges
          const capBadges = getCapabilityBadges(goal.see_tools);
          if (capBadges.length) {
            const capsWrap = document.createElement("div");
            capsWrap.className = "fleet-card-caps";
            const capLabel = document.createElement("span");
            capLabel.className = "caps-label";
            capLabel.textContent = "Capabilities:";
            capsWrap.appendChild(capLabel);
            capBadges.forEach(function (b) {
              const tag = document.createElement("span");
              tag.className = "cap-tag";
              tag.textContent = b.icon + " " + b.label;
              capsWrap.appendChild(tag);
            });
            card.appendChild(capsWrap);
          }

          // Telemetry
          const telemetry = document.createElement("div");
          telemetry.className = "fleet-card-telemetry";
          const due = goal.last_due_at ? "Last wake " + friendlyWhen(goal.last_due_at) + " · Ran on mini" : "Waiting for next wake cycle";
          const teleItem = document.createElement("div");
          teleItem.className = "telemetry-item";
          add(teleItem, "span", due, "telemetry-text");
          telemetry.appendChild(teleItem);
          card.appendChild(telemetry);

          // Action Buttons
          const actions = document.createElement("div");
          actions.className = "fleet-card-actions";
          if (goal.status === "active") {
            const wakeBtn = textButton("⚡ Wake Now", function () {
              wakeBtn.textContent = "⚡ Waking...";
              wakeBtn.disabled = true;
              act(goal.id, "wake");
            }, "btn-fleet-wake");
            actions.appendChild(wakeBtn);

            actions.appendChild(textButton("⏸️ Pause", function () {
              act(goal.id, "pause");
            }, "btn-fleet-pause"));
          }
          if (goal.status === "paused") {
            actions.appendChild(textButton("▶️ Resume Wake", function () {
              act(goal.id, "resume");
            }, "btn-fleet-wake"));
          }
          if (goal.status !== "done") {
            const configBtn = textButton("⚙️ Configure", function () {
              openGoalConfigModal(goal);
            }, "btn-fleet-configure");
            actions.appendChild(configBtn);

            const confirm = document.createElement("div");
            confirm.className = "confirm";
            confirm.hidden = true;
            add(confirm, "p", "Stop scheduled background wakes? Record will be archived.");
            confirm.appendChild(textButton("Stop waking", function () { act(goal.id, "close"); }, "danger"));
            confirm.appendChild(textButton("Keep watching", function () {
              confirm.hidden = true;
              delete actions.dataset.mode;
            }));
            const close = textButton("✕ Retire", function () {
              actions.dataset.mode = "confirm";
              confirm.hidden = false;
            }, "btn-fleet-close");
            actions.appendChild(close);
            actions.appendChild(confirm);
          }
          card.appendChild(actions);
          goalsActiveEl.appendChild(card);
        });
      }
    }

    // Render Archived
    if (goalsArchivedEl) {
      clear(goalsArchivedEl);
      closedList.slice().reverse().forEach(function (goal) {
        const item = document.createElement("div");
        item.className = "archived-sentinel-row";

        const left = document.createElement("div");
        left.className = "archived-row-left";
        const iconSpan = document.createElement("span");
        iconSpan.className = "archived-row-icon";
        iconSpan.textContent = getSentinelIcon(goal.title, goal.see_tools);
        left.appendChild(iconSpan);

        const info = document.createElement("div");
        add(info, "strong", goal.title || "Untitled Sentinel", "archived-row-title");
        const when = rhythmWords(goal.wake_cron);
        const last = goal.last_due_at ? " · Last run " + friendlyWhen(goal.last_due_at) : "";
        add(info, "span", when + last, "archived-row-meta");
        left.appendChild(info);
        item.appendChild(left);

        const right = document.createElement("div");
        right.className = "archived-row-right";
        const badge = document.createElement("span");
        badge.className = "archived-badge";
        badge.textContent = "ARCHIVED";
        right.appendChild(badge);

        const reactivateBtn = textButton("▶ Reactivate", function () {
          act(goal.id, "resume");
        }, "btn-reactivate");
        right.appendChild(reactivateBtn);
        item.appendChild(right);

        goalsArchivedEl.appendChild(item);
      });
    }

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

      // Top row
      const top = document.createElement("div");
      top.className = "feed-card-top";

      const titleGroup = document.createElement("div");
      titleGroup.className = "feed-card-title-group";
      const iconSpan = document.createElement("span");
      iconSpan.className = "feed-card-icon";
      iconSpan.textContent = getSentinelIcon(entry.goal_title, entry.see_tools);
      titleGroup.appendChild(iconSpan);

      add(titleGroup, "div", entry.goal_title || "Autonomous Sentinel Wake", "feed-card-title");
      top.appendChild(titleGroup);

      const metaGroup = document.createElement("div");
      metaGroup.className = "feed-card-meta-group";

      const word = stateWord(entry.status);
      add(metaGroup, "span", word.text.toUpperCase(), "feed-status-badge " + (entry.status === "completed" ? "badge-completed" : "badge-neutral"));

      const time = document.createElement("span");
      time.className = "feed-card-time";
      time.textContent = friendlyWhen(entry.at);
      metaGroup.appendChild(time);
      top.appendChild(metaGroup);

      card.appendChild(top);

      // Body
      const body = document.createElement("div");
      body.className = "feed-card-body";
      appendFormattedText(body, entry.note || "Quiet check completed — no immediate operator action needed.");
      card.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.className = "feed-card-footer";

      const capBadges = getCapabilityBadges(entry.see_tools);
      if (capBadges.length) {
        const capsWrap = document.createElement("div");
        capsWrap.className = "feed-caps";
        capBadges.forEach(function (b) {
          const tag = document.createElement("span");
          tag.className = "cap-tag";
          tag.textContent = b.icon + " " + b.label;
          capsWrap.appendChild(tag);
        });
        footer.appendChild(capsWrap);
      } else {
        footer.appendChild(document.createElement("span"));
      }

      const actions = document.createElement("div");
      actions.className = "feed-actions";

      // If email congestion was noted, offer 1-click sweep right inside the report card
      const noteLower = (entry.note || "").toLowerCase();
      if (noteLower.indexOf("unread") !== -1 || noteLower.indexOf("promot") !== -1 || noteLower.indexOf("retail") !== -1 || noteLower.indexOf("congest") !== -1) {
        const sweepBtn = textButton("🧹 Sweep 50 Promos", function () {
          sweepBtn.textContent = "⚡ Sweeping...";
          sweepBtn.disabled = true;
          fetch("/v1/gmail/sweep", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({ query: "category:promotions older_than:2d", limit: 50 }),
          })
            .then(readJson)
            .then(function (res) {
              const count = res.trashed_count != null ? res.trashed_count : 50;
              sweepBtn.textContent = "✓ Swept " + count;
              if (res.stats) updateMailboxUI(res.stats);
              setStatus("🧹 Swept " + count + " promotional threads to Trash.");
            })
            .catch(function () {
              sweepBtn.textContent = "Failed";
            });
        }, "btn-feed-action");
        actions.appendChild(sweepBtn);
      }

      if (entry.goal_id) {
        const rewakeBtn = textButton("⚡ Re-wake Sentinel", function () {
          rewakeBtn.textContent = "⚡ Waking...";
          rewakeBtn.disabled = true;
          act(entry.goal_id, "wake");
        }, "btn-feed-rewake");
        actions.appendChild(rewakeBtn);
      }

      footer.appendChild(actions);
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
        // Check for in-flight run to resume live tracking
        fetch("/v1/conversations/" + encodeURIComponent(convId) + "/runs", { headers: headers() })
          .then(readJson)
          .then(function (rRes) {
            const runs = rRes.runs || [];
            const activeRun = runs.find(function (r) { return r.status === "running" || r.status === "queued"; });
            if (activeRun) {
              const startMs = activeRun.created_at ? new Date(activeRun.created_at).getTime() : Date.now();
              startThinkingPoll(convId, startMs, (res.messages || []).length + 1);
            }
          })
          .catch(function () {});
      })
      .catch(function () {
        renderMessages([]);
      });
  }

  function logReceiptToDialogue(receiptText) {
    if (!activeConvId) {
      loadConversations().then(function () {
        if (activeConvId) {
          postReceiptMessage(activeConvId, receiptText);
        }
      });
      return;
    }
    postReceiptMessage(activeConvId, receiptText);
  }

  function postReceiptMessage(cid, text) {
    fetch("/v1/conversations/" + encodeURIComponent(cid) + "/messages", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ role: "assistant", content: text }),
    })
      .then(readJson)
      .then(function () {
        loadMessages(cid);
      })
      .catch(function () {});
  }

  function renderMessages(messages) {
    const targets = [chatMessagesEl, cockpitMessagesEl].filter(Boolean);
    if (!targets.length) return;

    targets.forEach(function (container) {
      clear(container);

      if (!messages || !messages.length) {
        if (container === chatMessagesEl && emptyChatEl) {
          container.appendChild(emptyChatEl);
        } else if (container === cockpitMessagesEl) {
          add(container, "p", "No messages yet. Send a directive or authorize an action bundle above.", "empty");
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
        container.appendChild(row);
      });

      container.scrollTop = container.scrollHeight;
      setTimeout(function () {
        container.scrollTop = container.scrollHeight;
      }, 100);
    });
  }

  function setThinkingState(on, customMain, customSub) {
    isThinking = on;
    if (thinkingBanner) thinkingBanner.hidden = !on;
    if (cockpitThinking) cockpitThinking.hidden = !on;
    if (presenceMark) presenceMark.dataset.state = on ? "awake" : "idle";

    const textEls = [
      document.getElementById("cockpit-thinking-text"),
      document.getElementById("steward-thinking-text"),
    ].filter(Boolean);
    const subEls = [
      document.getElementById("cockpit-thinking-sub"),
      document.getElementById("steward-thinking-sub"),
    ].filter(Boolean);
    if (on) {
      if (customMain) textEls.forEach(function (el) { el.textContent = customMain; });
      if (customSub) subEls.forEach(function (el) { el.textContent = customSub; });
    }
  }

  function stopThinkingPoll() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
    setThinkingState(false);
  }

  function startThinkingPoll(cid, startTime, expectedMinMsgs) {
    if (pollInterval) clearInterval(pollInterval);
    const startMs = startTime || Date.now();
    setThinkingState(true, "⚡ Waking Qwen 35B on mac-mini...", "0s elapsed · mac-mini private loop");

    let attempts = 0;
    pollInterval = setInterval(function () {
      attempts++;
      const elapsed = Math.max(1, Math.round((Date.now() - startMs) / 1000));
      const subEls = [
        document.getElementById("cockpit-thinking-sub"),
        document.getElementById("steward-thinking-sub"),
      ].filter(Boolean);
      subEls.forEach(function (el) { el.textContent = elapsed + "s elapsed · mac-mini private loop"; });

      // 1. Check runs status & tool traces
      fetch("/v1/conversations/" + encodeURIComponent(cid) + "/runs", { headers: headers() })
        .then(readJson)
        .then(function (res) {
          const runs = res.runs || [];
          const activeRun = runs.find(function (r) { return r.status === "running" || r.status === "queued"; }) || runs[runs.length - 1];
          const textEls = [
            document.getElementById("cockpit-thinking-text"),
            document.getElementById("steward-thinking-text"),
          ].filter(Boolean);

          let isDone = false;
          if (activeRun) {
            if (activeRun.status === "completed" || activeRun.status === "failed") {
              isDone = true;
            } else {
              const traces = activeRun.traces || [];
              let statusMsg = "";
              if (!traces.length) {
                statusMsg = "⚡ Initializing Qwen 35B on mac-mini...";
              } else {
                const lastTrace = traces[traces.length - 1];
                if (lastTrace.kind === "tool_result") {
                  const t = lastTrace.tool || "";
                  if (t === "gmail_search") {
                    statusMsg = "🔍 Searched mailbox · Analyzing results...";
                  } else if (t.indexOf("trash") !== -1) {
                    statusMsg = "🧹 Trashed batch of noise · Checking next batch...";
                  } else if (t.indexOf("archive") !== -1) {
                    statusMsg = "📁 Archived batch · Reviewing remaining...";
                  } else if (t === "gmail_mailbox_stats") {
                    statusMsg = "📊 Checked mailbox totals · Synthesizing...";
                  } else {
                    statusMsg = "⚡ Step " + traces.length + ": Finished " + t + "...";
                  }
                } else if (lastTrace.kind === "model_call") {
                  const txt = lastTrace.text || "";
                  if (txt.indexOf("gmail_search") !== -1) {
                    statusMsg = "🔍 Tool: Searching mailbox...";
                  } else if (txt.indexOf("batch_trash") !== -1) {
                    statusMsg = "🧹 Tool: Trashing matching threads...";
                  } else if (txt.indexOf("batch_archive") !== -1) {
                    statusMsg = "📁 Tool: Archiving matching threads...";
                  } else {
                    statusMsg = "⚡ Evaluating step " + (traces.length + 1) + "...";
                  }
                }
              }
              if (statusMsg) textEls.forEach(function (el) { el.textContent = statusMsg; });
            }
          }

          // 2. Poll messages if run is done or periodically
          if (isDone || attempts % 2 === 0) {
            fetch("/v1/conversations/" + encodeURIComponent(cid) + "/messages", { headers: headers() })
              .then(readJson)
              .then(function (mRes) {
                const msgs = mRes.messages || [];
                const last = msgs[msgs.length - 1];
                const hasAssistant = last && last.role === "assistant";
                const countSatisfied = expectedMinMsgs ? msgs.length >= expectedMinMsgs : hasAssistant;

                if ((hasAssistant && (isDone || countSatisfied)) || attempts >= 180) {
                  stopThinkingPoll();
                  renderMessages(msgs);
                  load();
                  loadMailboxStats();
                  loadActivity();
                }
              })
              .catch(function () {});
          }
        })
        .catch(function () {
          if (attempts >= 180) stopThinkingPoll();
        });
    }, 2000);
  }

  function sendMessage(text) {
    let content = (text || "").trim();
    if (!content) {
      if (activeTab === "cockpit" && cockpitInput) {
        content = cockpitInput.value.trim();
      } else if (chatInput) {
        content = chatInput.value.trim();
      }
    }
    if (!content || isThinking) return;

    if (chatInput) {
      chatInput.value = "";
      chatInput.style.height = "auto";
    }
    if (cockpitInput) {
      cockpitInput.value = "";
      cockpitInput.style.height = "auto";
    }

    setThinkingState(true, "⚡ Waking Qwen 35B on mac-mini...", "0s elapsed · mac-mini private loop");

    // Optimistic user message
    const tempMsg = {
      role: "user",
      content: content,
      created_at: new Date().toISOString(),
    };
    const activeContainer = (activeTab === "cockpit" && cockpitMessagesEl) ? cockpitMessagesEl : chatMessagesEl;
    const currentMessages = Array.prototype.map.call(
      activeContainer ? activeContainer.querySelectorAll(".steward-msg") : [],
      function (el) {
        const bubble = el.querySelector(".steward-msg-bubble");
        return {
          role: el.classList.contains("user") ? "user" : "assistant",
          content: bubble ? bubble.innerText : "",
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

        // 4. Poll live status & traces
        startThinkingPoll(cid, Date.now(), currentMessages.length + 1);
      })
      .catch(function (err) {
        stopThinkingPoll();
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
    if (composerDrawer) {
      composerDrawer.hidden = false;
      composerDrawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else if (form) {
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (titleInput) titleInput.focus();
  }

  // --- AUTONOMY & RADAR HELPERS ---
  function updateAutonomyUI(mode) {
    const buttons = document.querySelectorAll(".autonomy-btn");
    buttons.forEach(function (btn) {
      const match = btn.getAttribute("data-mode") === mode;
      btn.classList.toggle("active", match);
    });
  }

  function loadAutonomyMode() {
    fetch("/v1/steward/autonomy", { headers: headers() })
      .then(readJson)
      .then(function (res) {
        if (res && res.mode) {
          updateAutonomyUI(res.mode);
        }
      })
      .catch(function () {});
  }

  function setAutonomyMode(mode) {
    updateAutonomyUI(mode);
    fetch("/v1/steward/autonomy", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ mode: mode }),
    })
      .then(readJson)
      .then(function (res) {
        if (res && res.mode) {
          updateAutonomyUI(res.mode);
        }
      })
      .catch(function () {});
  }

  function updateMailboxUI(s) {
    if (!s) return;
    const inboxEl = document.getElementById("cockpit-stat-inbox");
    const unreadEl = document.getElementById("cockpit-stat-unread");
    const totalEl = document.getElementById("cockpit-stat-total");
    const threadsEl = document.getElementById("cockpit-stat-threads");
    const badgeEl = document.getElementById("radar-email-badge");
    const meterEl = document.getElementById("radar-meter-inbox");
    const burndownEl = document.getElementById("cockpit-burndown-target");

    if (badgeEl && s.email) badgeEl.textContent = s.email;
    if (totalEl && s.messages_total) totalEl.textContent = Number(s.messages_total).toLocaleString();
    if (threadsEl && s.threads_total) threadsEl.textContent = (s.threads_total / 1000).toFixed(1) + "k threads";

    const inboxLabel = (s.labels && s.labels.INBOX) || {};
    if (inboxEl && inboxLabel.messages_total != null) {
      inboxEl.textContent = Number(inboxLabel.messages_total).toLocaleString();
    }
    if (unreadEl && inboxLabel.messages_unread != null) {
      unreadEl.textContent = Number(inboxLabel.messages_unread).toLocaleString();
      if (burndownEl) {
        burndownEl.textContent = Number(inboxLabel.messages_unread).toLocaleString() + " → 500 Target";
      }
    }
    if (meterEl && s.messages_total && inboxLabel.messages_total) {
      const pct = Math.min(100, Math.round((inboxLabel.messages_total / s.messages_total) * 100));
      meterEl.style.width = pct + "%";
    }
  }

  function loadMailboxStats() {
    return loadMailboxRadar();
  }

  function loadMailboxRadar() {
    return fetch("/v1/gmail/stats", { headers: headers() })
      .then(readJson)
      .then(function (res) {
        if (res && res.ok && res.stats) {
          updateMailboxUI(res.stats);
        }
      })
      .catch(function () {});
  }

  function renderCockpitSentinels(goals) {
    const list = document.getElementById("cockpit-sentinel-list");
    if (!list) return;
    clear(list);
    const active = (goals || []).filter(function (g) { return g.status === "active"; });
    if (!active.length) {
      add(list, "p", "No active standing sentinels. Create one in Standing Watches.", "empty");
      return;
    }
    active.forEach(function (g) {
      const item = document.createElement("div");
      item.className = "cockpit-sentinel-item";

      const top = document.createElement("div");
      top.className = "sentinel-item-top";
      const name = add(top, "span", "", "sentinel-name");
      const dot = document.createElement("span");
      dot.className = "dot dot-emerald";
      name.appendChild(dot);
      name.appendChild(document.createTextNode(" " + (g.title || "Standing Sentinel")));
      add(top, "span", "ACTIVE", "sentinel-badge-active");
      item.appendChild(top);

      if (g.intent) {
        add(item, "p", g.intent, "sentinel-desc");
      }

      const meta = document.createElement("div");
      meta.className = "sentinel-meta";
      add(meta, "span", "🕒 " + (g.wake_cron || "0 8 * * *"));
      add(meta, "span", "⚡ " + (g.last_due_at ? "Last: " + friendlyWhen(g.last_due_at) : "Pending Wake"));
      item.appendChild(meta);

      const actions = document.createElement("div");
      actions.className = "sentinel-item-actions";
      const cfgBtn = add(actions, "button", "⚙️ Configure Watch", "btn-sentinel-edit");
      cfgBtn.type = "button";
      cfgBtn.addEventListener("click", function () {
        openGoalConfigModal(g);
      });
      const wakeBtn = add(actions, "button", "⚡ Wake Now", "btn-text-action");
      wakeBtn.type = "button";
      wakeBtn.addEventListener("click", function () {
        wakeBtn.textContent = "⚡ Waking...";
        wakeBtn.disabled = true;
        act(g.id, "wake");
      });
      item.appendChild(actions);

      list.appendChild(item);
    });
  }

  let currentPolicy = null;

  function loadEmailPolicy() {
    return fetch("/v1/steward/policy", { headers: headers() })
      .then(readJson)
      .then(function (policy) {
        currentPolicy = policy;
        renderExecutiveGuardrails(policy);
        renderGuardrailsDrawer(policy);
      })
      .catch(function () {});
  }

  function modifyPolicy(payload) {
    return fetch("/v1/steward/policy", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(payload),
    })
      .then(readJson)
      .then(function (policy) {
        currentPolicy = policy;
        renderExecutiveGuardrails(policy);
        renderGuardrailsDrawer(policy);
        const status = document.getElementById("guardrails-save-status");
        if (status) {
          status.textContent = "✓ Synced with Memory Vault";
          setTimeout(function () { status.textContent = ""; }, 3000);
        }
      })
      .catch(function (err) {
        alert("Could not update policy: " + err.message);
      });
  }

  function renderExecutiveGuardrails(policy) {
    const container = document.getElementById("cockpit-guardrails-container");
    if (!container) return;
    clear(container);
    if (!policy) return;

    // 1. Protected Whitelist
    const groupProtected = document.createElement("div");
    groupProtected.className = "guardrails-group";
    const headProt = document.createElement("div");
    headProt.className = "guardrails-group-header";
    add(headProt, "span", "🛡️ Protected Whitelist", "guardrails-group-title title-protected");
    add(headProt, "span", "(" + (policy.whitelist ? policy.whitelist.length : 0) + ")", "drawer-count-badge");
    groupProtected.appendChild(headProt);

    const pillsProt = document.createElement("div");
    pillsProt.className = "guardrail-pills";
    (policy.whitelist || []).forEach(function (item) {
      const pill = document.createElement("span");
      pill.className = "guardrail-pill pill-protected";
      pill.appendChild(document.createTextNode(item));
      const rem = add(pill, "button", "×", "pill-remove-btn");
      rem.type = "button";
      rem.title = "Remove from whitelist";
      rem.addEventListener("click", function (e) {
        e.stopPropagation();
        modifyPolicy({ action: "remove_whitelist", item: item });
      });
      pillsProt.appendChild(pill);
    });

    const addProtBtn = add(pillsProt, "button", "＋ Add", "btn-add-pill-inline");
    addProtBtn.type = "button";
    addProtBtn.title = "Add sender to whitelist";
    addProtBtn.addEventListener("click", function () {
      const val = prompt("Enter sender or domain to protect / whitelist (e.g. Delta, Netflix, NYTimes):");
      if (val && val.trim()) {
        modifyPolicy({ action: "add_whitelist", item: val.trim() });
      }
    });
    groupProtected.appendChild(pillsProt);
    container.appendChild(groupProtected);

    // 2. Auto-Archive Targets (Social & Newsletters)
    const groupArchive = document.createElement("div");
    groupArchive.className = "guardrails-group";
    const headArch = document.createElement("div");
    headArch.className = "guardrails-group-header";
    add(headArch, "span", "📁 Auto-Archive (Social & Alerts)", "guardrails-group-title title-archive");
    add(headArch, "span", "(" + (policy.auto_archive ? policy.auto_archive.length : 0) + ")", "drawer-count-badge");
    groupArchive.appendChild(headArch);

    const pillsArch = document.createElement("div");
    pillsArch.className = "guardrail-pills";
    (policy.auto_archive || []).forEach(function (item) {
      const pill = document.createElement("span");
      pill.className = "guardrail-pill pill-archive";
      pill.appendChild(document.createTextNode(item));
      const rem = add(pill, "button", "×", "pill-remove-btn");
      rem.type = "button";
      rem.title = "Remove from auto-archive";
      rem.addEventListener("click", function (e) {
        e.stopPropagation();
        modifyPolicy({ action: "remove_archive", item: item });
      });
      pillsArch.appendChild(pill);
    });

    const addArchBtn = add(pillsArch, "button", "＋ Add", "btn-add-pill-inline");
    addArchBtn.type = "button";
    addArchBtn.title = "Add platform or sender to auto-archive";
    addArchBtn.addEventListener("click", function () {
      const val = prompt("Enter social site or platform to auto-archive (e.g. Threads, Bluesky, LinkedIn):");
      if (val && val.trim()) {
        modifyPolicy({ action: "add_archive", item: val.trim() });
      }
    });
    groupArchive.appendChild(pillsArch);
    container.appendChild(groupArchive);

    // 3. Direct Trash & Unsubscribe
    const groupTrash = document.createElement("div");
    groupTrash.className = "guardrails-group";
    const headTrash = document.createElement("div");
    headTrash.className = "guardrails-group-header";
    add(headTrash, "span", "🗑️ Direct Trash & Unsubscribe", "guardrails-group-title title-trash");
    add(headTrash, "span", "(" + (policy.direct_trash ? policy.direct_trash.length : 0) + ")", "drawer-count-badge");
    groupTrash.appendChild(headTrash);

    const pillsTrash = document.createElement("div");
    pillsTrash.className = "guardrail-pills";
    (policy.direct_trash || []).forEach(function (item) {
      const pill = document.createElement("span");
      pill.className = "guardrail-pill pill-trash";
      pill.appendChild(document.createTextNode(item));
      const rem = add(pill, "button", "×", "pill-remove-btn");
      rem.type = "button";
      rem.title = "Remove from direct trash";
      rem.addEventListener("click", function (e) {
        e.stopPropagation();
        modifyPolicy({ action: "remove_trash", item: item });
      });
      pillsTrash.appendChild(pill);
    });

    const addTrashBtn = add(pillsTrash, "button", "＋ Add", "btn-add-pill-inline");
    addTrashBtn.type = "button";
    addTrashBtn.title = "Add sender to direct trash";
    addTrashBtn.addEventListener("click", function () {
      const val = prompt("Enter sender to direct trash / unsubscribe (e.g. Temu, Shein):");
      if (val && val.trim()) {
        modifyPolicy({ action: "add_trash", item: val.trim() });
      }
    });
    groupTrash.appendChild(pillsTrash);
    container.appendChild(groupTrash);

    // 3. Misaddressed S. Gerhart Patterns
    const groupOther = document.createElement("div");
    groupOther.className = "guardrails-group";
    const headOther = document.createElement("div");
    headOther.className = "guardrails-group-header";
    add(headOther, "span", "👤 Misaddressed ('Other Gerharts')", "guardrails-group-title title-other");
    add(headOther, "span", "(" + (policy.misaddressed_senders ? policy.misaddressed_senders.length : 0) + ")", "drawer-count-badge");
    groupOther.appendChild(headOther);

    const pillsOther = document.createElement("div");
    pillsOther.className = "guardrail-pills";
    (policy.misaddressed_senders || []).forEach(function (item) {
      const pill = document.createElement("span");
      pill.className = "guardrail-pill pill-other";
      pill.appendChild(document.createTextNode(item));
      const rem = add(pill, "button", "×", "pill-remove-btn");
      rem.type = "button";
      rem.title = "Remove misaddressed pattern";
      rem.addEventListener("click", function (e) {
        e.stopPropagation();
        modifyPolicy({ action: "remove_other", item: item });
      });
      pillsOther.appendChild(pill);
    });

    const addOtherBtn = add(pillsOther, "button", "＋ Add", "btn-add-pill-inline");
    addOtherBtn.type = "button";
    addOtherBtn.title = "Add misaddressed pattern";
    addOtherBtn.addEventListener("click", function () {
      const val = prompt("Enter misaddressed name or pattern (e.g. Shawn Gerhart Realtor):");
      if (val && val.trim()) {
        modifyPolicy({ action: "add_other", item: val.trim() });
      }
    });
    groupOther.appendChild(pillsOther);
    container.appendChild(groupOther);
  }

  function renderGuardrailsDrawer(policy) {
    if (!policy) return;
    const wlTags = document.getElementById("drawer-whitelist-tags");
    const archTags = document.getElementById("drawer-archive-tags");
    const dtTags = document.getElementById("drawer-trash-tags");
    const otherTags = document.getElementById("drawer-other-tags");
    const rawMd = document.getElementById("policy-raw-markdown");
    const wlBadge = document.getElementById("whitelist-count-badge");
    const archBadge = document.getElementById("archive-count-badge");
    const dtBadge = document.getElementById("trash-count-badge");
    const otherBadge = document.getElementById("other-count-badge");

    if (wlBadge) wlBadge.textContent = (policy.whitelist ? policy.whitelist.length : 0) + " items";
    if (archBadge) archBadge.textContent = (policy.auto_archive ? policy.auto_archive.length : 0) + " items";
    if (dtBadge) dtBadge.textContent = (policy.direct_trash ? policy.direct_trash.length : 0) + " items";
    if (otherBadge) otherBadge.textContent = (policy.misaddressed_senders ? policy.misaddressed_senders.length : 0) + " patterns";

    if (rawMd && (!rawMd.dataset.userEdited || rawMd.dataset.userEdited === "false")) {
      rawMd.value = policy.markdown || "";
    }

    if (wlTags) {
      clear(wlTags);
      (policy.whitelist || []).forEach(function (item) {
        const pill = document.createElement("span");
        pill.className = "guardrail-pill pill-protected";
        pill.appendChild(document.createTextNode(item));
        const rem = add(pill, "button", "×", "pill-remove-btn");
        rem.type = "button";
        rem.addEventListener("click", function () {
          modifyPolicy({ action: "remove_whitelist", item: item });
        });
        wlTags.appendChild(pill);
      });
    }

    if (archTags) {
      clear(archTags);
      (policy.auto_archive || []).forEach(function (item) {
        const pill = document.createElement("span");
        pill.className = "guardrail-pill pill-archive";
        pill.appendChild(document.createTextNode(item));
        const rem = add(pill, "button", "×", "pill-remove-btn");
        rem.type = "button";
        rem.addEventListener("click", function () {
          modifyPolicy({ action: "remove_archive", item: item });
        });
        archTags.appendChild(pill);
      });
    }

    if (dtTags) {
      clear(dtTags);
      (policy.direct_trash || []).forEach(function (item) {
        const pill = document.createElement("span");
        pill.className = "guardrail-pill pill-trash";
        pill.appendChild(document.createTextNode(item));
        const rem = add(pill, "button", "×", "pill-remove-btn");
        rem.type = "button";
        rem.addEventListener("click", function () {
          modifyPolicy({ action: "remove_trash", item: item });
        });
        dtTags.appendChild(pill);
      });
    }

    if (otherTags) {
      clear(otherTags);
      (policy.misaddressed_senders || []).forEach(function (item) {
        const pill = document.createElement("span");
        pill.className = "guardrail-pill pill-other";
        pill.appendChild(document.createTextNode(item));
        const rem = add(pill, "button", "×", "pill-remove-btn");
        rem.type = "button";
        rem.addEventListener("click", function () {
          modifyPolicy({ action: "remove_other", item: item });
        });
        otherTags.appendChild(pill);
      });
    }
  }

  function openGoalConfigModal(goal) {
    if (!goal) return;
    const modal = document.getElementById("sentinel-config-drawer-overlay");
    const idInput = document.getElementById("edit-goal-id");
    const titleInput = document.getElementById("edit-goal-title");
    const intentInput = document.getElementById("edit-goal-intent");
    const cronInput = document.getElementById("edit-wake-cron");
    const cronRow = document.getElementById("edit-cron-row");
    const rhythmSegs = document.querySelectorAll("#edit-rhythm .seg");
    const statusText = document.getElementById("edit-goal-status");

    if (idInput) idInput.value = goal.id;
    if (titleInput) titleInput.value = goal.title || "";
    if (intentInput) intentInput.value = goal.intent || "";
    if (statusText) statusText.textContent = "";

    const cron = goal.wake_cron || "0 8 * * *";
    if (cronInput) cronInput.value = cron;

    let matched = false;
    rhythmSegs.forEach(function (seg) {
      if (seg.dataset.cron === cron) {
        seg.classList.add("active");
        seg.setAttribute("aria-pressed", "true");
        matched = true;
      } else {
        seg.classList.remove("active");
        seg.setAttribute("aria-pressed", "false");
      }
    });

    if (!matched) {
      rhythmSegs.forEach(function (seg) {
        if (seg.dataset.cron === "custom") {
          seg.classList.add("active");
          seg.setAttribute("aria-pressed", "true");
        }
      });
      if (cronRow) cronRow.hidden = false;
    } else {
      if (cronRow) cronRow.hidden = true;
    }

    const toolsUl = document.getElementById("edit-see-tools");
    if (toolsUl) {
      clear(toolsUl);
      fetch("/v1/steward/access", { headers: headers() })
        .then(readJson)
        .then(function (access) {
          const see = (access.classes && access.classes.see) || [];
          see.forEach(function (toolName) {
            const li = document.createElement("li");
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "chip-tool" + ((goal.see_tools || []).includes(toolName) ? " active" : "");
            btn.textContent = toolName;
            btn.addEventListener("click", function () {
              btn.classList.toggle("active");
            });
            li.appendChild(btn);
            toolsUl.appendChild(li);
          });
        })
        .catch(function () {});
    }

    if (modal) modal.hidden = false;
  }

  // --- ACTIONS ---
  function load() {
    loadAutonomyMode();
    loadMailboxRadar();
    loadEmailPolicy();
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
      if (composerDrawer) {
        composerDrawer.hidden = !composerDrawer.hidden;
        if (!composerDrawer.hidden) {
          composerDrawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
          if (titleInput) titleInput.focus();
        }
      } else if (form) {
        form.scrollIntoView({ behavior: "smooth", block: "start" });
        if (titleInput) titleInput.focus();
      }
    });
  }

  if (btnCloseComposer) {
    btnCloseComposer.addEventListener("click", function () {
      if (composerDrawer) composerDrawer.hidden = true;
    });
  }

  if (btnCancelComposer) {
    btnCancelComposer.addEventListener("click", function () {
      if (composerDrawer) composerDrawer.hidden = true;
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
          if (composerDrawer) composerDrawer.hidden = true;
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

  // --- COCKPIT LISTENERS ---
  document.addEventListener("click", function (event) {
    // Autonomy buttons
    const autoBtn = event.target.closest(".autonomy-btn");
    if (autoBtn) {
      const mode = autoBtn.getAttribute("data-mode");
      if (mode) setAutonomyMode(mode);
      return;
    }
  });

  if (btnCockpitWake) {
    btnCockpitWake.addEventListener("click", function () {
      const active = (cachedGoals || []).find(function (g) { return g.status === "active"; });
      const targetId = active ? active.id : "9423ca82773245cebeba04508a1f4fcc";
      btnCockpitWake.textContent = "⚡ Waking...";
      btnCockpitWake.disabled = true;
      fetch("/v1/steward/goals/" + encodeURIComponent(targetId) + "/wake", {
        method: "POST",
        headers: headers(),
      })
        .then(readJson)
        .then(function () {
          setStatus("Sentinel wake triggered.");
          setTimeout(load, 3000);
        })
        .catch(function (err) {
          setStatus(err.message || "Could not trigger sentinel wake.");
        })
        .then(function () {
          btnCockpitWake.textContent = "⚡ Wake Now";
          btnCockpitWake.disabled = false;
        });
    });
  }

  // 1-Click Action Tray Execution
  const btnCi = document.getElementById("btn-action-ci");
  if (btnCi) {
    btnCi.addEventListener("click", function () {
      const card = document.getElementById("action-card-ci");
      if (card) card.classList.add("executed");
      btnCi.textContent = "✓ Dispatched";
      btnCi.disabled = true;
      sendMessage("Dispatch coding assistant to investigate the failed repo-validation run in a worktree");
    });
  }

  function renderSweepReceipt(card, count, snippets, action) {
    if (!card) return;
    card.classList.remove("executed");
    card.classList.add("sweep-success");

    const oldReceipt = card.querySelector(".sweep-audit-receipt");
    if (oldReceipt) oldReceipt.remove();

    const receipt = document.createElement("div");
    receipt.className = "sweep-audit-receipt";

    const head = document.createElement("div");
    head.className = "sweep-audit-header";
    if (action === "archive") {
      head.textContent = "✓ Archived " + count + " Threads to All Mail";
    } else {
      head.textContent = "✓ Trashed " + count + " Stale Threads (Audit Receipt)";
    }
    receipt.appendChild(head);

    if (snippets && snippets.length > 0) {
      const list = document.createElement("ul");
      list.className = "sweep-audit-list";
      snippets.slice(0, 5).forEach(function (snip) {
        const li = document.createElement("li");
        li.textContent = snip;
        list.appendChild(li);
      });
      receipt.appendChild(list);
    }

    const foot = document.createElement("div");
    foot.className = "sweep-audit-footer";
    const footText = document.createElement("span");
    footText.textContent = action === "archive" ? "All Mail Archive · Cleared from Inbox" : "Google Trash · 30-day recovery";
    const footTime = document.createElement("span");
    footTime.textContent = new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    foot.appendChild(footText);
    foot.appendChild(footTime);
    receipt.appendChild(foot);

    card.appendChild(receipt);
  }

  const btnRetail = document.getElementById("btn-action-retail");
  if (btnRetail) {
    btnRetail.addEventListener("click", function () {
      const card = document.getElementById("action-card-retail");
      btnRetail.textContent = "⚡ Sweeping 50...";
      btnRetail.disabled = true;

      const promoQuery = "category:promotions -humble -eero -experian -marriott older_than:2d";
      fetch("/v1/gmail/sweep", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query: promoQuery, limit: 50 }),
      })
        .then(readJson)
        .then(function (res) {
          const count = res.trashed_count != null ? res.trashed_count : 50;
          btnRetail.textContent = "⚡ Sweep Next 50";
          btnRetail.disabled = false;

          renderSweepReceipt(card, count, res.sample_snippets || []);

          if (res.stats) {
            updateMailboxUI(res.stats);
          } else {
            loadMailboxStats();
          }

          loadActivity();

          const snippetItems = (res.sample_snippets || []).map(function (s) { return "- " + s; }).join("\n");
          const receiptMsg = "### 🧹 Gmail Sweep Receipt\n" +
            "**Action:** Moved **" + count + " promotional threads** (`" + promoQuery + "`) to Gmail Trash.\n" +
            "**Whitelisted & Protected:** Humble Bundle, Eero, Experian, Marriott are preserved.\n" +
            "**Safety:** Recoverable for 30 days in Google Trash.\n" +
            (snippetItems ? "**Cleaned Samples:**\n" + snippetItems + "\n\n" : "\n") +
            "Backlog counter updated. Click **Sweep Next 50** on the card to continue cleaning.";
          logReceiptToDialogue(receiptMsg);

          setStatus("🧹 Swept " + count + " promotional threads older than 2 days to Trash.");
        })
        .catch(function (err) {
          btnRetail.textContent = "Sweep Failed (Retry)";
          btnRetail.disabled = false;
          setStatus(err.message || "Failed to execute promo sweep.");
        });
    });
  }

  const btnSchool = document.getElementById("btn-action-school");
  if (btnSchool) {
    btnSchool.addEventListener("click", function () {
      const card = document.getElementById("action-card-school");
      if (card) card.classList.add("executed");
      btnSchool.textContent = "✓ Requested Digest";
      btnSchool.disabled = true;
      sendMessage("Give me a 3-bullet summary of the school activity reports for Ella and Caroline");
    });
  }

  const btnSocial = document.getElementById("btn-action-social");
  if (btnSocial) {
    btnSocial.addEventListener("click", function () {
      const card = document.getElementById("action-card-social");
      btnSocial.textContent = "⚡ Archiving 100...";
      btnSocial.disabled = true;

      const socialQuery = "from:linkedin.com";
      fetch("/v1/gmail/sweep", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query: socialQuery, limit: 100, action: "archive" }),
      })
        .then(readJson)
        .then(function (res) {
          const count = res.archived_count != null ? res.archived_count : (res.trashed_count != null ? res.trashed_count : 100);
          btnSocial.textContent = "⚡ Archive Next 100";
          btnSocial.disabled = false;

          renderSweepReceipt(card, count, res.sample_snippets || [], "archive");

          if (res.stats) {
            updateMailboxUI(res.stats);
          } else {
            loadMailboxStats();
          }

          loadActivity();

          const snippetItems = (res.sample_snippets || []).map(function (s) { return "- " + s; }).join("\n");
          const receiptMsg = "### 📁 Gmail Archive Receipt\n" +
            "**Action:** Archived **" + count + " LinkedIn threads** (`" + socialQuery + "`) to All Mail.\n" +
            "**Destination:** Cleared from Primary Inbox, preserved in All Mail archive.\n" +
            (snippetItems ? "**Archived Samples:**\n" + snippetItems + "\n\n" : "\n") +
            "Backlog counter updated. Click **Archive Next 100** on the card to continue cleaning.";
          logReceiptToDialogue(receiptMsg);

          setStatus("📁 Archived " + count + " LinkedIn threads to All Mail.");
        })
        .catch(function (err) {
          btnSocial.textContent = "Archive Failed (Retry)";
          btnSocial.disabled = false;
          setStatus(err.message || "Failed to archive LinkedIn threads.");
        });
    });
  }

  const btnMisaddressed = document.getElementById("btn-action-misaddressed");
  if (btnMisaddressed) {
    btnMisaddressed.addEventListener("click", function () {
      const card = document.getElementById("action-card-misaddressed");
      btnMisaddressed.textContent = "⚡ Filtering...";
      btnMisaddressed.disabled = true;

      const misaddressedQuery = '"Shawn Gerhart" OR "realtor" OR "MLS" OR "mortgage closing"';
      fetch("/v1/gmail/sweep", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query: misaddressedQuery, limit: 100, action: "archive" }),
      })
        .then(readJson)
        .then(function (res) {
          const count = res.archived_count != null ? res.archived_count : (res.trashed_count != null ? res.trashed_count : 0);
          btnMisaddressed.textContent = "✓ Filter Next Batch";
          btnMisaddressed.disabled = false;

          renderSweepReceipt(card, count, res.sample_snippets || [], "archive");

          if (res.stats) {
            updateMailboxUI(res.stats);
          } else {
            loadMailboxStats();
          }

          loadActivity();

          const snippetItems = (res.sample_snippets || []).map(function (s) { return "- " + s; }).join("\n");
          const receiptMsg = "### 👤 Misaddressed Mail Triage Receipt\n" +
            "**Action:** Archived **" + count + " stray threads** (`" + misaddressedQuery + "`) to All Mail.\n" +
            "**Destination:** Cleared from Primary Inbox, safely archived in All Mail.\n" +
            (snippetItems ? "**Filtered Samples:**\n" + snippetItems + "\n\n" : "\n") +
            "Backlog counter updated. Click **Filter Next Batch** on the card to continue cleaning.";
          logReceiptToDialogue(receiptMsg);

          setStatus("👤 Archived " + count + " misaddressed threads to All Mail.");
        })
        .catch(function (err) {
          btnMisaddressed.textContent = "Filter Failed (Retry)";
          btnMisaddressed.disabled = false;
          setStatus(err.message || "Failed to filter misaddressed mail.");
        });
    });
  }

  if (btnAuthorizeAll) {
    btnAuthorizeAll.addEventListener("click", function () {
      btnAuthorizeAll.textContent = "⚡ Authorizing All...";
      btnAuthorizeAll.disabled = true;

      const promoQuery = "category:promotions -humble -eero -experian -marriott older_than:2d";
      // 1. Execute the 50 promo sweep
      fetch("/v1/gmail/sweep", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query: promoQuery, limit: 50 }),
      })
        .then(readJson)
        .then(function (res) {
          if (res.stats) updateMailboxUI(res.stats);
          else loadMailboxStats();
          const count = res.trashed_count != null ? res.trashed_count : 50;
          const retailCard = document.getElementById("action-card-retail");
          renderSweepReceipt(retailCard, count, res.sample_snippets || []);
          if (btnRetail) {
            btnRetail.textContent = "⚡ Sweep Next 50";
            btnRetail.disabled = false;
          }

          loadActivity();

          const ciCard = document.getElementById("action-card-ci");
          if (ciCard) ciCard.classList.add("executed");
          if (btnCi) btnCi.textContent = "✓ Dispatched";

          const schoolCard = document.getElementById("action-card-school");
          if (schoolCard) schoolCard.classList.add("executed");
          if (btnSchool) btnSchool.textContent = "✓ Requested";

          btnAuthorizeAll.textContent = "✓ All 3 Bundles Executed";
          btnAuthorizeAll.classList.add("authorized");

          sendMessage("Daily triage authorized: I swept " + count + " stale promotional threads to Trash. Please dispatch coding assistant to examine the failed repo-validation run, and summarize school reports for Ella and Caroline.");
        })
        .catch(function () {
          btnAuthorizeAll.disabled = false;
          sendMessage("Authorize all daily triage bundles: dispatch coding assistant for repo-validation, sweep 50 stale retail threads to Trash, and summarize school reports");
        });
    });
  }

  if (cockpitSendBtn) {
    cockpitSendBtn.addEventListener("click", function () {
      sendMessage();
    });
  }

  if (cockpitInput) {
    cockpitInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    cockpitInput.addEventListener("input", function () {
      cockpitInput.style.height = "auto";
      cockpitInput.style.height = Math.min(cockpitInput.scrollHeight, 140) + "px";
    });
  }

  // --- GUARDRAILS & SENTINEL MODALS EVENT LISTENERS ---
  const btnEditGuardrails = document.getElementById("btn-edit-guardrails");
  const guardrailsDrawerOverlay = document.getElementById("guardrails-drawer-overlay");
  const btnCloseGuardrailsDrawer = document.getElementById("btn-close-guardrails-drawer");
  const btnDoneGuardrails = document.getElementById("btn-done-guardrails");

  if (btnEditGuardrails && guardrailsDrawerOverlay) {
    btnEditGuardrails.addEventListener("click", function () {
      guardrailsDrawerOverlay.hidden = false;
      renderGuardrailsDrawer(currentPolicy);
    });
  }
  if (btnCloseGuardrailsDrawer && guardrailsDrawerOverlay) {
    btnCloseGuardrailsDrawer.addEventListener("click", function () {
      guardrailsDrawerOverlay.hidden = true;
    });
  }
  if (btnDoneGuardrails && guardrailsDrawerOverlay) {
    btnDoneGuardrails.addEventListener("click", function () {
      guardrailsDrawerOverlay.hidden = true;
    });
  }

  const btnAddWl = document.getElementById("btn-add-whitelist");
  if (btnAddWl) {
    btnAddWl.addEventListener("click", function () {
      const input = document.getElementById("input-new-whitelist");
      if (input && input.value.trim()) {
        modifyPolicy({ action: "add_whitelist", item: input.value.trim() });
        input.value = "";
      }
    });
  }

  const btnAddArch = document.getElementById("btn-add-archive");
  if (btnAddArch) {
    btnAddArch.addEventListener("click", function () {
      const input = document.getElementById("input-new-archive");
      if (input && input.value.trim()) {
        modifyPolicy({ action: "add_archive", item: input.value.trim() });
        input.value = "";
      }
    });
  }

  const btnAddDt = document.getElementById("btn-add-trash");
  if (btnAddDt) {
    btnAddDt.addEventListener("click", function () {
      const input = document.getElementById("input-new-trash");
      if (input && input.value.trim()) {
        modifyPolicy({ action: "add_trash", item: input.value.trim() });
        input.value = "";
      }
    });
  }

  const btnAddOther = document.getElementById("btn-add-other");
  if (btnAddOther) {
    btnAddOther.addEventListener("click", function () {
      const input = document.getElementById("input-new-other");
      if (input && input.value.trim()) {
        modifyPolicy({ action: "add_other", item: input.value.trim() });
        input.value = "";
      }
    });
  }

  const btnToggleRaw = document.getElementById("btn-toggle-raw-markdown");
  const rawWrap = document.getElementById("raw-markdown-wrap");
  if (btnToggleRaw && rawWrap) {
    btnToggleRaw.addEventListener("click", function () {
      rawWrap.hidden = !rawWrap.hidden;
    });
  }

  const btnSaveRaw = document.getElementById("btn-save-raw-markdown");
  if (btnSaveRaw) {
    btnSaveRaw.addEventListener("click", function () {
      const rawText = (document.getElementById("policy-raw-markdown").value || "").trim();
      modifyPolicy({ markdown: rawText });
    });
  }

  // Sentinel Config Drawer events
  const sentinelModal = document.getElementById("sentinel-config-drawer-overlay");
  const btnCloseSentConfig = document.getElementById("btn-close-sentinel-config");
  const btnCancelSentConfig = document.getElementById("btn-cancel-edit-goal");
  const editRhythmSegs = document.querySelectorAll("#edit-rhythm .seg");
  const editCronRow = document.getElementById("edit-cron-row");

  if (btnCloseSentConfig && sentinelModal) {
    btnCloseSentConfig.addEventListener("click", function () {
      sentinelModal.hidden = true;
    });
  }
  if (btnCancelSentConfig && sentinelModal) {
    btnCancelSentConfig.addEventListener("click", function () {
      sentinelModal.hidden = true;
    });
  }

  editRhythmSegs.forEach(function (seg) {
    seg.addEventListener("click", function () {
      editRhythmSegs.forEach(function (s) {
        s.classList.remove("active");
        s.setAttribute("aria-pressed", "false");
      });
      seg.classList.add("active");
      seg.setAttribute("aria-pressed", "true");
      if (seg.dataset.cron === "custom") {
        if (editCronRow) editCronRow.hidden = false;
      } else {
        if (editCronRow) editCronRow.hidden = true;
        const cronInput = document.getElementById("edit-wake-cron");
        if (cronInput) cronInput.value = seg.dataset.cron;
      }
    });
  });

  const sentinelEditForm = document.getElementById("sentinel-edit-form");
  if (sentinelEditForm) {
    sentinelEditForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const goalId = document.getElementById("edit-goal-id").value;
      const title = document.getElementById("edit-goal-title").value.trim();
      const intent = document.getElementById("edit-goal-intent").value.trim();

      let cron = "0 8 * * *";
      const activeSeg = document.querySelector("#edit-rhythm .seg.active");
      if (activeSeg) {
        if (activeSeg.dataset.cron === "custom") {
          cron = (document.getElementById("edit-wake-cron").value || "").trim();
        } else {
          cron = activeSeg.dataset.cron;
        }
      }

      const chosenTools = [];
      document.querySelectorAll("#edit-see-tools .chip-tool.active").forEach(function (el) {
        chosenTools.push(el.textContent.trim());
      });

      const statusText = document.getElementById("edit-goal-status");
      if (statusText) statusText.textContent = "Saving changes...";

      fetch("/v1/steward/goals/" + encodeURIComponent(goalId), {
        method: "PATCH",
        headers: headers(),
        body: JSON.stringify({
          title: title,
          intent: intent,
          wake_cron: cron,
          see_tools: chosenTools.length ? chosenTools : ["vault_read"],
        }),
      })
        .then(readJson)
        .then(function () {
          if (sentinelModal) sentinelModal.hidden = true;
          load();
        })
        .catch(function (err) {
          if (statusText) statusText.textContent = "Error: " + err.message;
        });
    });
  }

  document.addEventListener("ai-lab-auth-ready", load);
  if (form || chatMessagesEl) load();
  window.loadSteward = load;
  window.mountSteward = load;
  window.switchStewardTab = switchTab;
})();
