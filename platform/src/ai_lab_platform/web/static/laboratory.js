// AI Laboratory Workbench Reactive Controller (IWO-129)
(function () {
  let paradigms = [];
  let concepts = [];
  let activeParadigm = "all";
  let activeConceptId = "vector-geometry-cosine";
  let conversationHistory = [];

  const paradigmListEl = document.getElementById("paradigmList");
  const conceptListEl = document.getElementById("conceptList");
  const conceptSearchEl = document.getElementById("conceptSearch");
  const catalogCountBadge = document.getElementById("catalogCountBadge");

  const benchHeaderTitle = document.getElementById("benchHeaderTitle");
  const sciFocusTag = document.getElementById("sciFocusTag");
  const benchTitleEl = document.getElementById("benchTitle");
  const benchSummaryEl = document.getElementById("benchSummary");
  const benchParadigmEl = document.getElementById("benchParadigm");
  const benchTensorFlowEl = document.getElementById("benchTensorFlow");
  const benchFormulaEl = document.getElementById("benchFormula");
  const benchVarsEl = document.getElementById("benchVars");
  const benchMathExplanationEl = document.getElementById("benchMathExplanation");
  const benchNumericalEl = document.getElementById("benchNumerical");
  const benchCodeEl = document.getElementById("benchCode");
  const benchCitationsEl = document.getElementById("benchCitations");
  const copyCodeBtn = document.getElementById("copyCodeBtn");

  const scientistMessagesEl = document.getElementById("scientistMessages");
  const scientistInputEl = document.getElementById("scientistInput");
  const scientistSendBtn = document.getElementById("scientistSendBtn");

  function authHeaders() {
    return window.aiLabHeaders ? window.aiLabHeaders() : {};
  }

  // 1. Load Catalog
  async function loadCatalog() {
    try {
      const res = await fetch("/v1/lab/catalog");
      if (!res.ok) throw new Error("Catalog fetch failed");
      const data = await res.json();
      paradigms = data.paradigms || [];
      concepts = data.concepts || [];
      renderParadigms();
      renderConcepts();
      if (concepts.length > 0) {
        selectConcept(activeConceptId || concepts[0].id);
      }
    } catch (err) {
      console.error("Error loading lab catalog:", err);
    }
  }

  // 2. Render Paradigms
  function renderParadigms() {
    paradigmListEl.innerHTML = "";
    paradigms.forEach((p) => {
      const btn = document.createElement("button");
      btn.className = "paradigm-pill" + (p.id === activeParadigm ? " active" : "");
      btn.innerHTML = `<span>${p.icon || "•"}</span><span>${p.label}</span>`;
      btn.onclick = () => {
        activeParadigm = p.id;
        renderParadigms();
        renderConcepts();
      };
      paradigmListEl.appendChild(btn);
    });
  }

  // 3. Render Concepts
  function renderConcepts() {
    const q = (conceptSearchEl.value || "").trim().toLowerCase();
    conceptListEl.innerHTML = "";

    const filtered = concepts.filter((c) => {
      const matchParadigm = activeParadigm === "all" || c.paradigm === activeParadigm;
      const matchQuery = !q || c.title.toLowerCase().includes(q) || c.summary.toLowerCase().includes(q);
      return matchParadigm && matchQuery;
    });

    if (catalogCountBadge) {
      catalogCountBadge.textContent = `${filtered.length} Concepts`;
    }

    if (filtered.length === 0) {
      conceptListEl.innerHTML = '<div style="font-size:12px;color:var(--text-muted);padding:12px;text-align:center;">No matching concepts found</div>';
      return;
    }

    filtered.forEach((c) => {
      const div = document.createElement("div");
      div.className = "concept-item" + (c.id === activeConceptId ? " active" : "");
      div.innerHTML = `
        <div class="concept-item-header">
          <span class="concept-item-title">${c.title}</span>
          <span class="concept-item-badge">${c.paradigm}</span>
        </div>
        <div class="concept-item-desc">${c.summary}</div>
      `;
      div.onclick = () => selectConcept(c.id);
      conceptListEl.appendChild(div);
    });
  }

  conceptSearchEl.addEventListener("input", renderConcepts);

  // 4. Select Concept and Render Workbench
  async function selectConcept(conceptId) {
    activeConceptId = conceptId;
    renderConcepts();

    try {
      const res = await fetch(`/v1/lab/concept/${encodeURIComponent(conceptId)}`);
      if (!res.ok) throw new Error("Concept detail fetch failed");
      const c = await res.json();
      renderWorkbench(c);
    } catch (err) {
      console.error("Error loading concept:", err);
    }
  }

  function renderWorkbench(c) {
    if (benchHeaderTitle) benchHeaderTitle.textContent = c.title;
    if (sciFocusTag) sciFocusTag.textContent = c.title;
    benchTitleEl.textContent = c.title;
    benchSummaryEl.textContent = c.summary;
    benchParadigmEl.textContent = c.paradigm.toUpperCase();
    benchTensorFlowEl.textContent = c.tensor_flow;

    // KaTeX Formula
    if (window.katex && c.formula) {
      try {
        window.katex.render(c.formula, benchFormulaEl, { displayMode: true, throwOnError: false });
      } catch (_) {
        benchFormulaEl.textContent = c.formula;
      }
    } else {
      benchFormulaEl.textContent = c.formula;
    }

    // Variables Grid
    benchVarsEl.innerHTML = "";
    if (c.variables) {
      Object.entries(c.variables).forEach(([sym, desc]) => {
        const row = document.createElement("div");
        row.className = "math-var-row";
        row.innerHTML = `<span class="math-var-symbol">${sym}</span><span class="math-var-desc">${desc}</span>`;
        benchVarsEl.appendChild(row);
      });
    }

    // Math mechanism explanation
    benchMathExplanationEl.innerHTML = `<strong>Mechanism Intuition:</strong> ${c.math_explanation}`;

    // Numerical walkthrough
    benchNumericalEl.innerHTML = `<strong>Numerical Walkthrough:</strong><br>${c.numerical_example.replace(/\n/g, "<br>")}`;

    // Code block
    benchCodeEl.textContent = c.code_snippet;

    // Citations
    benchCitationsEl.innerHTML = "";
    if (c.nexus_citations && c.nexus_citations.length > 0) {
      c.nexus_citations.forEach((cit) => {
        const card = document.createElement("div");
        card.className = "citation-card";
        const encodedTitle = encodeURIComponent(cit.title);
        card.innerHTML = `
          <div class="cit-top">
            <div class="cit-title">📖 ${cit.title}</div>
            <span class="concept-item-badge" style="background:rgba(245,158,11,0.1);color:#f59e0b;">${cit.category || 'ai-books'}</span>
          </div>
          <div class="cit-chapter">${cit.chapter}</div>
          <div class="cit-relevance">${cit.relevance}</div>
          <a href="/nexus/?search=${encodedTitle}" target="_blank" class="cit-link-btn">Study in Nexus ↗</a>
        `;
        benchCitationsEl.appendChild(card);
      });
    } else {
      benchCitationsEl.innerHTML = '<div style="font-size:12px;color:var(--text-muted);padding:8px;">No book citations cataloged for this concept yet.</div>';
    }
  }

  // Copy code button with feedback
  copyCodeBtn.onclick = () => {
    navigator.clipboard.writeText(benchCodeEl.textContent);
    copyCodeBtn.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
      <span style="color:#10b981;">Copied!</span>
    `;
    setTimeout(() => {
      copyCodeBtn.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        <span>Copy Code</span>
      `;
    }, 2000);
  };

  // 5. Staff Scientist Peer Dialogue
  async function sendScientistMessage(text) {
    const msg = (text || scientistInputEl.value || "").trim();
    if (!msg) return;

    // Add user message
    appendMessage("user", "Operator", msg);
    scientistInputEl.value = "";
    scientistInputEl.style.height = "38px";
    conversationHistory.push({ role: "user", content: msg });

    // Show typing placeholder
    const typingCard = appendMessage("scientist", "Staff Scientist", "Analyzing at the bench (searching books & literature)...");

    try {
      const res = await fetch("/v1/lab/scientist/chat", {
        method: "POST",
        headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
        body: JSON.stringify({
          message: msg,
          concept_id: activeConceptId,
          history: conversationHistory,
        }),
      });

      if (!res.ok) throw new Error("Staff Scientist response failed (" + res.status + ")");
      const data = await res.json();

      // Replace typing card content
      typingCard.querySelector(".msg-content").innerHTML = formatMarkdown(data.reply);
      conversationHistory.push({ role: "scientist", content: data.reply });

      // Add citation chips if returned
      if (data.citations && data.citations.length > 0) {
        const chipContainer = document.createElement("div");
        chipContainer.style.display = "flex";
        chipContainer.style.flexWrap = "wrap";
        chipContainer.style.gap = "4px";
        chipContainer.style.marginTop = "6px";
        data.citations.slice(0, 3).forEach((cit) => {
          const chip = document.createElement("span");
          chip.className = "msg-citation-chip";
          chip.textContent = `📚 ${cit.title || cit.reference || "Library Citation"}`;
          chipContainer.appendChild(chip);
        });
        typingCard.appendChild(chipContainer);
      }
    } catch (err) {
      typingCard.querySelector(".msg-content").textContent = "Research error: " + err.message;
    }
  }

  function appendMessage(role, author, content) {
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.innerHTML = `
      <span class="msg-author">${author}</span>
      <div class="msg-content">${formatMarkdown(content)}</div>
    `;
    scientistMessagesEl.appendChild(div);
    scientistMessagesEl.scrollTop = scientistMessagesEl.scrollHeight;
    return div;
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let safe = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    // Bold
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Code blocks
    safe = safe.replace(/```([\s\S]*?)```/g, "<pre class='code-box' style='margin:6px 0;padding:8px;font-size:11px;'>$1</pre>");
    // Inline code
    safe = safe.replace(/`([^`]+)`/g, "<code style='background:rgba(255,255,255,0.08);padding:2px 4px;border-radius:4px;'>$1</code>");
    // Newlines
    safe = safe.replace(/\n/g, "<br>");
    return safe;
  }

  scientistSendBtn.onclick = () => sendScientistMessage();
  scientistInputEl.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
  });
  scientistInputEl.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendScientistMessage();
    }
  };

  // Quick buttons
  document.querySelectorAll(".quick-btn").forEach((btn) => {
    btn.onclick = () => {
      const prompt = btn.getAttribute("data-prompt");
      sendScientistMessage(prompt);
    };
  });

  // Initial load
  loadCatalog();
})();
