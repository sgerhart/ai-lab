(function () {
  const path = (window.location.pathname || "/").replace(/\/$/, "") || "/";
  const links = [
    { href: "/", label: "AI Lab", match: /^\/$/ },
    { href: "/antares", label: "Antares", match: /^\/antares$/ },
    { href: "/secrets", label: "API keys", match: /^\/secrets$/ },
    { href: "/help", label: "Help", match: /^\/help$/ },
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
        const active = l.match.test(path) ? " active" : "";
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
      "<h2>Sign in</h2>" +
      "<p>Personal lab — username and password for this operator only.</p>" +
      '<label for="ai-lab-login-user">Username</label>' +
      '<input id="ai-lab-login-user" autocomplete="username" />' +
      '<label for="ai-lab-login-pass">Password</label>' +
      '<input id="ai-lab-login-pass" type="password" autocomplete="current-password" />' +
      '<button type="button" id="ai-lab-login-submit">Sign in</button>' +
      '<p class="ai-lab-login-err" id="ai-lab-login-err"></p>' +
      "</div>";
    document.body.appendChild(wrap);

    if (!document.getElementById("ai-lab-login-style")) {
      const st = document.createElement("style");
      st.id = "ai-lab-login-style";
      st.textContent =
        "#ai-lab-login-modal{position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.55);" +
        "display:flex;align-items:center;justify-content:center;padding:16px}" +
        "#ai-lab-login-modal[hidden]{display:none}" +
        ".ai-lab-login-card{width:min(380px,100%);background:#1a1a1a;color:#ececec;" +
        "border:1px solid #333;border-radius:16px;padding:20px;font:14px/1.4 system-ui,sans-serif}" +
        ".ai-lab-login-card h2{margin:0 0 6px;font-size:20px}" +
        ".ai-lab-login-card p{margin:0 0 12px;color:#afafaf;font-size:13px}" +
        ".ai-lab-login-card label{display:block;font-size:12px;color:#afafaf;margin:8px 0 4px}" +
        ".ai-lab-login-card input{width:100%;box-sizing:border-box;background:#111;border:1px solid #333;" +
        "color:#ececec;border-radius:10px;padding:10px 12px;font:inherit}" +
        ".ai-lab-login-card button{margin-top:12px;width:100%;border:0;border-radius:10px;" +
        "padding:10px;background:#10a37f;color:#04140f;font:inherit;font-weight:650;cursor:pointer}" +
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
      if (!d.auth_ready) {
        hint.textContent = "Auth not configured on mini";
      } else if (has) {
        hint.textContent = "Signed in";
      } else if (d.login_required || d.login_available || d.paste_required) {
        hint.textContent = "Sign in required";
        ensureLoginModal();
        document.getElementById("ai-lab-login-modal").hidden = false;
      } else {
        hint.textContent = "Auth ready";
      }
      document.dispatchEvent(new CustomEvent("ai-lab-auth-ready", { detail: d }));
    })
    .catch(function () {
      const hint = document.getElementById("ai-lab-auth-hint");
      if (hint) hint.textContent = "Auth status unavailable";
    });
})();
