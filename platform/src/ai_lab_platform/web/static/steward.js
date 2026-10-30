/* Steward Desk: hand over a responsibility, then read what comes back. */
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
  let newestId = "";

  function setStatus(text) {
    statusEl.textContent = text || "";
  }

  function headers() {
    const extra = window.aiLabHeaders ? window.aiLabHeaders() : {};
    return Object.assign({ "Content-Type": "application/json" }, extra);
  }

  function readJson(response) {
    return response.text().then(function (text) {
      var body = {};
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

  function checkedTools() {
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

    if (!goals.length) {
      presence.textContent = "Quiet";
      presenceDetail.textContent = "Nothing is in its care. Leave a responsibility and it will keep watch.";
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

  function renderGoals(goals) {
    clear(goalsEl);
    renderPresence(goals);
    if (!goals.length) {
      add(goalsEl, "p", "The first responsibility will sit here. Leave one above to begin.", "empty");
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
        const close = textButton("✕ Close", function () {
          actions.dataset.mode = "confirm";
          confirm.hidden = false;
        });
        const confirm = document.createElement("div");
        confirm.className = "confirm";
        confirm.hidden = true;
        add(confirm, "p", "This stops scheduled wakes. The record stays.");
        confirm.appendChild(textButton("Stop waking", function () { act(goal.id, "close"); }, "danger"));
        confirm.appendChild(textButton("Keep watching", function () {
          confirm.hidden = true;
          delete actions.dataset.mode;
        }));
        actions.appendChild(close);
        actions.appendChild(confirm);
      }
      if (actions.childNodes.length) card.appendChild(actions);
      goalsEl.appendChild(card);
    });
    newestId = "";
  }

  function renderActivity(entries) {
    clear(activityEl);
    if (!entries || !entries.length) {
      add(activityEl, "p", "Notes from autonomous wakes will show up here.", "empty");
      return;
    }
    const list = document.createElement("ol");
    list.className = "timeline";
    entries.forEach(function (entry) {
      const item = document.createElement("li");
      const top = document.createElement("div");
      top.style.cssText = "display:flex;justify-content:space-between;align-items:center;gap:12px;";
      add(top, "h3", entry.goal_title || "A goal");
      const word = stateWord(entry.status);
      add(top, "span", word.text, word.className);
      item.appendChild(top);

      add(item, "p", "Woke " + friendlyWhen(entry.at), "meta");
      if (entry.note) {
        add(item, "div", entry.note, "note");
      } else {
        add(item, "div", "Quiet check completed — no immediate operator action needed.", "note");
      }
      const sources = sourceLabels(entry.see_tools);
      if (sources) add(item, "p", "🔍 Read: " + sources, "meta");
      list.appendChild(item);
    });
    activityEl.appendChild(list);
  }

  function load() {
    return fetch("/v1/steward/access", { headers: headers() })
      .then(readJson)
      .then(function (access) {
        const see = access.classes && access.classes.see ? access.classes.see : [];
        if (!seeTools.childNodes.length) renderTools(see);
        return Promise.all([
          fetch("/v1/steward/goals", { headers: headers() }).then(readJson),
          fetch("/v1/steward/activity", { headers: headers() }).then(readJson),
        ]);
      })
      .then(function (pair) {
        renderGoals(pair[0].goals || []);
        renderActivity(pair[1].activity || []);
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
        else if (name === "wake") setStatus("⚡ Woken now. Findings recorded in Brought back.");
        else setStatus("Closed. The record stays.");
        return load();
      })
      .catch(function (err) {
        setStatus(err.message || "The lab could not update that goal.");
      });
  }

  rhythm.addEventListener("click", function (event) {
    const button = event.target.closest("button[data-cron]");
    if (!button) return;
    const value = button.getAttribute("data-cron");
    preset.value = value;
    Array.prototype.forEach.call(rhythm.querySelectorAll("button"), function (item) {
      item.setAttribute("aria-pressed", item === button ? "true" : "false");
    });
    if (value === "custom") {
      cronRow.hidden = false;
      cronInput.focus();
      return;
    }
    cronInput.value = value;
    cronRow.hidden = true;
  });

  preset.addEventListener("change", function () {
    if (preset.value !== "custom") cronInput.value = preset.value;
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const tools = checkedTools();
    if (!tools.length) {
      setStatus("Leave it at least one thing to read.");
      return;
    }
    saveBtn.disabled = true;
    setStatus("");
    fetch("/v1/steward/goals", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({
        title: titleInput.value,
        intent: intentInput.value,
        wake_cron: cronInput.value,
        see_tools: tools,
      }),
    })
      .then(readJson)
      .then(function (goal) {
        newestId = goal.id || "";
        titleInput.value = "";
        intentInput.value = "";
        setStatus("It has this in its care now.");
        titleInput.focus();
        return load();
      })
      .catch(function (err) {
        setStatus(err.message || "The lab could not save that goal.");
      })
      .then(function () {
        saveBtn.disabled = false;
      });
  });

  document.addEventListener("ai-lab-auth-ready", load);
  if (form) load();
  window.loadSteward = load;
  window.mountSteward = load;
})();
