(function () {
  const path = (window.location.pathname || "/").replace(/\/$/, "") || "/";
  const search = window.location.search || "";
  const isAntares = /open=antares/.test(search) || /^\/antares/.test(path);
  const links = [
    { href: "/", label: "Studio", active: path === "/" && !isAntares },
    { href: "/nexus/", label: "📚 Nexus", active: /^\/nexus/.test(path) },
    { href: "/classroom", label: "Classroom", active: /^\/classroom$/.test(path) },
    { href: "/steward", label: "Steward", active: /^\/steward$/.test(path) },
    { href: "/?open=antares", label: "Antares", active: isAntares },
    { href: "/secrets", label: "API keys", active: /^\/secrets$/.test(path) },
    { href: "/help", label: "Help", active: /^\/help$/.test(path) },
  ];
  const nav = document.createElement("nav");
  nav.className = "ai-lab-topnav";
  nav.setAttribute("aria-label", "Primary");
  nav.innerHTML =
    '<div class="inner">' +
    '<a class="ai-lab-brand" href="/"><img class="ai-lab-mark" src="/static/ai-lab-icon.jpg" alt="">AI Lab</a>' +
    '<div class="ai-lab-links">' +
    links
      .map(function (l) {
        const active = l.active ? " active" : "";
        return '<a class="' + active.trim() + '" href="' + l.href + '">' + l.label + "</a>";
      })
      .join("") +
    "</div>" +
    '<div class="ai-lab-token-hint" id="ai-lab-auth-hint">Checking auth…</div>' +
    "</div>";
  document.body.insertBefore(nav, document.body.firstChild);

  window.aiLabAuth = { paste_required: true, login_required: false, mode: "token" };

  window.aiLabHeaders = function () {
    const h = {};
    const t = sessionStorage.getItem("ai_lab_token") || "";
    if (t) h.Authorization = "Bearer " + t;
    return h;
  };

  function ensureLoginModal() {
    if (document.getElementById("ai-lab-login-modal")) return;
    const wrap = document.createElement("div");
    wrap.id = "ai-lab-login-modal";
    wrap.setAttribute("data-auth-panel", "1");
    wrap.hidden = true;
    wrap.innerHTML =
      '<div class="ai-lab-login-card">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">' +
      '<h2 style="margin:0">Sign in</h2>' +
      '<button type="button" id="ai-lab-login-close" style="background:transparent;border:0;color:#888;font-size:18px;cursor:pointer;width:auto;padding:0;margin:0">&times;</button>' +
      '</div>' +
      "<p>Personal lab — username and password for this operator only.</p>" +
      '<label for="ai-lab-login-user">Username</label>' +
      '<input id="ai-lab-login-user" autocomplete="username" />' +
      '<label for="ai-lab-login-pass">Password</label>' +
      '<input id="ai-lab-login-pass" type="password" autocomplete="current-password" />' +
      '<button type="button" id="ai-lab-login-submit">Sign in</button>' +
      '<p class="ai-lab-login-err" id="ai-lab-login-err"></p>' +
      "</div>";
    document.body.appendChild(wrap);

    wrap.addEventListener("click", function (e) {
      if (e.target === wrap) wrap.hidden = true;
    });

    document.getElementById("ai-lab-login-close").onclick = function () {
      wrap.hidden = true;
    };

    if (!document.getElementById("ai-lab-login-style")) {
      const st = document.createElement("style");
      st.id = "ai-lab-login-style";
      st.textContent =
        "#ai-lab-login-modal{position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.55);" +
        "display:flex;align-items:center;justify-content:center;padding:16px}" +
        "#ai-lab-login-modal[hidden]{display:none!important}" +
        ".ai-lab-login-card{width:min(380px,100%);background:#1a1a1a;color:#ececec;" +
        "border:1px solid #333;border-radius:16px;padding:20px;font:14px/1.4 system-ui,sans-serif}" +
        ".ai-lab-login-card h2{margin:0 0 6px;font-size:20px}" +
        ".ai-lab-login-card p{margin:0 0 12px;color:#afafaf;font-size:13px}" +
        ".ai-lab-login-card label{display:block;font-size:12px;color:#afafaf;margin:8px 0 4px}" +
        ".ai-lab-login-card input{width:100%;box-sizing:border-box;background:#111;border:1px solid #333;" +
        "color:#ececec;border-radius:10px;padding:10px 12px;font:inherit}" +
        ".ai-lab-login-card button{margin-top:12px;width:100%;border:0;border-radius:10px;" +
        "padding:10px;background:#7cb8ff;color:#061018;font:inherit;font-weight:650;cursor:pointer}" +
        ".ai-lab-login-err{color:#ff6b7a;min-height:1.2em;margin-top:8px!important}";
      document.head.appendChild(st);
    }

    document.getElementById("ai-lab-login-submit").onclick = function () {
      const user = document.getElementById("ai-lab-login-user").value.trim();
      const pass = document.getElementById("ai-lab-login-pass").value;
      const err = document.getElementById("ai-lab-login-err");
      err.textContent = "";
      fetch("/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user, password: pass }),
      })
        .then(function (r) {
          return r.text().then(function (t) {
            var body;
            try { body = JSON.parse(t); } catch (e) { body = { detail: t }; }
            if (!r.ok) throw new Error(body.detail || r.statusText);
            return body;
          });
        })
        .then(function (body) {
          sessionStorage.setItem("ai_lab_token", body.token || "");
          wrap.hidden = true;
          document.dispatchEvent(new CustomEvent("ai-lab-auth-ready", { detail: window.aiLabAuth }));
          window.location.reload();
        })
        .catch(function (e) {
          err.textContent = String(e.message || e);
        });
    };
  }

  fetch("/v1/auth/status")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      window.aiLabAuth = d;
      const hint = document.getElementById("ai-lab-auth-hint");
      const has = !!(sessionStorage.getItem("ai_lab_token") || "");
      if (!hint) return;
      hint.style.cursor = "pointer";
      hint.onclick = function () {
        ensureLoginModal();
        const m = document.getElementById("ai-lab-login-modal");
        if (m) m.hidden = !m.hidden;
      };
      if (!d.auth_ready) {
        hint.textContent = "Auth not configured on mini";
      } else if (has) {
        hint.textContent = "Signed in";
      } else if (d.login_required || d.login_available || d.paste_required) {
        hint.textContent = "Sign in (optional)";
      } else {
        hint.textContent = "Auth ready";
      }
      document.dispatchEvent(new CustomEvent("ai-lab-auth-ready", { detail: d }));
    })
    .catch(function () {
      const hint = document.getElementById("ai-lab-auth-hint");
      if (hint) hint.textContent = "Auth status unavailable";
    });

  // Reuse one tab per name. The Python Lab tab is "ai-lab-jupyter".
  // R uses its own name so it does not just focus the Python tab.
  // A new about:blank tab is the first open; a later click only focuses.
  window.aiLabOpenOnce = function (url, windowName) {
    const name = windowName || "ai-lab-jupyter";
    const heldMap = window.aiLabHeldWindows || (window.aiLabHeldWindows = {});
    const held = heldMap[name];
    if (held && held.closed === false) {
      held.focus();
      return true;
    }
    const win = window.open("", name);
    if (!win) return false;
    heldMap[name] = win;
    if (name === "ai-lab-jupyter") window.aiLabJupyterWindow = win;
    try {
      if (!win.location.href || win.location.href === "about:blank") {
        win.location.href = url;
      }
    } catch (_) {
      // The tab is already on Studio Jupyter, a different origin.
    }
    win.focus();
    return true;
  };
})();
