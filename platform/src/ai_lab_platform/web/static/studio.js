/* Agent Studio: Streamlined Super Agent Fleet, 1-Page Configurator, and Live Operations */
(function () {
  const FLEET_PRESETS = [
    {
      id: "second-brain",
      title: "Second Brain & Partner",
      agent: "personal",
      purpose: "second-brain",
      icon: "🧠",
      blurb: "Your high-intellect peer. Synthesizes memory, conducts deep web searches, drafts executive decisions, and retains persistent context.",
      tools: ["memory", "web", "files", "reports"],
      model: "qwen3.6:35b-a3b",
      instructions: "You are the operator's primary Second Brain and high-intellect strategic partner. Provide deeply reasoned, proactive, and structured guidance. Synthesize past memories, verify current web facts, and deliver insightful solutions.",
    },
    {
      id: "coding-pair",
      title: "Autonomous Coding Pair",
      agent: "coding-assistant",
      purpose: "build",
      icon: "💻",
      blurb: "Senior engineering peer. Reads the codebase, designs architectures, and proposes changes in isolated Git worktrees with human approval gates.",
      tools: ["files", "git", "sandbox"],
      model: "qwen3-coder:30b",
      instructions: "You are a senior principal software engineer. Inspect the repository, analyze code structure, and draft rigorous patches. All filesystem changes occur in isolated Git worktree sandboxes and require operator approval.",
    },
    {
      id: "deep-research",
      title: "Deep Research & Reports",
      agent: "research",
      purpose: "research",
      icon: "🔍",
      blurb: "Advanced research specialist. Investigates topics across the live internet, extracts technical sources, and compiles comprehensive structured reports.",
      tools: ["web", "files", "reports", "memory"],
      model: "qwen3.6:35b-a3b",
      instructions: "You are a research scientist. Conduct exhaustive web investigations, cross-reference credible sources, and compile clear, structured executive briefings in markdown.",
    },
    {
      id: "system-ops",
      title: "Lab System Operations",
      agent: "lab-operations",
      purpose: "lab",
      icon: "⚙️",
      blurb: "Systems and infrastructure administrator. Monitors Mac mini host health, tailnet connectivity, model memory usage, and background jobs.",
      tools: ["files", "memory"],
      model: "llama3.2:3b",
      instructions: "You are the AI Lab Systems Engineer. Monitor host health, inspect logs, check Tailscale networking, and ensure zero-downtime control plane operation.",
    },
    {
      id: "security-compute",
      title: "Security Compute Agent",
      agent: "security",
      purpose: "security",
      icon: "🛡️",
      blurb: "Security compute lifecycle specialist. Validates templates, isolated networks, and bounded analysis VMs with strict human approval gates and residual cleanup audit.",
      tools: ["files", "sandbox", "reports"],
      model: "qwen3.6:35b-a3b",
      instructions: "You are the Security Compute Agent. Validate VM templates and isolated analysis networks. Ephemeral lifecycle operations and untrusted executions strictly require human approval. Residual resources are permanently audited.",
    },
  ];

  const PURPOSES = [
    { id: "second-brain", label: "Second Brain", agent: "personal", blurb: "Executive partner, memory synthesis, web research." },
    { id: "build", label: "Coding Pair", agent: "coding-assistant", blurb: "Read repo and change code in isolated git worktrees." },
    { id: "research", label: "Deep Research", agent: "research", blurb: "Internet deep dives and sourced reports." },
    { id: "product", label: "Product & Spec", agent: "research", blurb: "Specs, architecture decisions, and roadmaps." },
    { id: "lab", label: "System Ops", agent: "lab-operations", blurb: "Host health, tailnet checks, telemetry." },
    { id: "security", label: "Security Compute", agent: "security", blurb: "VM template validation, isolated analysis, residual cleanup audit." },
  ];

  const AVAILABLE_TOOLS = [
    { id: "files", label: "Files", icon: "📁", blurb: "Read workspace & repo context" },
    { id: "git", label: "Git", icon: "🌿", blurb: "Status, branch inspection, diffs" },
    { id: "sandbox", label: "Sandbox", icon: "🛡️", blurb: "Isolated worktree edits with human gate" },
    { id: "memory", label: "Memory", icon: "🧠", blurb: "Search persistent lab memory & insights" },
    { id: "web", label: "Web Search", icon: "🌐", blurb: "Search internet and read live web pages" },
    { id: "reports", label: "Reports", icon: "📊", blurb: "Draft structured executive reports" },
  ];

  const SKILLS = [
    { group: "Engineering", items: [
      ["Explain Architecture", "Analyze the repository structure and key dependencies."],
      ["Implement Patch", "Propose a tested patch in an isolated git worktree."],
      ["Review Diffs", "Review code changes for security, logic errors, and test coverage."],
    ]},
    { group: "Second Brain & Research", items: [
      ["Executive Synthesis", "Synthesize multiple documents into strategic decisions."],
      ["Web Deep Dive", "Investigate an external technical topic and cite sources."],
      ["Memory Journaling", "Record insights and patterns into persistent lab memory."],
    ]},
    { group: "Operations", items: [
      ["Host Health Check", "Inspect Mac mini resource utilization and daemon status."],
      ["Tailnet Verify", "Confirm trusted Tailscale mesh connectivity and zero-trust auth."],
    ]},
  ];

  let host = null;
  let section = "dashboard";
  let draft = null;
  let currentRun = null;
  let openStep = -1;

  function evaluateDraftPosture(d) {
    if (!d) return { isolation_tier: 1, filesystem_class: "read-only", network_class: "none", approval_required_tools: [], warnings: [] };
    const agent = d.agent || "personal";
    const tools = (d.studio && d.studio.tools) || d.tools || [];
    let tier = 1;
    let tierLabel = "Bounded Local Sandbox";
    let fs = "Read-Only";
    let fsSub = "Zero primary tree mutation";
    let net = "None";
    let netSub = "Zero external network egress";
    const approval = [];
    const warnings = [];

    if (agent === "coding-assistant") {
      const hasWorktree = tools.includes("sandbox") || tools.includes("git_commit") || tools.includes("apply_patch");
      tier = hasWorktree ? 2 : 1;
      tierLabel = hasWorktree ? "Isolated Worktree Sandbox" : "Bounded Local Read-Only";
      fs = "Isolated Worktree";
      fsSub = "Changes restricted to throwaway git worktree";
      net = "None";
      netSub = "Zero external network egress";
      approval.push("apply_patch", "git_commit");
    } else if (agent === "personal") {
      tier = 0;
      tierLabel = "Trusted User Vault";
      fs = "User Vault Scoped";
      fsSub = "Scoped strictly to ~/.ai-lab/";
      net = "Egress Allowlist";
      netSub = "Public web search & cited fetch allowlist";
    } else if (agent === "research") {
      tier = 1;
      tierLabel = "Bounded Research Loop";
      fs = "Reports Scoped";
      fsSub = "Writes restricted to markdown reports";
      net = "Egress Allowlist";
      netSub = "Public web search & verified sources";
    } else if (agent === "lab-operations") {
      tier = 1;
      tierLabel = "Local Host Inspection";
      fs = "Read-Only";
      fsSub = "Host metrics and telemetry only";
      net = "None";
      netSub = "Zero external egress";
      if (tools.includes("memory_write")) approval.push("lab_memory_upsert");
    } else if (agent === "vuln-localize") {
      tier = 1;
      tierLabel = "Antares Fixture Sandbox";
      fs = "Read-Only Fixture";
      fsSub = "Target repo checked in read-only mode";
      net = "Loopback Only";
      netSub = "127.0.0.1:8001 Antares completion loop";
    } else if (agent === "security") {
      tier = 2;
      tierLabel = "Security Compute Sandbox";
      fs = "Isolated Analysis VM";
      fsSub = "Ephemeral hypervisor clone with zero host mutation";
      net = "Isolated Bridge";
      netSub = "Strict 1-NIC isolated network with zero external egress";
      approval.push("security_vm_clone", "security_vm_power", "security_vm_destroy", "security_benign_validate", "security_untrusted_execute", "security_vm_cleanup");
    }

    const denied = ["git_push", "pr_create", "deploy", "host_mutate", "rm_rf", "secrets_read"];
    tools.forEach((t) => {
      const name = typeof t === "string" ? t : (t.name || "");
      if (denied.includes(name)) {
        warnings.push("Tool '" + name + "' is permanently denied for automated agents under ADR 0038 / AGENTS.md.");
      }
    });

    return {
      isolation_tier: tier,
      isolation_label: tierLabel,
      filesystem_class: fs,
      filesystem_sub: fsSub,
      network_class: net,
      network_sub: netSub,
      approval_required_tools: approval,
      warnings: warnings,
    };
  }

  function $(id) { return document.getElementById(id); }

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

  function blankDraft(purposeId) {
    const p = PURPOSES.find((x) => x.id === purposeId) || PURPOSES[0];
    const preset = FLEET_PRESETS.find((x) => x.purpose === p.id) || FLEET_PRESETS[0];
    return {
      id: null,
      title: "Custom " + p.label,
      purpose: p.id,
      agent: p.agent,
      role: p.blurb,
      objective: "Help the operator think, build, and research as an intelligent peer.",
      instructions: preset.instructions,
      model: preset.model || "qwen3.6:35b-a3b",
      backend: "ollama",
      tools: preset.tools ? [...preset.tools] : ["memory", "web", "files"],
      skills: [],
      knowledge: "",
      cron: "",
      task: "",
    };
  }

  function fromDefinition(d) {
    const studio = (d.studio && typeof d.studio === "object") ? d.studio : {};
    return {
      id: d.id,
      title: d.title || "Custom Agent",
      purpose: studio.purpose || "build",
      agent: d.agent || "coding-assistant",
      role: studio.role || "",
      objective: studio.objective || "",
      instructions: studio.instructions || d.system_prompt || "",
      model: studio.model || "",
      backend: studio.backend || "ollama",
      tools: studio.tools || (Array.isArray(d.tools) ? d.tools : ["files", "git"]),
      skills: studio.skills || [],
      knowledge: studio.knowledge || "",
      cron: d.schedule_cron || studio.cron || "",
      task: studio.task || "",
    };
  }

  function mark() {
    document.querySelectorAll(".studio-link").forEach((btn) => {
      const id = btn.getAttribute("data-studio");
      const on = id === section || (section === "builder" && id === "builder") || (section === "dashboard" && id === "dashboard");
      btn.classList.toggle("active", on);
    });
  }

  async function launchChat(agentName, title) {
    try {
      const conv = await host.api("/v1/conversations", {
        method: "POST",
        body: JSON.stringify({ agent: agentName || "personal", title: title || "" }),
      });
      if (typeof host.loadConversations === "function") {
        await host.loadConversations();
      }
      if (typeof host.openConversation === "function") {
        await host.openConversation(conv.id);
      } else {
        host.state.conversationId = conv.id;
        host.state.conversationAgent = conv.agent || agentName;
        host.setView("chat");
      }
    } catch (e) {
      host.showErr(e);
    }
  }

  /* ------------------- FLEET VIEW ------------------- */
  function renderFleet(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Super Agent Fleet" }),
      el("p", { text: "High-intellect local AI peers powered by Apple Silicon M4. Equipped for memory synthesis, deep web research, sandboxed coding, and live operations." }),
    ]));

    // Core Presets
    root.appendChild(el("div", { class: "studio-h", text: "Core Super Agents" }));
    const grid = el("div", { class: "fleet-grid" });

    FLEET_PRESETS.forEach((preset) => {
      const card = el("article", { class: "fleet-card" });
      const head = el("div", { class: "fleet-header" }, [
        el("div", {}, [
          el("h3", { class: "fleet-title", text: preset.icon + " " + preset.title }),
        ]),
        el("span", { class: "pill on", text: preset.agent }),
      ]);
      card.appendChild(head);
      card.appendChild(el("p", { class: "fleet-blurb", text: preset.blurb }));

      const badges = el("div", { class: "badge-row" });
      preset.tools.forEach((t) => badges.appendChild(el("span", { class: "pill", text: t })));
      badges.appendChild(el("span", { class: "pill on", text: preset.model }));
      const pPost = evaluateDraftPosture(preset);
      badges.appendChild(el("span", { class: "pill", style: "border-color: #38bdf8; color: #38bdf8;", text: "Tier " + pPost.isolation_tier + " · " + pPost.filesystem_class }));
      card.appendChild(badges);

      const actions = el("div", { class: "fleet-actions" });
      actions.appendChild(el("button", {
        class: "btn-action-chat",
        type: "button",
        text: "💬 Chat with " + preset.title.split(" ")[0],
        onclick: () => launchChat(preset.agent, "Chat with " + preset.title),
      }));
      actions.appendChild(el("button", {
        class: "btn-action-edit",
        type: "button",
        text: "⚙️ Configure",
        onclick: () => {
          draft = blankDraft(preset.purpose);
          draft.title = preset.title;
          draft.instructions = preset.instructions;
          draft.tools = [...preset.tools];
          draft.model = preset.model;
          section = "builder";
          render();
        },
      }));
      if (preset.id === "second-brain") {
        actions.appendChild(el("button", {
          class: "btn-action-chat",
          style: "background: color-mix(in srgb, var(--live) 15%, transparent); border-color: color-mix(in srgb, var(--live) 40%, var(--line)); color: var(--ink);",
          type: "button",
          text: "🛡️ Steward Watches",
          onclick: () => {
            if (host && typeof host.setView === "function") {
              host.setView("steward");
            }
          },
        }));
      }
      card.appendChild(actions);
      grid.appendChild(card);
    });
    root.appendChild(grid);

    // Custom Agents Section
    root.appendChild(el("div", { class: "studio-h", text: "Custom Configured Agents" }));
    const defs = host.state.definitions || [];
    const customGrid = el("div", { class: "fleet-grid" });

    if (!defs.length) {
      customGrid.appendChild(el("div", { class: "fleet-card", style: "border-style:dashed;align-items:center;justify-content:center;min-height:140px;" }, [
        el("p", { class: "muted", text: "No custom agents configured yet." }),
        el("button", {
          class: "btn-action-chat",
          style: "max-width:200px;",
          type: "button",
          text: "+ Create Custom Agent",
          onclick: () => openBuilder("second-brain"),
        }),
      ]));
    } else {
      defs.forEach((d) => {
        const studio = d.studio || {};
        const card = el("article", { class: "fleet-card" });
        const head = el("div", { class: "fleet-header" }, [
          el("h3", { class: "fleet-title", text: "🤖 " + (d.title || "Custom Agent") }),
          el("span", { class: "pill on", text: d.agent || "custom" }),
        ]);
        card.appendChild(head);
        card.appendChild(el("p", { class: "fleet-blurb", text: studio.role || d.system_prompt || "Custom configured super agent." }));

        const badges = el("div", { class: "badge-row" });
        (studio.tools || d.tools || []).forEach((t) => badges.appendChild(el("span", { class: "pill", text: typeof t === "string" ? t : t.name })));
        if (studio.model) badges.appendChild(el("span", { class: "pill on", text: studio.model }));
        const pPost = d.security_posture || evaluateDraftPosture(d);
        badges.appendChild(el("span", { class: "pill", style: "border-color: #38bdf8; color: #38bdf8;", text: "Tier " + pPost.isolation_tier + " · " + pPost.filesystem_class }));
        card.appendChild(badges);

        const actions = el("div", { class: "fleet-actions" });
        actions.appendChild(el("button", {
          class: "btn-action-chat",
          type: "button",
          text: "💬 Chat",
          onclick: () => launchChat(d.agent || "personal", "Chat with " + (d.title || "Agent")),
        }));
        actions.appendChild(el("button", {
          class: "btn-action-edit",
          type: "button",
          text: "⚙️ Edit",
          onclick: () => openExisting(d),
        }));
        actions.appendChild(el("button", {
          class: "btn-action-del",
          type: "button",
          text: "🗑",
          title: "Delete",
          onclick: () => removeDefinition(d).catch((e) => host.showErr(e)),
        }));
        card.appendChild(actions);
        customGrid.appendChild(card);
      });
    }
    root.appendChild(customGrid);
  }

  /* ------------------- 1-PAGE CONFIGURATOR ------------------- */
  function renderBuilder(root) {
    if (!draft) draft = blankDraft("second-brain");

    // Header with Back button, Title, and Actions
    const top = el("div", { class: "builder-top" });
    const left = el("div", { style: "flex:1;min-width:0;" });
    left.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => show("dashboard"), text: "← Super Agent Fleet" }));

    const titleInput = el("input", {
      class: "builder-title",
      value: draft.title,
      placeholder: "Agent Name (e.g., Senior Systems Architect)",
    });
    titleInput.addEventListener("input", () => { draft.title = titleInput.value; });
    left.appendChild(titleInput);
    top.appendChild(left);

    const actions = el("div", { class: "builder-actions" });
    actions.appendChild(el("button", {
      class: "studio-new",
      type: "button",
      text: draft.id ? "💾 Save Changes" : "💾 Create Agent",
      onclick: () => saveDraft().catch((e) => host.showErr(e)),
    }));
    actions.appendChild(el("button", {
      class: "studio-link",
      type: "button",
      text: "💬 Chat with Agent",
      onclick: async () => {
        if (!draft.id) await saveDraft();
        await launchChat(draft.agent, "Chat with " + draft.title);
      },
    }));
    if (draft.id) {
      actions.appendChild(el("button", {
        class: "studio-link",
        type: "button",
        text: "🗑 Delete",
        onclick: () => removeDefinition({ id: draft.id, title: draft.title }).catch((e) => host.showErr(e)),
      }));
    }
    top.appendChild(actions);
    root.appendChild(top);

    // 1-Page Form
    const steps = el("div", { class: "step-list" });

    // Archetype Presets
    const presetBox = el("section", { class: "step" });
    presetBox.appendChild(el("div", { class: "n", text: "Quick Archetype Presets" }));
    const pRow = el("div", { class: "purpose-row", style: "margin-top:8px;" });
    PURPOSES.forEach((p) => {
      const isCur = draft.purpose === p.id;
      pRow.appendChild(el("button", {
        type: "button",
        class: isCur ? "on" : "",
        onclick: () => {
          draft.purpose = p.id;
          draft.agent = p.agent;
          const pre = FLEET_PRESETS.find((x) => x.purpose === p.id);
          if (pre) {
            draft.instructions = pre.instructions;
            draft.tools = [...pre.tools];
            if (pre.model) draft.model = pre.model;
          }
          render();
        },
      }, [p.label, el("small", { text: p.blurb })]));
    });
    presetBox.appendChild(pRow);
    steps.appendChild(presetBox);

    // Purpose & Model
    const modelStep = el("section", { class: "step" });
    modelStep.appendChild(el("div", { class: "n", text: "Brain & Reasoning Model" }));

    const mSelect = el("select");
    mSelect.appendChild(el("option", { value: "", text: "Use active session model" }));
    (host.state.choices || []).forEach((c) => {
      const opt = el("option", {
        value: c.backend + "::" + c.model,
        text: (c.label || c.model) + (c.billing_class === "local" ? " · local (M4)" : " · API"),
      });
      if ((draft.backend && draft.model && draft.backend === c.backend && draft.model === c.model) || draft.model === c.model) {
        opt.selected = true;
      }
      mSelect.appendChild(opt);
    });
    mSelect.addEventListener("change", () => {
      const [backend, ...rest] = mSelect.value.split("::");
      draft.backend = backend || "ollama";
      draft.model = rest.join("::");
    });
    modelStep.appendChild(el("div", { class: "field", style: "margin-top:8px;" }, [
      el("label", { text: "Local Apple Silicon Model" }),
      mSelect,
      el("p", { class: "note", text: "High-reasoning models like Qwen 3.6 35B and Qwen 3 Coder run locally on host unified memory without latency or API charges." }),
    ]));
    steps.appendChild(modelStep);

    // Capabilities & Tools
    const toolStep = el("section", { class: "step" });
    toolStep.appendChild(el("div", { class: "n", text: "Super Tools & Capabilities" }));
    const toolRow = el("div", { class: "tool-row", style: "margin-top:8px;" });
    AVAILABLE_TOOLS.forEach((t) => {
      const on = (draft.tools || []).includes(t.id);
      toolRow.appendChild(el("button", {
        type: "button",
        class: on ? "on" : "",
        onclick: () => {
          draft.tools = on ? draft.tools.filter((x) => x !== t.id) : draft.tools.concat([t.id]);
          render();
        },
      }, [t.icon + " " + t.label, el("small", { text: t.blurb })]));
    });
    toolStep.appendChild(toolRow);
    steps.appendChild(toolStep);

    // Security & Isolation Posture (IWO-068)
    const secStep = el("section", { class: "step security-posture-box" });
    secStep.appendChild(el("div", { class: "n", text: "🛡️ Effective Security & Isolation Posture" }));

    const posture = evaluateDraftPosture(draft);
    const secContent = el("div", { style: "margin-top:10px;" });

    const pGrid = el("div", { class: "posture-metrics-grid" });
    pGrid.appendChild(el("div", { class: "posture-card" }, [
      el("div", { class: "posture-label", text: "Isolation Tier" }),
      el("div", { class: "posture-val", text: "Tier " + posture.isolation_tier }),
      el("div", { class: "posture-sub", text: posture.isolation_label }),
    ]));
    pGrid.appendChild(el("div", { class: "posture-card" }, [
      el("div", { class: "posture-label", text: "Filesystem Class" }),
      el("div", { class: "posture-val", text: posture.filesystem_class }),
      el("div", { class: "posture-sub", text: posture.filesystem_sub }),
    ]));
    pGrid.appendChild(el("div", { class: "posture-card" }, [
      el("div", { class: "posture-label", text: "Network Class" }),
      el("div", { class: "posture-val", text: posture.network_class }),
      el("div", { class: "posture-sub", text: posture.network_sub }),
    ]));
    pGrid.appendChild(el("div", { class: "posture-card" }, [
      el("div", { class: "posture-label", text: "Human Approval Gate" }),
      el("div", { class: "posture-val", text: posture.approval_required_tools.length ? "Enforced" : "Not Required" }),
      el("div", { class: "posture-sub", text: posture.approval_required_tools.length ? posture.approval_required_tools.join(", ") : "Read-only operations" }),
    ]));
    secContent.appendChild(pGrid);

    const policyBanner = el("div", { class: "posture-policy-banner", style: "margin-top:12px;" }, [
      el("div", { class: "posture-banner-title", text: "Enforced Policy vs Draft Intent" }),
      el("p", { class: "note", text: "The runtime strictly enforces boundaries from agents/" + draft.agent + "/policy.json. Tool requests outside the policy ceiling or mutative actions without human approval are blocked." }),
    ]);
    secContent.appendChild(policyBanner);

    if (posture.warnings && posture.warnings.length) {
      const warnBox = el("div", { class: "posture-warnings", style: "margin-top:10px;" });
      posture.warnings.forEach((w) => {
        warnBox.appendChild(el("div", { class: "warn-pill", text: "⚠️ " + w }));
      });
      secContent.appendChild(warnBox);
    }
    secStep.appendChild(secContent);
    steps.appendChild(secStep);

    // System Instructions
    const promptStep = el("section", { class: "step" });
    promptStep.appendChild(el("div", { class: "n", text: "System Instructions & Behavioral Rules" }));
    const promptArea = el("textarea", { rows: "8", style: "margin-top:8px;" });
    promptArea.value = draft.instructions || "";
    promptArea.placeholder = "Define how this agent should think, reason, and interact...";
    promptArea.addEventListener("input", () => { draft.instructions = promptArea.value; });
    promptStep.appendChild(promptArea);
    steps.appendChild(promptStep);

    // Specialized Knowledge & Cron
    const extraStep = el("section", { class: "step" });
    extraStep.appendChild(el("div", { class: "n", text: "Knowledge Context & Automation (Optional)" }));
    const knowArea = el("textarea", { rows: "3", style: "margin-top:8px;" });
    knowArea.value = draft.knowledge || "";
    knowArea.placeholder = "Key repositories, architecture guidelines, or specific domains to focus on...";
    knowArea.addEventListener("input", () => { draft.knowledge = knowArea.value; });
    extraStep.appendChild(el("div", { class: "field" }, [el("label", { text: "Specialized Context" }), knowArea]));

    const cronInput = el("input", { type: "text", value: draft.cron || "", placeholder: "e.g. 0 9 * * * (Daily 9 AM)" });
    cronInput.addEventListener("input", () => { draft.cron = cronInput.value; });
    extraStep.appendChild(el("div", { class: "field" }, [el("label", { text: "Schedule (Cron Expression)" }), cronInput]));
    steps.appendChild(extraStep);

    // Live Execution Section
    const runBox = el("section", { class: "step" });
    runBox.appendChild(el("div", { class: "n", text: "Trigger Autonomous Background Task" }));
    const taskArea = el("textarea", { rows: "3", style: "margin-top:8px;" });
    taskArea.value = draft.task || "";
    taskArea.placeholder = "Describe the task to execute in the background...";
    taskArea.addEventListener("input", () => { draft.task = taskArea.value; });
    runBox.appendChild(taskArea);

    const runActions = el("div", { class: "builder-actions", style: "margin-top:12px;" });
    if (draft.purpose === "build") {
      runActions.appendChild(el("button", {
        class: "studio-link",
        type: "button",
        text: "Prepare Worktree Sandbox",
        onclick: () => prepareCopy().catch((e) => host.showErr(e)),
      }));
    }
    runActions.appendChild(el("button", {
      class: "studio-new",
      type: "button",
      text: "⚡ Run Background Task",
      onclick: () => runDraft().catch((e) => host.showErr(e)),
    }));
    runBox.appendChild(runActions);
    if (host.state.worktreeId) {
      runBox.appendChild(el("p", { class: "note", text: "Active worktree sandbox: " + host.state.worktreeId }));
    }
    steps.appendChild(runBox);

    root.appendChild(steps);
  }

  /* ------------------- WORKFLOWS VIEW ------------------- */
  function renderWorkflows(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Workflows & Skills" }),
      el("p", { text: "Orchestrate multi-step pipelines and attach specialized skills to your super agent fleet." }),
    ]));

    root.appendChild(el("div", { class: "studio-h", text: "Workflow Patterns" }));
    const wfGrid = el("div", { class: "fleet-grid" });

    [
      {
        title: "Autonomous SDLC Pipeline",
        icon: "🔄",
        blurb: "1. Spec Architecture → 2. Create Worktree Sandbox → 3. Implement Code → 4. Diff Review → 5. Human Approval Gate.",
        tag: "Active",
      },
      {
        title: "Daily Second Brain Digest",
        icon: "🧠",
        blurb: "1. Query Memory Vault → 2. Deep Web Research on Topics → 3. Compile Executive Sourced Report.",
        tag: "Active",
      },
      {
        title: "Security & Repo Audit",
        icon: "🛡️",
        blurb: "1. Scan for leaked secrets → 2. Run validate-repo.sh & preflight.sh → 3. Report test coverage.",
        tag: "Active",
      },
    ].forEach((wf) => {
      const card = el("article", { class: "fleet-card" }, [
        el("div", { class: "fleet-header" }, [
          el("h3", { class: "fleet-title", text: wf.icon + " " + wf.title }),
          el("span", { class: "pill on", text: wf.tag }),
        ]),
        el("p", { class: "fleet-blurb", text: wf.blurb }),
      ]);
      wfGrid.appendChild(card);
    });
    root.appendChild(wfGrid);

    root.appendChild(el("div", { class: "studio-h", text: "Skill Catalog" }));
    SKILLS.forEach((grp) => {
      root.appendChild(el("div", { class: "studio-h", style: "font-size:11px;margin-top:12px;", text: grp.group }));
      const sGrid = el("div", { class: "lib-grid" });
      grp.items.forEach(([name, blurb]) => {
        sGrid.appendChild(el("button", {
          class: "lib-card",
          type: "button",
          onclick: () => {
            if (!draft) draft = blankDraft("second-brain");
            if (!draft.skills.includes(name)) draft.skills.push(name);
            draft.instructions = (draft.instructions ? draft.instructions + "\n" : "") + "Skill: " + name + ". " + blurb;
            section = "builder";
            render();
          },
        }, [
          el("strong", { text: name }),
          el("span", { text: blurb }),
          el("div", { class: "badge-row" }, [el("span", { class: "pill on", text: "+ Attach to Agent" })]),
        ]));
      });
      root.appendChild(sGrid);
    });
  }

  /* ------------------- RUNS & APPROVALS VIEW ------------------- */
  function renderRuns(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Live Runs & Approvals" }),
      el("p", { text: "Background tasks running on the Mac mini host. Inspect live reasoning traces and approve gated actions." }),
    ]));

    const runs = host.state.runs || [];
    if (!runs.length) {
      root.appendChild(el("p", { class: "muted", text: "No runs yet. Trigger a task from the configurator or chat." }));
      return;
    }

    runs.forEach((run) => {
      const isPending = run.status === "waiting_for_approval";
      const row = el("button", {
        class: "run-row",
        type: "button",
        style: isPending ? "border-color:#e8b45c;" : "",
        onclick: () => host.openRun(run.id).catch((e) => host.showErr(e)),
      }, [
        el("div", {}, [
          el("strong", { text: run.objective || "Task: " + run.id }),
          el("div", { class: "badge-row", style: "margin-top:4px;" }, [
            el("span", { class: "pill", text: run.agent || "agent" }),
            el("span", { class: "pill", text: run.model || "local" }),
          ]),
        ]),
        el("span", { class: isPending ? "pill later" : "pill on", text: run.status || "" }),
      ]);
      root.appendChild(row);
    });
  }

  function traceLabel(trace) {
    if (trace.kind === "model_call") return "🧠 Model Inference";
    if (trace.kind === "model_wait") return "⏳ Waiting";
    if (trace.kind === "tool_result") return "🛠️ Tool: " + (trace.tool || "call");
    if (trace.kind === "final") return "✅ Complete";
    return trace.kind || "Step";
  }

  function traceBody(trace) {
    if (trace.kind === "tool_result") return (trace.ok ? "Success" : "Failed") + "\n" + (trace.observation || "");
    return trace.text || trace.observation || "";
  }

  function renderRun(root) {
    const run = currentRun;
    if (!run) {
      renderRuns(root);
      return;
    }

    root.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => show("runs"), text: "← Runs & Approvals" }));
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Task Detail" }),
      el("p", { text: run.objective || run.id || "" }),
    ]));

    const meta = el("div", { class: "badge-row" });
    meta.appendChild(el("span", { class: run.status === "waiting_for_approval" ? "pill later" : "pill on", text: run.status || "running" }));
    if (run.model) meta.appendChild(el("span", { class: "pill", text: run.model }));
    if (run.backend) meta.appendChild(el("span", { class: "pill", text: run.backend }));
    root.appendChild(meta);

    if (run.error) root.appendChild(el("p", { class: "muted", style: "color:#ff6b7a;", text: run.error }));

    // Approval Box if pending
    if (run.pending_action) {
      const box = el("div", { class: "run-box", style: "border-color:#e8b45c;margin-top:16px;" });
      box.appendChild(el("div", { class: "studio-h", style: "color:#e8b45c;", text: "⚠️ Human-In-The-Loop Approval Required" }));
      box.appendChild(el("pre", { style: "background:#111;padding:12px;border-radius:8px;overflow:auto;font-size:12px;", text: JSON.stringify(run.pending_action, null, 2) }));
      const row = el("div", { class: "builder-actions", style: "margin-top:12px;" });
      row.appendChild(el("button", { class: "studio-new", type: "button", onclick: () => decide("approved"), text: "✓ Approve Action" }));
      row.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => decide("denied"), text: "✗ Reject Action" }));
      box.appendChild(row);
      root.appendChild(box);
    }

    // Traces Timeline
    const list = el("div", { class: "timeline" });
    const traces = run.traces || [];
    if (!traces.length) list.appendChild(el("p", { class: "muted", text: "Task queued. Waiting for worker step..." }));
    traces.forEach((trace, index) => {
      const open = openStep === index;
      const step = el("button", {
        class: "tl-step",
        type: "button",
        onclick: () => { openStep = open ? -1 : index; render(); },
      }, [
        el("div", { class: "when", text: traceLabel(trace) }),
        el("div", { class: "what", text: (traceBody(trace) || "").replace(/\s+/g, " ").slice(0, 200) }),
      ]);
      if (open) step.appendChild(el("div", { class: "tl-detail", text: traceBody(trace) }));
      list.appendChild(step);
    });
    root.appendChild(list);

    const actions = el("div", { class: "builder-actions", style: "margin-top:16px;" });
    actions.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => act("cancel"), text: "Cancel Run" }));
    actions.appendChild(el("button", { class: "studio-link", type: "button", onclick: () => act("retry"), text: "Retry Run" }));
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

  async function prepareCopy() {
    const created = await host.api("/v1/coding/worktrees", { method: "POST", body: "{}" });
    host.state.worktreeId = created.id || "";
    host.showErr("");
    render();
  }

  async function runDraft() {
    if (!draft.id) await saveDraft();
    const choice = draft.model
      ? { model: draft.model, backend: draft.backend || "ollama", billing_class: "local" }
      : host.selectedChoice();
    const run = await host.api("/v1/agent-definitions/" + draft.id + "/runs", {
      method: "POST",
      body: JSON.stringify({
        objective: (draft.task || "").trim() || draft.title || "Execute configured objective.",
        model: choice.model || "qwen3.6:35b-a3b",
        billing_class: choice.billing_class || "local",
        backend: choice.backend || "ollama",
        max_steps: 10,
        worktree_id: draft.purpose === "build" && host.state.worktreeId ? host.state.worktreeId : "",
      }),
    });
    host.showRun(run);
  }

  async function saveDraft() {
    const p = PURPOSES.find((x) => x.id === draft.purpose) || PURPOSES[0];
    draft.agent = p.agent;
    const studio = Object.assign({}, draft);
    delete studio.id;
    delete studio.task;

    const body = {
      title: draft.title || "Custom Agent",
      agent: draft.agent,
      system_prompt: draft.instructions || "",
      tools: draft.tools || [],
      mcp_server_ids: [],
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

  async function removeDefinition(d) {
    if (!d || !d.id) return;
    if (!window.confirm("Delete " + (d.title || "this agent") + "?")) return;
    await host.api("/v1/agent-definitions/" + d.id, { method: "DELETE" });
    if (draft && draft.id === d.id) draft = null;
    await host.loadDefinitions();
    host.showErr("");
    show("dashboard");
  }

  function openBuilder(purposeId) {
    draft = blankDraft(purposeId || "second-brain");
    section = "builder";
    host.setView("agent");
  }

  function openExisting(d) {
    draft = fromDefinition(d);
    section = "builder";
    host.state.definitionId = d.id;
    host.setView("agent");
  }

  const PAGES = {
    dashboard: renderFleet,
    agents: renderFleet,
    fleet: renderFleet,
    templates: renderFleet,
    builder: renderBuilder,
    workflows: renderWorkflows,
    skills: renderWorkflows,
    tools: renderWorkflows,
    knowledge: renderWorkflows,
    memory: renderWorkflows,
    runs: renderRuns,
    run: renderRun,
    evaluations: renderRuns,
    permissions: renderPermissions,
    published: renderFleet,
  };

  /* ------------------- PERMISSIONS & SECURITY POSTURE VIEW (IWO-068) ------------------- */
  function renderPermissions(root) {
    root.appendChild(el("div", { class: "studio-hero" }, [
      el("h1", { text: "Fleet Security Posture & Permissions" }),
      el("p", { text: "Real-time governance, isolation tiers, and approval ceilings across AI Lab agent archetypes and custom definitions." }),
    ]));

    root.appendChild(el("div", { class: "studio-h", text: "Enforced Security Boundaries" }));
    const tableWrap = el("div", { class: "posture-table-wrap" });
    const table = el("table", { class: "posture-table" });
    table.innerHTML = "<thead><tr>" +
      "<th>Agent Identity</th>" +
      "<th>Isolation Tier</th>" +
      "<th>Filesystem Class</th>" +
      "<th>Network Class</th>" +
      "<th>Allowed Tools</th>" +
      "<th>Approval Gate</th>" +
      "<th>Audit & Events</th>" +
      "</tr></thead><tbody></tbody>";
    const tbody = table.querySelector("tbody");

    const ARCHETYPES = [
      {
        id: "coding-assistant",
        title: "Coding Assistant",
        tier: "Tier 2",
        fs: "Isolated Worktree",
        net: "None (zero egress)",
        allowed: "repo_read, repo_search, git_status, git_diff",
        approval: "apply_patch, git_commit (worktree only)",
        audit: "Active (SecurityEvent)",
      },
      {
        id: "personal",
        title: "Personal / Second Brain",
        tier: "Tier 0",
        fs: "User Vault Scoped (~/.ai-lab)",
        net: "Egress Allowlist (public web)",
        allowed: "vault_read, web_search, nexus_search, files_read, report_write",
        approval: "None (read-only ceiling)",
        audit: "Active (SecurityEvent)",
      },
      {
        id: "research",
        title: "Research Agent",
        tier: "Tier 1",
        fs: "Reports Scoped",
        net: "Egress Allowlist (public web)",
        allowed: "web_search, research, report_write",
        approval: "None (read-only ceiling)",
        audit: "Active (SecurityEvent)",
      },
      {
        id: "lab-operations",
        title: "Lab Operations",
        tier: "Tier 1",
        fs: "Read-Only",
        net: "None (local inspection)",
        allowed: "files_read, lab_health, memory_search",
        approval: "lab_memory_upsert",
        audit: "Active (SecurityEvent)",
      },
      {
        id: "vuln-localize",
        title: "Antares Vuln Localize",
        tier: "Tier 1",
        fs: "Read-Only Fixture",
        net: "Loopback Only (127.0.0.1:8001)",
        allowed: "fixture_read, localize",
        approval: "None (sandbox completions)",
        audit: "Active (SecurityEvent)",
      },
    ];

    ARCHETYPES.forEach((a) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td><strong>" + a.title + "</strong><br><small class='muted'>" + a.id + "</small></td>" +
        "<td><span class='pill on'>" + a.tier + "</span></td>" +
        "<td>" + a.fs + "</td>" +
        "<td>" + a.net + "</td>" +
        "<td><small>" + a.allowed + "</small></td>" +
        "<td>" + (a.approval.includes("None") ? "<small class='muted'>None</small>" : "<span class='pill' style='border-color:var(--warn, #f59e0b);color:var(--warn, #f59e0b);'>" + a.approval + "</span>") + "</td>" +
        "<td><span class='pill on' style='border-color:var(--live, #10b981);color:var(--live, #10b981);'>✓ " + a.audit + "</span></td>";
      tbody.appendChild(tr);
    });

    const defs = host && host.state && host.state.definitions ? host.state.definitions : [];
    defs.forEach((d) => {
      const p = d.security_posture || evaluateDraftPosture(d);
      const tr = document.createElement("tr");
      tr.innerHTML = "<td><strong>🤖 " + (d.title || "Custom Agent") + "</strong><br><small class='muted'>agent: " + (d.agent || "custom") + "</small></td>" +
        "<td><span class='pill on'>Tier " + p.isolation_tier + "</span></td>" +
        "<td>" + p.filesystem_class + "</td>" +
        "<td>" + p.network_class + "</td>" +
        "<td><small>" + ((p.allowed_tools || []).slice(0, 4).join(", ") || "standard") + "</small></td>" +
        "<td>" + ((p.approval_required_tools || []).length ? "<span class='pill' style='border-color:var(--warn, #f59e0b);color:var(--warn, #f59e0b);'>" + p.approval_required_tools.join(", ") + "</span>" : "<small class='muted'>None</small>") + "</td>" +
        "<td><span class='pill on' style='border-color:var(--live, #10b981);color:var(--live, #10b981);'>✓ Active</span></td>";
      tbody.appendChild(tr);
    });

    tableWrap.appendChild(table);
    root.appendChild(tableWrap);
  }

  function render() {
    const root = $("studio-canvas");
    if (!root) return;
    mark();
    const next = document.createElement("div");
    next.className = "studio-page";
    try {
      const page = PAGES[section] || renderFleet;
      page(next);
    } catch (err) {
      next.appendChild(el("p", { class: "muted", text: String(err && err.message || err) }));
    }
    root.replaceChildren(next);
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

  function bindRail() {
    document.querySelectorAll(".studio-link").forEach((btn) => {
      const id = btn.getAttribute("data-studio");
      if (!id) return;
      btn.addEventListener("click", () => show(id));
    });
    const newer = $("studio-new");
    if (newer) newer.addEventListener("click", () => openBuilder("second-brain"));
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
