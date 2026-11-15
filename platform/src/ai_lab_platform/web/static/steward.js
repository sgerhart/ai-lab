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
      const line = lines[i].trim();
      if (!line) {
        currentList = null;
        continue;
      }
      if (/^#{1,3}\s+/.test(line)) {
        currentList = null;
        const heading = document.createElement("h4");
        heading.className = "feed-section-heading";
        heading.textContent = line.replace(/^#{1,3}\s+/, "");
        container.appendChild(heading);
      } else if (/^[-*]\s+/.test(line)) {
        if (!currentList) {
          currentList = document.createElement("ul");
          currentList.className = "feed-bullet-list";
          container.appendChild(currentList);
        }
        const li = document.createElement("li");
        li.textContent = line.replace(/^[-*]\s+/, "");
        currentList.appendChild(li);
      } else {
        currentList = null;
        const p = document.createElement("p");
        p.textContent = line;
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
    });
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

    isThinking = true;
    if (thinkingBanner) thinkingBanner.hidden = false;
    if (cockpitThinking) cockpitThinking.hidden = false;
    if (presenceMark) presenceMark.dataset.state = "awake";

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
                if (cockpitThinking) cockpitThinking.hidden = true;
                renderMessages(msgs);
                load(); // Refresh watches in case Steward created one
              } else if (attempts >= 20) {
                clearInterval(pollInterval);
                pollInterval = null;
                isThinking = false;
                if (thinkingBanner) thinkingBanner.hidden = true;
                if (cockpitThinking) cockpitThinking.hidden = true;
                renderMessages(msgs);
              }
            })
            .catch(function () {
              if (attempts >= 20) {
                clearInterval(pollInterval);
                pollInterval = null;
                isThinking = false;
                if (thinkingBanner) thinkingBanner.hidden = true;
                if (cockpitThinking) cockpitThinking.hidden = true;
              }
            });
        }, 1100);
      })
      .catch(function (err) {
        isThinking = false;
        if (thinkingBanner) thinkingBanner.hidden = true;
        if (cockpitThinking) cockpitThinking.hidden = true;
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

  function loadMailboxRadar() {
    fetch("/v1/gmail/stats", { headers: headers() })
      .then(readJson)
      .then(function (res) {
        if (res && res.ok && res.stats) {
          const s = res.stats;
          const inboxEl = document.getElementById("cockpit-stat-inbox");
          const unreadEl = document.getElementById("cockpit-stat-unread");
          const totalEl = document.getElementById("cockpit-stat-total");
          const threadsEl = document.getElementById("cockpit-stat-threads");
          const badgeEl = document.getElementById("radar-email-badge");
          const meterEl = document.getElementById("radar-meter-inbox");

          if (badgeEl && s.email) badgeEl.textContent = s.email;
          if (totalEl && s.messages_total) totalEl.textContent = Number(s.messages_total).toLocaleString();
          if (threadsEl && s.threads_total) threadsEl.textContent = (s.threads_total / 1000).toFixed(1) + "k threads";

          const inboxLabel = (s.labels && s.labels.INBOX) || {};
          if (inboxEl && inboxLabel.messages_total) {
            inboxEl.textContent = Number(inboxLabel.messages_total).toLocaleString();
          }
          if (unreadEl && inboxLabel.messages_unread) {
            unreadEl.textContent = Number(inboxLabel.messages_unread).toLocaleString() + " unread";
          }
          if (meterEl && s.messages_total && inboxLabel.messages_total) {
            const pct = Math.min(100, Math.round((inboxLabel.messages_total / s.messages_total) * 100));
            meterEl.style.width = pct + "%";
          }
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
      add(meta, "span", "Cron: " + (g.wake_cron || "0 8 * * *"));
      add(meta, "span", g.last_due_at ? "Last: " + friendlyWhen(g.last_due_at) : "Pending Wake");
      item.appendChild(meta);

      list.appendChild(item);
    });
  }

  // --- ACTIONS ---
  function load() {
    loadAutonomyMode();
    loadMailboxRadar();
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

  function renderSweepReceipt(card, count, snippets) {
    if (!card) return;
    card.classList.remove("executed");
    card.classList.add("sweep-success");

    const oldReceipt = card.querySelector(".sweep-audit-receipt");
    if (oldReceipt) oldReceipt.remove();

    const receipt = document.createElement("div");
    receipt.className = "sweep-audit-receipt";

    const head = document.createElement("div");
    head.className = "sweep-audit-header";
    head.textContent = "✓ Trashed " + count + " Stale Threads (Audit Receipt)";
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
    footText.textContent = "Google Trash · 30-day recovery";
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

      fetch("/v1/gmail/sweep", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query: "category:promotions older_than:2d", limit: 50 }),
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
            "**Action:** Moved **" + count + " promotional threads** (`category:promotions older_than:2d`) to Gmail Trash.\n" +
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

  if (btnAuthorizeAll) {
    btnAuthorizeAll.addEventListener("click", function () {
      btnAuthorizeAll.textContent = "⚡ Authorizing All...";
      btnAuthorizeAll.disabled = true;

      // 1. Execute the 50 promo sweep
      fetch("/v1/gmail/sweep", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query: "category:promotions older_than:2d", limit: 50 }),
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

  document.addEventListener("ai-lab-auth-ready", load);
  if (form || chatMessagesEl) load();
  window.loadSteward = load;
  window.mountSteward = load;
  window.switchStewardTab = switchTab;
})();
