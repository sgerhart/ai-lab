/* Steward page: standing goals and wake activity. */
(function () {
  "use strict";

  const form = document.getElementById("goal-form");
  const titleInput = document.getElementById("goal-title");
  const intentInput = document.getElementById("goal-intent");
  const preset = document.getElementById("wake-preset");
  const cronInput = document.getElementById("wake-cron");
  const seeTools = document.getElementById("see-tools");
  const goalsEl = document.getElementById("goals");
  const activityEl = document.getElementById("activity");
  const statusEl = document.getElementById("status");
  const saveBtn = document.getElementById("save-goal");

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
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function add(parent, tag, text, className) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text == null ? "" : String(text);
    parent.appendChild(el);
    return el;
  }

  function empty(parent, text) {
    clear(parent);
    add(parent, "p", text, "empty");
  }

  function checkedTools() {
    return Array.prototype.map.call(
      seeTools.querySelectorAll("input[type=checkbox]:checked"),
      function (box) { return box.value; }
    );
  }

  function renderTools(names) {
    clear(seeTools);
    (names || []).forEach(function (name) {
      const item = document.createElement("li");
      const label = document.createElement("label");
      const box = document.createElement("input");
      box.type = "checkbox";
      box.value = name;
      box.checked = true;
      label.appendChild(box);
      label.appendChild(document.createTextNode(" " + name));
      item.appendChild(label);
      seeTools.appendChild(item);
    });
  }

  function statusClass(status) {
    if (status === "active" || status === "completed" || status === "queued") return "status-active";
    if (status === "paused") return "status-paused";
    if (status === "done" || status === "failed" || status === "error") return "status-done";
    return "meta";
  }

  function renderGoals(goals) {
    clear(goalsEl);
    if (!goals || !goals.length) {
      empty(goalsEl, "No goals yet.");
      return;
    }
    goals.forEach(function (goal) {
      const card = document.createElement("article");
      card.className = "card";
      add(card, "h3", goal.title || "Untitled");
      if (goal.intent) add(card, "p", goal.intent);
      const meta = add(card, "p", "", "meta");
      add(meta, "span", goal.status || "", statusClass(goal.status));
      meta.appendChild(document.createTextNode(
        " · " + (goal.wake_cron || "") +
        (goal.last_due_at ? " · last due " + goal.last_due_at : " · not due yet")
      ));
      if (goal.see_tools && goal.see_tools.length) {
        add(card, "p", "Reads " + goal.see_tools.join(", "), "meta");
      }
      const actions = document.createElement("div");
      actions.className = "actions";
      if (goal.status === "active") {
        const pause = document.createElement("button");
        pause.type = "button";
        pause.className = "ghost";
        pause.textContent = "Pause";
        pause.addEventListener("click", function () { act(goal.id, "pause"); });
        actions.appendChild(pause);
      }
      if (goal.status !== "done") {
        const close = document.createElement("button");
        close.type = "button";
        close.className = "ghost";
        close.textContent = "Close";
        close.addEventListener("click", function () { act(goal.id, "close"); });
        actions.appendChild(close);
      }
      if (actions.childNodes.length) card.appendChild(actions);
      goalsEl.appendChild(card);
    });
  }

  function renderActivity(entries) {
    clear(activityEl);
    if (!entries || !entries.length) {
      empty(activityEl, "Nothing has woken yet.");
      return;
    }
    entries.forEach(function (entry) {
      const card = document.createElement("article");
      card.className = "card";
      add(card, "h3", entry.goal_title || "Goal");
      const meta = add(card, "p", "", "meta");
      add(meta, "span", entry.status || "", statusClass(entry.status));
      if (entry.at) meta.appendChild(document.createTextNode(" · " + entry.at));
      if (entry.note) add(card, "p", entry.note, "note");
      if (entry.see_tools && entry.see_tools.length) {
        add(card, "p", "Reads " + entry.see_tools.join(", "), "meta");
      }
      activityEl.appendChild(card);
    });
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
    setStatus("");
    fetch("/v1/steward/goals/" + encodeURIComponent(id) + "/" + name, {
      method: "POST",
      headers: headers(),
    })
      .then(readJson)
      .then(function () {
        setStatus(name === "pause" ? "Paused." : "Closed.");
        return load();
      })
      .catch(function (err) {
        setStatus(err.message || "The lab could not update that goal.");
      });
  }

  preset.addEventListener("change", function () {
    if (preset.value !== "custom") cronInput.value = preset.value;
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const tools = checkedTools();
    if (!tools.length) {
      setStatus("Check at least one source a wake may read.");
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
      .then(function () {
        titleInput.value = "";
        intentInput.value = "";
        setStatus("Saved.");
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
  load();
})();
