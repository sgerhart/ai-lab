/* Agent Studio canvas. The host page owns auth, chat, and run approval. */
(function () {
  const PURPOSES = [
    { id: "build", label: "Build", agent: "coding-assistant", blurb: "Read a repo and change a separate copy after you approve." },
    { id: "learn", label: "Learn", agent: "research", blurb: "Teach a topic and write a sourced note." },
    { id: "product", label: "Product", agent: "research", blurb: "Draft a spec, a decision, or the next build step." },
    { id: "company", label: "Company", agent: "research", blurb: "Summarize files and the work of running the company." },
    { id: "lab", label: "Lab", agent: "lab-operations", blurb: "Check this lab. No file edits." },
  ];
  const TOOLS = [
    { id: "files", label: "Files", blurb: "Read the workspace" },
    { id: "git", label: "Git", blurb: "Status and diff" },
    { id: "sandbox", label: "Sandbox", blurb: "Separate copy for edits" },
    { id: "memory", label: "Memory", blurb: "Search what the lab remembers" },
    { id: "web", label: "Web", blurb: "Allowlisted fetch" },
  ];
  const SKILLS = [
    { group: "Build", items: [
      ["Explain a codebase", "Read the repo and name the parts that matter."],
      ["Implement a change", "Propose a patch in a separate copy and wait."],
      ["Review a diff", "Look for bugs and missing tests before you commit."],
    ]},
    { group: "Learn", items: [
      ["Tutor a topic", "Explain one idea, then give a small exercise."],
      ["Summarize a document", "Keep the claims tied to the source."],
      ["Turn a question into a project", "A short path from curiosity to something you can build."],
    ]},
    { group: "Product", items: [
      ["Draft a spec", "Users, scope, and what done means."],
      ["Decision log", "What you chose, and why."],
    ]},
    { group: "Company", items: [
      ["Weekly brief", "What moved, what is stuck, what is next."],
      ["Draft a reply", "A message you send yourself. Sending stays behind approval."],
    ]},
    { group: "Later", items: [
      ["Read mail", "Connect a mailbox, then summarize. Not connected yet."],
      ["Read a portfolio", "Balances and history only. Transfers stay behind approval."],
    ]},
  ];
  const ADV = ["Identity", "Instructions", "Model", "Context", "Memory", "Tools", "Skills", "Knowledge", "Workflow", "Permissions", "Runtime", "Versions"];
  const NAV = [
    ["", [["dashboard", "Dashboard"]]],
    ["Agents", [["agents", "My Agents"], ["templates", "Templates"], ["published", "Published"]]],
    ["Library", [["skills", "Skills"], ["tools", "Tools"], ["knowledge", "Knowledge"], ["memory", "Memory"], ["workflows", "Workflows"]]],
    ["Operate", [["runs", "Runs"], ["evaluations", "Evaluations"], ["permissions", "Permissions"]]],
  ];

  let host = null;
  let section = "dashboard";
  let mode = "simple";
  let adv = "Identity";
  let draft = null;
  let caps = null;
  let currentRun = null;
  let openStep = -1;

  function $(id) { return document.getElementById(id); }
  function purposeOf(id) { return PURPOSES.find((p) => p.id === id) || PURPOSES[0]; }
  function blankDraft(purposeId) {
    const p = purposeOf(purposeId || "build");
    return {
      id: null,
      title: "",
      purpose: p.id,
      agent: p.agent,
      instructions: "",
      role: "",
      objective: "",
      constraints: "Wait for approval before commit, push, send, delete, or anything that spends or moves money.",
      policies: "",
      output_format: "",
      model: "",
      backend: "",
      reasoning: "",
      temperature: "",
      fallback: "",
      tools: p.id === "build" ? ["files", "git", "sandbox"] : ["memory"],
      skills: [],
      knowledge: "",
      memory: { session: true, user: true, agent: true, shared: false, retention_days: 30 },
      workflow: "manager",
      cron: "",
      mcp: "",
      versions: [],
      change_note: "",
      task: "",
    };
  }
  function el(tag, attrs, kids) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else if (k === "html") node.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2).toLowerCase(), v);
      else if (v != null && v !== false) node.setAttribute(k, String(v));
    });
    (kids || []).forEach((kid) => {
      if (kid == null) return;
      node.appendChild(typeof kid === "string" ? document.createTextNode(kid) : kid);
    });
    return node;
  }
  function mark() {
    document.querySelectorAll(".studio-link").forEach((btn) => {
      const id = btn.getAttribute("data-studio");
      const on = id === section || (section === "builder" && id === "agents");
      btn.classList.toggle("active", on);
    });
  }
  function toolList(tools) {
    if (!Array.isArray(tools)) return [];
    return tools.map((t) => (typeof t === "string" ? t : (t && t.name) || "")).filter(Boolean);
  }
  function badges(d) {
    const row = el("div", { class: "badge-row" });
    const p = purposeOf(d.purpose || "build");
    row.appendChild(el("span", { class: "pill on", text: p.label }));
    toolList(d.tools).slice(0, 3).forEach((t) => row.appendChild(el("span", { class: "pill", text: t })));
    if ((d.memory || {}).agent) row.appendChild(el("span", { class: "pill", text: "Memory" }));
    return row;
  }
  function fromDefinition(d) {
    const studio = d.studio && typeof d.studio === "object" ? d.studio : {};
    const next = Object.assign(blankDraft(studio.purpose), studio, {
      id: d.id,
      title: d.title || "",
      agent: d.agent || "lab-operations",
      instructions: studio.instructions || d.system_prompt || "",
      cron: d.schedule_cron || studio.cron || "",
      mcp: (d.mcp_server_ids || []).join(", "),
      tools: studio.tools || blankDraft(studio.purpose).tools,
      versions: studio.versions || [],
    });
    return next;
  }
  function composePrompt(d) {
    if (mode === "simple") {
      const lines = ["Purpose: " + purposeOf(d.purpose).label];
      if (d.instructions.trim()) lines.push(d.instructions.trim());
      if (d.knowledge.trim()) lines.push("Knowledge:\n" + d.knowledge.trim());
      return lines.join("\n\n");
    }
    const parts = [
      ["Role", d.role],
      ["Objective", d.objective],
      ["Constraints", d.constraints],
      ["Policies", d.policies],
      ["Output format", d.output_format],
      ["Instructions", d.instructions],
      ["Knowledge", d.knowledge],
    ];
    return parts.filter(([, v]) => (v || "").trim()).map(([k, v]) => k + ":\n" + v.trim()).join("\n\n");
  }
  function field(label, node) {
    return el("div", { class: "field" }, [el("label", { text: label }), node]);
  }
  function input(value, on, attrs) {
    const node = el("input", Object.assign({ type: "text", value: value || "" }, attrs || {}));
    node.addEventListener("input", () => on(node.value));
    return node;
  }
  function area(value, on, rows) {
    const node = el("textarea", { rows: String(rows || 4) });
    node.value = value || "";
    node.addEventListener("input", () => on(node.value));
    return node;
  }

  function renderDashboard(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Agent Studio" }),
      el("p", { text: "Design agents for building, learning, and the work around your product and company. Chat stays the place you talk. This is the place you shape the agent." }),
    ]));
    const launch = el("div", { class: "studio-launch" });
    [["build", "Build something", "A coding agent that edits only a separate copy, and only after you approve."],
      ["learn", "Learn a topic", "A tutor that stays sourced and remembers what you are studying."],
      ["company", "Run the company", "Briefs, drafts, and files. Sending and spending wait for you."],
    ].forEach(([id, title, blurb]) => {
      launch.appendChild(el("button", { class: "launch-card", type: "button", onclick: () => openBuilder(id) }, [
        el("strong", { text: title }),
        el("span", { text: blurb }),
      ]));
    });
    root.appendChild(launch);
    root.appendChild(el("div", { class: "studio-h", text: "Your agents" }));
    renderAgentBoard(root);
  }
  function renderAgentBoard(root) {
    const defs = (host.state.definitions || []);
    const board = el("div", { class: "agent-board" });
    if (!defs.length) {
      board.appendChild(el("p", { class: "muted", text: "No agents yet. Start from a template when you want a tracked agent for building, learning, or the company." }));
    }
    defs.forEach((d) => {
      const studio = d.studio || {};
      const tile = el("button", { class: "agent-tile", type: "button", onclick: () => openExisting(d) }, [
        el("h3", { text: d.title || "Untitled" }),
      ]);
      tile.appendChild(badges(Object.assign({ purpose: studio.purpose || "build", model: studio.model, tools: studio.tools, memory: studio.memory }, studio)));
      board.appendChild(tile);
    });
    root.appendChild(board);
  }
  function renderTemplates(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Templates" }),
      el("p", { text: "Start from the job. You can change the model, tools, and instructions before you save." }),
    ]));
    const grid = el("div", { class: "lib-grid" });
    PURPOSES.forEach((p) => {
      grid.appendChild(el("button", { class: "lib-card", type: "button", onclick: () => openBuilder(p.id) }, [
        el("strong", { text: p.label }),
        el("span", { text: p.blurb }),
      ]));
    });
    root.appendChild(grid);
  }
  function renderSkills(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Skills" }),
      el("p", { text: "A tool can open a file. A skill knows how to do a job. Attach one from the agent builder." }),
    ]));
    SKILLS.forEach((group) => {
      root.appendChild(el("div", { class: "studio-h", text: group.group }));
      const grid = el("div", { class: "lib-grid" });
      group.items.forEach(([name, blurb]) => {
        const later = group.group === "Later";
        grid.appendChild(el("button", {
          class: "lib-card",
          type: "button",
          onclick: () => attachSkill(name),
        }, [
          el("strong", { text: name }),
          el("span", { text: blurb }),
          el("div", { class: "badge-row" }, [el("span", { class: later ? "pill later" : "pill on", text: later ? "Add-on" : "Attach" })]),
        ]));
      });
      root.appendChild(grid);
    });
  }
  function attachSkill(name) {
    if (!draft) openBuilder("build");
    if (!draft.skills.includes(name)) draft.skills.push(name);
    if (!draft.instructions.includes(name)) {
      draft.instructions = (draft.instructions ? draft.instructions + "\n" : "") + "Skill: " + name + ".";
    }
    section = "builder";
    mode = "advanced";
    adv = "Skills";
    host.setView("agent");
  }
  function renderTools(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Tools" }),
      el("p", { text: "Native tools the lab can already run, plus MCP servers you have saved. A saved server is not permission to call it. Enterprise systems can be added later as connections, not as the point of the studio." }),
    ]));
    root.appendChild(el("div", { class: "studio-h", text: "Native" }));
    const grid = el("div", { class: "lib-grid" });
    const list = (caps && caps.capabilities) || [];
    if (!list.length) {
      grid.appendChild(el("p", { class: "muted", text: "Open this page while signed in to see the live tool list." }));
    }
    list.forEach((cap) => {
      const risk = cap.risk || "";
      grid.appendChild(el("article", { class: "lib-card" }, [
        el("strong", { text: cap.name || "" }),
        el("span", { text: ((cap.tools || [])[0] || {}).description || cap.connection_state || "" }),
        el("div", { class: "badge-row" }, [
          el("span", { class: cap.permitted ? "pill on" : "pill later", text: cap.connection_state || risk }),
        ]),
      ]));
    });
    root.appendChild(grid);
  }
  function renderStatic(root, title, lead, body) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: title }),
      el("p", { text: lead }),
    ]));
    body.forEach((block) => root.appendChild(block));
  }
  function renderKnowledge(root) {
    renderStatic(root, "Knowledge", "Notes, project files, and repo context an agent may read. Project documents already live under Projects. This page is the studio view of that idea.", [
      el("p", { class: "muted", text: "Put the sources on the agent when you build it. The Knowledge step is saved with the agent." }),
    ]);
  }
  function renderMemory(root) {
    renderStatic(root, "Memory", "Memory is several stores, not one bucket. Each agent sets its own policy in the builder.", [
      el("div", { class: "lib-grid" }, [
        ["Working", "The current task."],
        ["Session", "This conversation."],
        ["Episodic", "Earlier tasks and what happened."],
        ["Semantic", "Facts and notes."],
        ["User", "Your preferences."],
        ["Agent", "What this agent has learned."],
        ["Shared", "Off unless you turn it on for a team of agents."],
      ].map(([name, blurb]) => el("article", { class: "lib-card" }, [el("strong", { text: name }), el("span", { text: blurb })]))),
    ]);
  }
  function renderWorkflows(root) {
    renderStatic(root, "Workflows", "Three ways agents can work together. Today a run is one agent that stays responsible. Handoffs and explicit graphs come next.", [
      el("div", { class: "pattern-grid" }, [
        ["Manager", "One agent owns the task and may use tools.", "Live"],
        ["Handoff", "Build, then review, then you approve.", "Later"],
        ["Graph", "Steps with a condition and two branches.", "Later"],
      ].map(([name, blurb, tag]) => el("article", { class: "pattern-card" }, [
        el("strong", { text: name }),
        el("span", { text: blurb }),
        el("div", { class: "badge-row" }, [el("span", { class: tag === "Live" ? "pill on" : "pill later", text: tag })]),
      ]))),
    ]);
  }
  function renderPublished(root) {
    renderStatic(root, "Published", "An agent card other agents could read later: name, capabilities, tools, input, output, and permissions. Nothing is published yet.", [
      el("p", { class: "muted", text: "Save an agent first. Publishing and agent-to-agent handoff stay in the next phase." }),
    ]);
  }
  function renderEvaluations(root) {
    renderStatic(root, "Evaluations", "Each agent should have a small suite you can rerun when the model, prompt, or skill changes. No suite has run yet.", [
      el("article", { class: "lib-card" }, [
        el("strong", { text: "What a comparison will show" }),
        el("span", { text: "Accuracy, tool errors, cost, and latency for two saved versions. The version list on an agent is already stored when you save." }),
      ]),
    ]);
  }
  function traceLabel(trace) {
    if (trace.kind === "model_call") return "Model";
    if (trace.kind === "tool_result") return "Tool · " + (trace.tool || "call");
    if (trace.kind === "final") return "Complete";
    return trace.kind || "Step";
  }
  function traceBody(trace) {
    if (trace.kind === "tool_result") return (trace.ok ? "ok" : "fail") + "\n" + (trace.observation || "");
    return trace.text || trace.observation || "";
  }
  function renderRuns(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Runs" }),
      el("p", { text: "Tasks the mini is running or has finished. Open one to see the timeline and approve a step." }),
    ]));
    const runs = host.state.runs || [];
    if (!runs.length) {
      root.appendChild(el("p", { class: "muted", text: "No runs yet. Open an agent and choose Run." }));
      return;
    }
    runs.forEach((run) => {
      const row = el("button", { class: "run-row", type: "button", onclick: () => host.openRun(run.id).catch((e) => host.showErr(e)) }, [
        el("span", { text: run.objective || "Untitled task" }),
        el("span", { class: "pill", text: run.status || "" }),
      ]);
      root.appendChild(row);
    });
  }
  function renderRun(root) {
    const run = currentRun;
    if (!run) {
      renderRuns(root);
      return;
    }
    root.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => show("runs"), text: "← Runs" }));
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Run" }),
      el("p", { text: run.objective || run.id || "" }),
    ]));
    const meta = el("div", { class: "badge-row" });
    meta.appendChild(el("span", { class: "pill on", text: run.status || "unknown" }));
    if (run.model) meta.appendChild(el("span", { class: "pill", text: run.model }));
    if (run.backend) meta.appendChild(el("span", { class: "pill", text: run.backend }));
    root.appendChild(meta);
    if (run.error) root.appendChild(el("p", { class: "muted", text: run.error }));
    const list = el("div", { class: "timeline" });
    const traces = run.traces || [];
    if (!traces.length) list.appendChild(el("p", { class: "muted", text: "No steps yet. A queued run fills this timeline as the worker proceeds." }));
    traces.forEach((trace, index) => {
      const open = openStep === index;
      const step = el("button", {
        class: "tl-step",
        type: "button",
        onclick: () => { openStep = open ? -1 : index; render(); },
      }, [
        el("div", { class: "when", text: traceLabel(trace) }),
        el("div", { class: "what", text: (traceBody(trace) || "").replace(/\s+/g, " ").slice(0, 180) }),
      ]);
      if (open) step.appendChild(el("div", { class: "tl-detail", text: traceBody(trace) }));
      list.appendChild(step);
    });
    root.appendChild(list);
    if (run.pending_action) {
      const box = el("div", { class: "run-box" });
      box.appendChild(el("div", { class: "studio-h", text: "Approval" }));
      box.appendChild(el("p", { class: "muted", text: JSON.stringify(run.pending_action, null, 2) }));
      const row = el("div", { class: "builder-actions" });
      row.appendChild(el("button", { class: "studio-new", type: "button", onclick: () => decide("approved"), text: "Approve" }));
      row.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => decide("denied"), text: "Reject" }));
      box.appendChild(row);
      root.appendChild(box);
    }
    const actions = el("div", { class: "builder-actions" });
    actions.style.marginTop = "16px";
    actions.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => act("cancel"), text: "Cancel" }));
    actions.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => act("retry"), text: "Retry" }));
    root.appendChild(actions);
  }
  async function decide(decision) {
    const run = await host.api("/v1/agent-runs/" + currentRun.id + "/approve-action", {
      method: "POST",
      body: JSON.stringify({ decision: decision, action_id: host.state.pendingActionId }),
    });
    host.showRun(run);
  }
  async function act(name) {
    const run = await host.api("/v1/agent-runs/" + currentRun.id + "/" + name, { method: "POST", body: "{}" });
    host.showRun(run);
  }
  function renderPermissions(root) {
    renderStatic(root, "Permissions", "Low risk is search and read. Medium is create and modify. High is delete, execute, deploy, send, or move money. High risk waits for you.", [
      el("div", { class: "lib-grid" }, [
        ["Read files and git", "Allowed for a build agent.", "Low"],
        ["Patch or commit", "Only in a separate copy, and only after you approve that exact change.", "High"],
        ["Push, send, spend, transfer", "Not granted. A later skill still stops for approval.", "High"],
      ].map(([name, blurb, tag]) => el("article", { class: "lib-card" }, [
        el("strong", { text: name }),
        el("span", { text: blurb }),
        el("div", { class: "badge-row" }, [el("span", { class: tag === "Low" ? "pill on" : "pill later", text: tag })]),
      ]))),
    ]);
  }

  function simpleBuilder(root) {
    const steps = el("div", { class: "step-list" });
    const name = input(draft.title, (v) => { draft.title = v; });
    name.className = "";
    steps.appendChild(el("section", { class: "step" }, [
      el("div", { class: "n", text: "1 · Name" }),
      field("Name", input(draft.title, (v) => { draft.title = v; }, { placeholder: "Product builder" })),
    ]));
    const purposes = el("div", { class: "purpose-row" });
    PURPOSES.forEach((p) => {
      purposes.appendChild(el("button", {
        type: "button",
        class: p.id === draft.purpose ? "on" : "",
        onclick: () => {
          draft.purpose = p.id;
          draft.agent = p.agent;
          render();
        },
      }, [p.label, el("small", { text: p.blurb })]));
    });
    steps.appendChild(el("section", { class: "step" }, [
      el("div", { class: "n", text: "2 · Purpose" }),
      purposes,
    ]));
    const model = el("select");
    const blank = el("option", { value: "", text: "Use the chat model" });
    model.appendChild(blank);
    (host.state.choices || []).forEach((c) => {
      const opt = el("option", { value: c.backend + "::" + c.model, text: (c.label || c.model) + (c.billing_class === "local" ? " · local" : " · billed") });
      if (draft.backend === c.backend && draft.model === c.model) opt.selected = true;
      model.appendChild(opt);
    });
    model.addEventListener("change", () => {
      const [backend, ...rest] = model.value.split("::");
      draft.backend = backend || "";
      draft.model = rest.join("::");
    });
    steps.appendChild(el("section", { class: "step" }, [
      el("div", { class: "n", text: "3 · Model" }),
      field("Model", model),
      el("p", { class: "note", text: "Local Studio models stay the default. A billed model runs only if you have already authorized spend." }),
    ]));
    const tools = el("div", { class: "tool-row" });
    TOOLS.forEach((t) => {
      const on = (draft.tools || []).includes(t.id);
      tools.appendChild(el("button", {
        type: "button",
        class: on ? "on" : "",
        onclick: () => {
          draft.tools = on ? draft.tools.filter((x) => x !== t.id) : draft.tools.concat([t.id]);
          render();
        },
      }, [t.label, el("small", { text: t.blurb })]));
    });
    steps.appendChild(el("section", { class: "step" }, [
      el("div", { class: "n", text: "4 · Tools" }),
      tools,
      el("p", { class: "note", text: "The agent kind still decides what the runtime may call. A build agent can patch only after you approve, and only in a separate copy." }),
    ]));
    steps.appendChild(el("section", { class: "step" }, [
      el("div", { class: "n", text: "5 · Knowledge" }),
      field("What should it read?", area(draft.knowledge, (v) => { draft.knowledge = v; }, 3)),
    ]));
    steps.appendChild(el("section", { class: "step" }, [
      el("div", { class: "n", text: "6 · Instructions" }),
      field("How should it work?", area(draft.instructions, (v) => { draft.instructions = v; }, 5)),
    ]));
    root.appendChild(steps);
  }
  function advBuilder(root) {
    const shell = el("div", { class: "adv-shell" });
    const nav = el("div", { class: "adv-nav" });
    ADV.forEach((name) => {
      nav.appendChild(el("button", { type: "button", class: name === adv ? "on" : "", onclick: () => { adv = name; render(); } }, [name]));
    });
    const panel = el("div");
    const mem = draft.memory || {};
    if (adv === "Identity") {
      panel.appendChild(field("Name", input(draft.title, (v) => { draft.title = v; })));
      panel.appendChild(field("Description", area(draft.objective, (v) => { draft.objective = v; }, 3)));
      panel.appendChild(el("p", { class: "note", text: "Version " + String((draft.versions || []).length + 1) + ". Icon and a public agent card come with publishing." }));
    } else if (adv === "Instructions") {
      ["role", "objective", "constraints", "policies", "output_format", "instructions"].forEach((key) => {
        const label = key.replace("_", " ");
        panel.appendChild(field(label.charAt(0).toUpperCase() + label.slice(1), area(draft[key], (v) => { draft[key] = v; }, key === "instructions" ? 5 : 3)));
      });
    } else if (adv === "Model") {
      panel.appendChild(field("Model id", input(draft.model, (v) => { draft.model = v; }, { placeholder: "llama3.2:3b" })));
      panel.appendChild(field("Provider", input(draft.backend, (v) => { draft.backend = v; }, { placeholder: "ollama" })));
      panel.appendChild(field("Reasoning", input(draft.reasoning, (v) => { draft.reasoning = v; })));
      panel.appendChild(field("Temperature", input(draft.temperature, (v) => { draft.temperature = v; })));
      panel.appendChild(field("Fallback", input(draft.fallback, (v) => { draft.fallback = v; })));
      panel.appendChild(el("p", { class: "note", text: "Stored on the agent. A run uses the model you pick here, or the chat model if this is blank. Temperature is not sent to the runtime yet." }));
    } else if (adv === "Memory") {
      [["session", "Session memory"], ["user", "User memory"], ["agent", "Agent learning"], ["shared", "Shared memory"]].forEach(([key, label]) => {
        const box = el("input", { type: "checkbox" });
        box.checked = !!mem[key];
        box.addEventListener("change", () => { draft.memory[key] = box.checked; });
        panel.appendChild(el("label", { class: "toggle-line" }, [label, box]));
      });
      panel.appendChild(field("Retention (days)", input(String(mem.retention_days || 30), (v) => { draft.memory.retention_days = Number(v) || 30; })));
    } else if (adv === "Tools") {
      panel.appendChild(field("MCP server ids", input(draft.mcp, (v) => { draft.mcp = v; }, { placeholder: "Leave blank unless you added a server under MCP" })));
      panel.appendChild(el("p", { class: "note", text: "Only servers on your allowlist are accepted." }));
    } else if (adv === "Skills") {
      panel.appendChild(el("p", { class: "muted", text: draft.skills.length ? draft.skills.join(", ") : "No skills attached. Pick one from Skills." }));
    } else if (adv === "Knowledge") {
      panel.appendChild(field("Knowledge", area(draft.knowledge, (v) => { draft.knowledge = v; }, 5)));
    } else if (adv === "Workflow") {
      panel.appendChild(field("Mode", input(draft.workflow, (v) => { draft.workflow = v; }, { placeholder: "manager" })));
      panel.appendChild(field("Schedule", input(draft.cron, (v) => { draft.cron = v; }, { placeholder: "Optional. 0 9 * * *" })));
    } else if (adv === "Context") {
      panel.appendChild(el("p", { class: "muted", text: "Working context is the current task and the conversation you run from. It is not the same store as durable memory." }));
    } else if (adv === "Permissions") {
      panel.appendChild(el("p", { class: "muted", text: "Commit, push, send, delete, and transfers wait for approval. This page records that policy on the agent. The runtime still enforces the agent kind." }));
    } else if (adv === "Runtime") {
      panel.appendChild(el("p", { class: "muted", text: "This definition runs on the mini, with models on the Studio. A build agent uses an isolated copy as its sandbox. Cloud and Kubernetes runtimes are later." }));
    } else if (adv === "Versions") {
      const list = draft.versions || [];
      if (!list.length) panel.appendChild(el("p", { class: "muted", text: "The first save becomes version 1." }));
      list.forEach((v) => panel.appendChild(el("p", { class: "muted", text: "v" + v.version + " · " + (v.note || "Saved") + " · " + (v.at || "") })));
      panel.appendChild(field("Note for the next save", input(draft.change_note, (v) => { draft.change_note = v; })));
    }
    shell.appendChild(nav);
    shell.appendChild(panel);
    root.appendChild(shell);
  }
  function renderBuilder(root) {
    const top = el("div", { class: "builder-top" });
    const left = el("div");
    left.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => show("agents"), text: "← My Agents" }));
    const title = el("input", { class: "builder-title", value: draft.title, placeholder: "Name this agent" });
    title.addEventListener("input", () => { draft.title = title.value; });
    left.appendChild(title);
    left.appendChild(badges(draft));
    const actions = el("div", { class: "builder-actions" });
    actions.appendChild(el("div", { class: "seg" }, [
      el("button", { type: "button", class: mode === "simple" ? "on" : "", onclick: () => { mode = "simple"; render(); }, text: "Simple" }),
      el("button", { type: "button", class: mode === "advanced" ? "on" : "", onclick: () => { mode = "advanced"; render(); }, text: "Advanced" }),
    ]));
    actions.appendChild(el("button", { class: "studio-new", type: "button", onclick: () => saveDraft().catch((e) => host.showErr(e)), text: draft.id ? "Save" : "Create" }));
    top.appendChild(left);
    top.appendChild(actions);
    root.appendChild(top);
    if (mode === "simple") simpleBuilder(root);
    else advBuilder(root);
    const run = el("div", { class: "run-box" });
    run.appendChild(el("div", { class: "studio-h", text: "Run" }));
    run.appendChild(field("Task", area(draft.task, (v) => { draft.task = v; }, 3)));
    const row = el("div", { class: "builder-actions" });
    if (draft.purpose === "build") {
      row.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => prepareCopy().catch((e) => host.showErr(e)), text: "Prepare a separate copy" }));
    }
    row.appendChild(el("button", { class: "studio-new", type: "button", onclick: () => runDraft().catch((e) => host.showErr(e)), text: "Run" }));
    run.appendChild(row);
    run.appendChild(el("p", { class: "note", text: host.state.worktreeId ? "Separate copy " + host.state.worktreeId + " is ready." : "A build run can read before a copy exists. It cannot change files until you prepare one and approve the edit." }));
    root.appendChild(run);
  }

  const PAGES = {
    dashboard: renderDashboard,
    agents: (root) => {
      root.appendChild(el("div", { class: "studio-hero" }, [el("h1", { text: "My Agents" }), el("p", { text: "Open an agent to change it, or start a new one." })]));
      renderAgentBoard(root);
    },
    templates: renderTemplates,
    published: renderPublished,
    skills: renderSkills,
    tools: renderTools,
    knowledge: renderKnowledge,
    memory: renderMemory,
    workflows: renderWorkflows,
    evaluations: renderEvaluations,
    permissions: renderPermissions,
    builder: renderBuilder,
    runs: renderRuns,
    run: renderRun,
  };

  function render() {
    const root = $("studio-canvas");
    if (!root) return;
    mark();
    const next = document.createElement("div");
    next.className = "studio-page";
    try {
      const page = PAGES[section] || renderDashboard;
      page(next);
    } catch (err) {
      next.appendChild(el("p", { class: "muted", text: String(err && err.message || err) }));
    }
    root.replaceChildren(next);
    if (section === "tools" && !caps) {
      host.api("/v1/capabilities?agent=coding-assistant").then((data) => {
        caps = data;
        if (section === "tools") render();
      }).catch(() => {});
    }
  }
  function studioCovered() {
    const shell = document.getElementById("prefs-shell");
    return !document.body.classList.contains("in-studio") || (shell && shell.classList.contains("open"));
  }
  function show(name) {
    section = name === "builder" ? "builder" : name;
    if (name === "runs") {
      const paint = () => {
        if (host.state.view === "agents" && !studioCovered()) render();
        else host.setView("agents");
      };
      host.loadRuns().then(paint).catch((e) => { host.showErr(e); paint(); });
      return;
    }
    if (studioCovered() || (host.state.view !== "agents" && host.state.view !== "agent")) {
      host.setView(name === "builder" ? "agent" : "agents");
      return;
    }
    if (name === "builder") host.setView("agent");
    else if (host.state.view !== "agents") host.setView("agents");
    else render();
  }
  function openBuilder(purposeId) {
    draft = blankDraft(purposeId);
    mode = "simple";
    section = "builder";
    host.setView("agent");
  }
  function openExisting(d) {
    draft = fromDefinition(d);
    mode = "simple";
    section = "builder";
    host.state.definitionId = d.id;
    host.setView("agent");
  }
  async function saveDraft() {
    const p = purposeOf(draft.purpose);
    draft.agent = p.agent;
    const versions = (draft.versions || []).slice(-19);
    versions.push({
      version: versions.length + 1,
      at: new Date().toISOString(),
      note: draft.change_note || "Saved from Agent Studio",
      purpose: draft.purpose,
      model: draft.model || "",
    });
    draft.versions = versions;
    draft.change_note = "";
    const studio = Object.assign({}, draft);
    delete studio.id;
    delete studio.task;
    const body = {
      title: draft.title || "Untitled agent",
      agent: draft.agent,
      system_prompt: composePrompt(draft),
      tools: draft.tools || [],
      mcp_server_ids: (draft.mcp || "").split(",").map((s) => s.trim()).filter(Boolean),
      schedule_cron: (draft.cron || "").trim(),
      studio: studio,
    };
    const saved = draft.id
      ? await host.api("/v1/agent-definitions/" + draft.id, { method: "PUT", body: JSON.stringify(body) })
      : await host.api("/v1/agent-definitions", { method: "POST", body: JSON.stringify(body) });
    draft.id = saved.id;
    host.state.definitionId = saved.id;
    await host.loadDefinitions();
    host.showErr("");
    render();
  }
  async function prepareCopy() {
    const created = await host.api("/v1/coding/worktrees", { method: "POST", body: "{}" });
    host.state.worktreeId = created.id || "";
    host.showErr("");
    render();
  }
  async function runDraft() {
    if (!draft.id) await saveDraft();
    const choice = draft.model
      ? { model: draft.model, backend: draft.backend || "ollama", billing_class: draft.backend && draft.backend !== "ollama" ? "usage_billed_api" : "local" }
      : host.selectedChoice();
    const run = await host.api("/v1/agent-definitions/" + draft.id + "/runs", {
      method: "POST",
      body: JSON.stringify({
        objective: (draft.task || "").trim() || draft.title || "Start the task.",
        model: choice.model || "llama3.2:3b",
        billing_class: choice.billing_class || "local",
        backend: choice.backend || "ollama",
        max_steps: 8,
        worktree_id: draft.purpose === "build" && host.state.worktreeId ? host.state.worktreeId : "",
      }),
    });
    host.showRun(run);
  }

  function bindRail() {
    document.querySelectorAll(".studio-link").forEach((btn) => {
      const id = btn.getAttribute("data-studio");
      if (!id) return;
      btn.addEventListener("click", () => show(id));
    });
    const newer = $("studio-new");
    if (newer) newer.addEventListener("click", () => openBuilder("build"));
    const toggle = $("toggle-studio");
    const showBtn = $("show-studio");
    function toggleRail() {
      const collapsed = $("studio-rail").classList.toggle("collapsed");
      if (showBtn) showBtn.hidden = !collapsed;
    }
    if (toggle) toggle.addEventListener("click", toggleRail);
    if (showBtn) showBtn.addEventListener("click", toggleRail);
  }

  window.mountAgentStudio = function mountAgentStudio(next) {
    host = next;
    bindRail();
    window.agentStudio = {
      render: render,
      show: show,
      openBuilder: openBuilder,
      openAgent: (id) => {
        const d = (host.state.definitions || []).find((x) => x.id === id);
        if (d) openExisting(d);
      },
      mark: (name) => { section = name; mark(); },
      presentRun: (run) => {
        currentRun = run;
        openStep = -1;
        section = "run";
        if (host.state.view === "agents" && !studioCovered()) render();
        else host.setView("agents");
      },
    };
  };
})();
