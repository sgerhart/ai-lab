(function () {
  const path = (window.location.pathname || "/").replace(/\/$/, "") || "/";
  const links = [
    { href: "/", label: "Status", match: /^\/$/ },
    { href: "/lab", label: "Lab", match: /^\/lab$/ },
    { href: "/agents", label: "Studio", match: /^\/agents$/ },
    { href: "/secrets", label: "API keys", match: /^\/secrets$/ },
    { href: "/help", label: "Help", match: /^\/help$/ },
  ];
  const nav = document.createElement("nav");
  nav.className = "ai-lab-topnav";
  nav.setAttribute("aria-label", "Primary");
  nav.innerHTML =
    '<div class="inner">' +
    '<a class="ai-lab-brand" href="/lab">ai-lab · mini</a>' +
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

  window.aiLabAuth = { paste_required: true, mode: "token" };

  window.aiLabHeaders = function () {
    const h = {};
    const t = sessionStorage.getItem("ai_lab_token") || "";
    if (t) h.Authorization = "Bearer " + t;
    return h;
  };

  fetch("/v1/auth/status")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      window.aiLabAuth = d;
      const hint = document.getElementById("ai-lab-auth-hint");
      if (!hint) return;
      if (!d.token_configured) {
        hint.textContent = "API token not configured on mini (fail closed)";
      } else if (d.paste_required) {
        const has = !!(sessionStorage.getItem("ai_lab_token") || "");
        hint.innerHTML = has
          ? "Token in session"
          : 'Token required — see <a href="/help#token">Help</a>';
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
