/**
 * Pull new iCloud books into the local Nexus mirror and add them to the shelf.
 * The static catalog stays as it is. Disk scans only add paths it does not already list.
 */
function labAuthHeaders() {
  const headers = { "Content-Type": "application/json" };
  let token = "";
  try {
    token = sessionStorage.getItem("ai_lab_token") || "";
  } catch (err) {
    token = "";
  }
  if (token) headers.Authorization = "Bearer " + token;
  return headers;
}

function replaceDiskBooks(books) {
  if (typeof CONSOLIDATED_LIBRARY === "undefined") return;
  for (let index = CONSOLIDATED_LIBRARY.length - 1; index >= 0; index -= 1) {
    const id = String(CONSOLIDATED_LIBRARY[index].id || "");
    if (id.indexOf("disk-") === 0) CONSOLIDATED_LIBRARY.splice(index, 1);
  }
  const known = new Set();
  CONSOLIDATED_LIBRARY.forEach((item) => {
    (item.formats || []).forEach((fmt) => known.add(fmt.path));
  });
  (books || []).forEach((book) => {
    const formats = (book.formats || []).filter((fmt) => fmt.path && !known.has(fmt.path));
    if (!formats.length) return;
    formats.forEach((fmt) => known.add(fmt.path));
    CONSOLIDATED_LIBRARY.push({
      id: book.id,
      title: book.title,
      category: book.category,
      desc: book.desc || "",
      formats: formats,
    });
  });
}

function refreshLibraryView() {
  if (typeof updateLibraryFilterCounts === "function") updateLibraryFilterCounts();
  const searchInput = document.getElementById("librarySearchInput");
  const active = document.querySelector("#libraryFilters .filter-pill.active");
  if (typeof renderLibrary === "function") {
    renderLibrary(
      active ? active.getAttribute("data-filter") : "all",
      searchInput ? searchInput.value : ""
    );
  }
}

function syncStatusText(data) {
  const errors = data.errors || [];
  const copied = data.copied || [];
  if (errors.length) return errors[0];
  if (data.note) return data.note;
  if (copied.length) {
    return "Copied " + copied.length + " file" + (copied.length === 1 ? "" : "s") + " from iCloud.";
  }
  return "iCloud already matches this library.";
}

async function loadListedBooks(url) {
  const res = await fetch(url, { headers: labAuthHeaders() });
  if (!res.ok) return false;
  const data = await res.json();
  replaceDiskBooks(data.books || []);
  refreshLibraryView();
  return true;
}

async function applyShelfSummaries() {
  if (typeof CONSOLIDATED_LIBRARY === "undefined") return;
  try {
    const res = await fetch("/v1/nexus/summaries", { headers: labAuthHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    const byPath = new Map();
    (data.summaries || []).forEach((row) => {
      if (row && row.path && row.summary) byPath.set(row.path, row.summary);
    });
    if (!byPath.size) return;
    CONSOLIDATED_LIBRARY.forEach((item) => {
      (item.formats || []).forEach((fmt) => {
        const text = byPath.get(fmt.path);
        if (text) item.desc = text;
      });
    });
    refreshLibraryView();
  } catch (err) {
    // Cards keep their catalog line when summaries are not ready.
  }
}

async function loadDiskLibrary() {
  try {
    if (await loadListedBooks("/v1/nexus/library")) return;
  } catch (err) {
    // The static catalog stays available when the control plane is unreachable.
  }
  try {
    await loadListedBooks("disk-books.json?v=20261017-dlpy");
  } catch (err) {
    // A missing sidecar leaves the catalog as it is.
  }
}

async function syncLibraryFromICloud() {
  const btn = document.getElementById("syncLibraryBtn");
  const status = document.getElementById("syncLibraryStatus");
  if (btn) btn.disabled = true;
  if (status) status.textContent = "Syncing from iCloud…";
  try {
    const res = await fetch("/v1/nexus/sync", {
      method: "POST",
      headers: labAuthHeaders(),
      body: JSON.stringify({ apply: true }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (status) {
        status.textContent = res.status === 401
          ? "Sign in on Studio, then sync again."
          : "Sync is not available on this lab yet.";
      }
      return;
    }
    replaceDiskBooks(data.books || []);
    refreshLibraryView();
    if (status) status.textContent = syncStatusText(data);
  } catch (err) {
    if (status) status.textContent = "Could not reach the lab to sync.";
  } finally {
    if (btn) btn.disabled = false;
  }
}

const SHELF_ORDER = [
  ["ai-books", "AI & GenAI"],
  ["python-ds", "Python & Data Science"],
  ["cloud-books", "Cloud & Platform"],
  ["cyber-books", "Cybersecurity"],
  ["papers", "Research Papers"],
  ["courses", "Courses & Bootcamps"],
];

function shelfLabel(category) {
  const known = SHELF_ORDER.find((row) => row[0] === category);
  if (known) return known[1];
  return String(category || "Other").replace(/-/g, " ");
}

function bookCardHtml(item) {
  const formats = item.formats || [];
  const pdfFmt = formats.find((fmt) => fmt.format === "PDF");
  const epubFmt = formats.find((fmt) => fmt.format === "EPUB");
  const fileUrl = typeof getFileUrl === "function" ? getFileUrl : (path) => encodeURI(path);
  const esc = typeof escapeHtml === "function" ? escapeHtml : escapeMatch;
  let formatBadge = "";
  if (pdfFmt && epubFmt) formatBadge = '<span class="badge badge-format-dual">PDF + EPUB</span>';
  else if (pdfFmt) formatBadge = '<span class="badge badge-format-pdf">PDF</span>';
  else if (epubFmt) formatBadge = '<span class="badge badge-format-epub">EPUB</span>';
  else formatBadge = `<span class="badge badge-format">${esc(formats[0] ? formats[0].format : "FILE")}</span>`;

  const primaryObj = pdfFmt || epubFmt || formats[0] || {};
  const primaryPath = primaryObj.path || "";
  const primaryFilename = primaryPath.split("/").pop() || "";
  const coverUrl = primaryPath ? `/v1/nexus/cover?path=${encodeURIComponent(primaryPath)}` : "";

  let actionButtons = "";
  if (pdfFmt) {
    actionButtons += `<button type="button" class="btn-study-copilot" data-title="${esc(item.title)}" data-category="${esc(item.category)}" data-path="${esc(pdfFmt.path)}" title="Open in Split-Screen AI Study Copilot">🎓 Study</button>`;
  }
  if (pdfFmt && epubFmt) {
    actionButtons += `<a href="${fileUrl(pdfFmt.path)}" class="btn-format btn-format-pdf" target="_blank" title="Open PDF">PDF ↗</a><a href="${fileUrl(epubFmt.path)}" class="btn-format btn-format-epub" target="_blank" title="Open EPUB">EPUB ↗</a>`;
  } else if (pdfFmt) {
    actionButtons += `<a href="${fileUrl(pdfFmt.path)}" class="btn-format btn-format-single" target="_blank">PDF ↗</a>`;
  } else if (epubFmt) {
    actionButtons += `<a href="${fileUrl(epubFmt.path)}" class="btn-format btn-format-epub" target="_blank">EPUB ↗</a>`;
  } else if (formats[0]) {
    actionButtons += `<a href="${fileUrl(formats[0].path)}" class="btn-format btn-format-single" target="_blank">Open ↗</a>`;
  }

  const category = String(item.category || "").replace(/-/g, " ");

  return `
    <article class="library-card has-cover" data-id="${esc(item.id || '')}">
      <div class="library-card-cover-col">
        <div class="library-cover-wrap">
          ${coverUrl ? `<img class="library-cover-img" src="${coverUrl}" alt="${esc(item.title)}" loading="lazy" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';" />` : ''}
          <div class="library-cover-fallback" style="${coverUrl ? 'display:none;' : 'display:flex;'}">
            <span class="library-cover-fallback-icon">📚</span>
            <div class="library-cover-fallback-title">${esc(item.title)}</div>
            <span class="library-cover-fallback-cat">${esc(category)}</span>
          </div>
        </div>
      </div>
      <div class="library-card-content">
        <div class="library-card-top">
          <div class="library-card-meta">
            <span class="library-card-category">${esc(category)}</span>
            ${formatBadge}
          </div>
          <h3 class="library-card-title" title="${esc(item.title)}">${esc(item.title)}</h3>
          <p class="library-card-desc">${esc(item.desc || "")}</p>
        </div>
        <div class="library-card-bottom">
          <code class="library-card-filename" title="${esc(primaryFilename)}">${esc(primaryFilename)}</code>
          <div class="library-card-actions">
            ${actionButtons}
          </div>
        </div>
      </div>
    </article>
  `;
}

let nexusViewMode = "grid";
try {
  nexusViewMode = localStorage.getItem("nexus_view_mode") || "grid";
} catch (e) {
  nexusViewMode = "grid";
}

function bindViewModeToggle() {
  const gridBtn = document.getElementById("viewModeGrid");
  const shelvesBtn = document.getElementById("viewModeShelves");
  if (!gridBtn || !shelvesBtn) return;

  function setMode(mode) {
    nexusViewMode = mode;
    try { localStorage.setItem("nexus_view_mode", mode); } catch (e) {}
    if (mode === "grid") {
      gridBtn.classList.add("active");
      shelvesBtn.classList.remove("active");
    } else {
      shelvesBtn.classList.add("active");
      gridBtn.classList.remove("active");
    }
    refreshLibraryView();
  }

  gridBtn.addEventListener("click", () => setMode("grid"));
  shelvesBtn.addEventListener("click", () => setMode("shelves"));

  if (nexusViewMode === "shelves") {
    shelvesBtn.classList.add("active");
    gridBtn.classList.remove("active");
  } else {
    gridBtn.classList.add("active");
    shelvesBtn.classList.remove("active");
  }
}

function renderLibraryShelves(filter, search) {
  const grid = document.getElementById("libraryGrid");
  if (!grid || typeof CONSOLIDATED_LIBRARY === "undefined") return;
  const query = String(search || "").toLowerCase().trim();
  const active = filter || "all";
  const matched = CONSOLIDATED_LIBRARY.filter((item) => {
    if (active !== "all" && item.category !== active) return false;
    if (!query) return true;
    const title = String(item.title || "").toLowerCase();
    const desc = String(item.desc || "").toLowerCase();
    const pathHit = (item.formats || []).some((fmt) => String(fmt.path || "").toLowerCase().includes(query));
    return title.includes(query) || desc.includes(query) || pathHit;
  });
  if (!matched.length) {
    grid.classList.remove("is-shelves");
    grid.classList.add("is-grid");
    grid.innerHTML = '<div class="library-empty"><p>No books match that search.</p></div>';
    return;
  }
  if (nexusViewMode === "grid" || active !== "all") {
    grid.classList.remove("is-shelves");
    grid.classList.add("is-grid");
    grid.innerHTML = matched.map(bookCardHtml).join("");
    return;
  }
  grid.classList.remove("is-grid");
  grid.classList.add("is-shelves");
  const groups = new Map();
  matched.forEach((item) => {
    const key = item.category || "other";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  });
  const ordered = [];
  SHELF_ORDER.forEach((row) => {
    if (groups.has(row[0])) ordered.push(row[0]);
  });
  groups.forEach((_books, key) => {
    if (ordered.indexOf(key) === -1) ordered.push(key);
  });
  grid.innerHTML = ordered.map((key) => {
    const books = groups.get(key);
    const label = shelfLabel(key);
    return `<section class="book-shelf"><div class="book-shelf-head"><h2>${escapeMatch(label)}</h2><span class="book-shelf-count">${books.length}</span><button type="button" class="shelf-scroll" data-dir="prev" aria-label="Scroll ${escapeMatch(label)} back">‹</button><button type="button" class="shelf-scroll" data-dir="next" aria-label="Scroll ${escapeMatch(label)} forward">›</button></div><div class="book-shelf-row">${books.map(bookCardHtml).join("")}</div></section>`;
  }).join("");
  window.requestAnimationFrame(updateShelfButtons);
}

function updateShelfButtons() {
  document.querySelectorAll(".book-shelf").forEach((shelf) => {
    const row = shelf.querySelector(".book-shelf-row");
    const overflow = Boolean(row) && row.scrollWidth > row.clientWidth + 8;
    shelf.querySelectorAll(".shelf-scroll").forEach((btn) => {
      btn.hidden = !overflow;
    });
  });
}

function bindShelfScroll() {
  const grid = document.getElementById("libraryGrid");
  if (!grid || grid.dataset.shelves) return;
  grid.dataset.shelves = "1";
  grid.addEventListener("click", (event) => {
    const btn = event.target.closest(".shelf-scroll");
    if (!btn) return;
    const row = btn.closest(".book-shelf") && btn.closest(".book-shelf").querySelector(".book-shelf-row");
    if (!row) return;
    const direction = btn.getAttribute("data-dir") === "prev" ? -1 : 1;
    row.scrollBy({ left: direction * Math.max(280, row.clientWidth * 0.8), behavior: "smooth" });
  });
  window.addEventListener("resize", updateShelfButtons);
}

function escapeMatch(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));
}

function renderBookMatches(books) {
  const host = document.getElementById("nexusBookMatches");
  if (!host) return;
  if (!books || !books.length) {
    host.hidden = true;
    host.innerHTML = "";
    return;
  }
  const rows = books.map((book) => {
    const path = book.path || "";
    const where = book.chapter ? escapeMatch(book.chapter) + ". " : "";
    const open = path
      ? `<a href="${encodeURI(path)}" target="_blank" rel="noopener">Open</a>`
      : "";
    return `<article class="book-match"><div><h3>${escapeMatch(book.title)}</h3><p>${where}${escapeMatch(book.snippet || "")}</p>${open}</div></article>`;
  }).join("");
  host.hidden = false;
  host.innerHTML = `<p class="book-matches-label">Books that can help</p>${rows}`;
}

let bookSearchTimer = 0;

async function findHelpfulBooks(query) {
  const q = (query || "").trim();
  if (q.length < 3) {
    renderBookMatches([]);
    return;
  }
  try {
    const res = await fetch("/v1/nexus/search?q=" + encodeURIComponent(q), { headers: labAuthHeaders() });
    if (!res.ok) {
      renderBookMatches([]);
      return;
    }
    const data = await res.json();
    renderBookMatches(data.books || []);
  } catch (err) {
    renderBookMatches([]);
  }
}

function bindHelpfulBookSearch() {
  const input = document.getElementById("librarySearchInput");
  if (!input || input.dataset.nexusSearch) return;
  input.dataset.nexusSearch = "1";
  input.addEventListener("input", () => {
    window.clearTimeout(bookSearchTimer);
    const value = input.value;
    bookSearchTimer = window.setTimeout(() => findHelpfulBooks(value), 350);
  });
  const clearBtn = document.getElementById("clearSearchBtn");
  if (clearBtn) clearBtn.addEventListener("click", () => renderBookMatches([]));
}

function initLibrarySync() {
  bindShelfScroll();
  bindViewModeToggle();
  renderLibrary = renderLibraryShelves;
  bindHelpfulBookSearch();
  const btn = document.getElementById("syncLibraryBtn");
  if (btn) btn.addEventListener("click", syncLibraryFromICloud);
  loadDiskLibrary();
  applyShelfSummaries();
  const view = document.getElementById("viewLibrary");
  if (view && view.classList.contains("active")) renderLibraryShelves("all", "");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLibrarySync);
} else {
  initLibrarySync();
}
