/* Classroom player: lesson beats, browser voice, and whiteboard marks. */
(function () {
  "use strict";

  const state = {
    lesson: null,
    beats: [],
    index: 0,
    mode: "idle",
    hand: false,
    voice: true,
    queue: [],
    transcript: [],
    after: "stay",
    beatDone: false,
    token: 0,
    askId: 0,
    timers: [],
    scene: [],
    paused: false,
    hold: null,
    talk: null,
    draw: null,
    script: "",
    layout: null,
  };

  const topicForm = document.getElementById("topic-form");
  const topicInput = document.getElementById("topic");
  const startBtn = document.getElementById("start-class");
  const statusEl = document.getElementById("status");
  const planEl = document.getElementById("lesson-plan");
  const captionEl = document.getElementById("caption");
  const pauseBtn = document.getElementById("pause-instructor");
  const handBtn = document.getElementById("raise-hand");
  const voiceBtn = document.getElementById("voice-toggle");
  const questionForm = document.getElementById("question-form");
  const questionInput = document.getElementById("question");
  const askBtn = document.getElementById("ask-question");
  const noteBtn = document.getElementById("pass-note");
  const discussion = document.getElementById("discussion");
  const canvas = document.getElementById("board");

  function setStatus(text) {
    statusEl.textContent = text;
  }

  function headers() {
    const extra = window.aiLabHeaders ? window.aiLabHeaders() : {};
    return Object.assign({ "Content-Type": "application/json" }, extra);
  }

  function halt() {
    state.token += 1;
    state.timers.forEach(function (timer) {
      window.clearTimeout(timer);
    });
    state.timers = [];
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  function jsonBody(response) {
    return response.text().then(function (text) {
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch (err) {
        return { detail: text };
      }
    });
  }

  function errorText(response, body) {
    if (response.status === 401) {
      return "Sign in from the header, then try again.";
    }
    const detail = body && body.detail;
    if (typeof detail === "string" && detail) return detail;
    return "The classroom request failed (" + response.status + ").";
  }

  topicForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const topic = topicInput.value.trim();
    if (!topic) {
      setStatus("Name a topic to start class.");
      topicInput.focus();
      return;
    }
    halt();
    state.paused = false;
    state.hold = null;
    state.askId += 1;
    state.lesson = null;
    state.queue = [];
    state.hand = false;
    syncHand();
    startBtn.disabled = true;
    setStatus("Writing the lesson plan…");
    fetch("/v1/classroom/lessons", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ topic: topic }),
    })
      .then(function (response) {
        return jsonBody(response).then(function (body) {
          if (!response.ok) throw new Error(errorText(response, body));
          return body;
        });
      })
      .then(function (lesson) {
        state.lesson = lesson;
        state.transcript = [];
        discussion.replaceChildren();
        const empty = document.createElement("li");
        empty.className = "empty";
        empty.textContent = "Questions and answers stay in this list.";
        discussion.appendChild(empty);
        state.beats = Array.isArray(lesson.segments) ? lesson.segments : [];
        renderPlan(lesson);
        setAskingEnabled(true);
        if (!state.beats.length) {
          setStatus("The lesson plan has no sections.");
          return;
        }
        playBeat(0);
      })
      .catch(function (err) {
        setStatus(err.message || "The classroom could not start.");
      })
      .then(function () {
        startBtn.disabled = false;
      });
  });

  function renderPlan(lesson) {
    planEl.replaceChildren();
    const title = document.createElement("h2");
    title.textContent = lesson.title || lesson.topic || "Lesson";
    const source = document.createElement("p");
    source.className = "source";
    source.textContent =
      lesson.source === "model"
        ? "The local model wrote this lesson plan."
        : "The local model did not return a plan. This is the classroom outline, and class still runs.";
    const goals = document.createElement("ol");
    (lesson.objectives || []).forEach(function (item) {
      const li = document.createElement("li");
      li.textContent = item;
      goals.appendChild(li);
    });
    const label = document.createElement("p");
    label.className = "plan-label";
    label.textContent = "Lesson";
    planEl.append(title, source, goals, label);
    state.beats.forEach(function (beat, index) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "beat";
      btn.dataset.beat = String(index);
      btn.textContent = beat.title || "Part " + (index + 1);
      btn.addEventListener("click", function () {
        state.hand = false;
        syncHand();
        state.queue = [];
        playBeat(index);
      });
      planEl.appendChild(btn);
    });
  }

  function highlight(index) {
    planEl.querySelectorAll(".beat").forEach(function (btn, i) {
      btn.setAttribute("aria-current", i === index ? "true" : "false");
    });
  }

  function playBeat(index) {
    const beat = state.beats[index];
    if (!beat) return;
    state.paused = false;
    state.hold = null;
    halt();
    const token = state.token;
    state.index = index;
    state.mode = "teaching";
    state.beatDone = false;
    state.script = beat.speech || "";
    highlight(index);
    setStatus("Teaching: " + (beat.title || "lesson"));
    syncPause();
    let speechDone = false;
    let drawDone = false;
    function check() {
      if (token !== state.token || state.paused) return;
      if (speechDone && drawDone) afterBeat();
    }
    speak(beat.speech || "", token, function () {
      speechDone = true;
      check();
    });
    const plan = drawPlan(state.scene, beat.board || [], beat.place || "");
    playOps(plan.ops, token, function () {
      drawDone = true;
      check();
    }, plan.replace, beat.speech || "");
  }

  function afterBeat() {
    state.beatDone = true;
    if (state.hand) {
      state.mode = "paused";
      syncPause();
      setStatus("Hand raised.");
      return;
    }
    if (state.queue.length) {
      state.after = "next";
      askNow(state.queue.shift(), true);
      return;
    }
    if (state.index + 1 < state.beats.length) {
      playBeat(state.index + 1);
      return;
    }
    state.mode = "idle";
    syncPause();
    setStatus("That is the end of the lesson. Ask a question, or start another topic.");
  }

  const NOVELTY = /albert|bad news|bahh|bells|boing|bubbles|cellos|eloquence|good news|zarvox|trinoids|whisper|fred|junior|superstar|kathy|ralph|princess/i;
  const VOICE_RANK = [
    /premium/i,
    /enhanced/i,
    /siri/i,
    /ava \(english \(us\)\)/i,
    /zoe \(english \(us\)\)/i,
    /allison/i,
    /ava/i,
    /zoe/i,
    /flo \(english \(us\)\)/i,
    /eddy \(english \(us\)\)/i,
    /flo \(english \(uk\)\)/i,
    /eddy \(english \(uk\)\)/i,
    /flo/i,
    /eddy/i,
    /samantha/i,
    /nathan/i,
    /nicky/i,
    /daniel/i,
    /karen/i,
    /moira/i,
    /tessa/i,
  ];

  function chooseVoice(voices) {
    const english = (voices || []).filter(function (voice) {
      return /^en/i.test(voice.lang || "") && !NOVELTY.test(voice.name || "");
    });
    for (let i = 0; i < VOICE_RANK.length; i++) {
      const hit = english.find(function (voice) {
        return VOICE_RANK[i].test(voice.name || "");
      });
      if (hit) return hit;
    }
    return english.find(function (voice) {
      return /en[-_]us/i.test(voice.lang || "");
    }) || english[0] || null;
  }

  function withVoices(cb) {
    if (!window.speechSynthesis) {
      cb([]);
      return;
    }
    const ready = window.speechSynthesis.getVoices();
    if (ready.length) {
      cb(ready);
      return;
    }
    let finished = false;
    function finish() {
      if (finished) return;
      finished = true;
      cb(window.speechSynthesis.getVoices());
    }
    window.speechSynthesis.addEventListener("voiceschanged", finish, { once: true });
    window.speechSynthesis.getVoices();
    state.timers.push(window.setTimeout(finish, 400));
  }

  function splitSentences(text) {
    const parts = String(text || "").match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [];
    const rows = parts.map(function (part) {
      return part.trim();
    }).filter(Boolean);
    return rows.length ? rows : [String(text || "")];
  }

  const SAY_AS = [
    [/\bvxlan\b/gi, "vix-lan"],
    [/\bvteps\b/gi, "V T E Ps"],
    [/\bvtep\b/gi, "V T E P"],
    [/\bevpn\b/gi, "E V P N"],
    [/\bvnis\b/gi, "V N Is"],
    [/\bvni\b/gi, "V N I"],
    [/\budp\b/gi, "U D P"],
    [/\bbgp\b/gi, "B G P"],
    [/\bvlan\b/gi, "vee lan"],
    [/\bmac\b/gi, "mack"],
    [/\bip\b/gi, "I P"],
  ];

  function speakable(text) {
    return SAY_AS.reduce(function (line, rule) {
      return line.replace(rule[0], rule[1]);
    }, String(text || ""));
  }

  function speak(text, token, done) {
    captionEl.textContent = text;
    const sentences = splitSentences(text);
    state.talk = { sentences: sentences, index: 0, charIndex: 0, started: 0 };
    if (!state.voice || !window.speechSynthesis) {
      const words = String(text || "").split(/\s+/).filter(Boolean).length;
      const ms = Math.min(14000, Math.max(1400, words * 280));
      state.timers.push(window.setTimeout(function () {
        if (token !== state.token) return;
        done();
      }, ms));
      return;
    }
    withVoices(function (voices) {
      if (token !== state.token) return;
      const voice = chooseVoice(voices);
      if (voice) {
        const label = document.getElementById("voice-name");
        if (label) label.textContent = "Speaking as " + voice.name;
      }
      let index = 0;
      function next() {
        if (token !== state.token) return;
        if (index >= sentences.length) {
          done();
          return;
        }
        state.talk.index = index;
        state.talk.charIndex = 0;
        state.talk.started = performance.now();
        const line = sentences[index];
        index += 1;
        speakLine(line, voice, token, function () {
          const pause = window.setTimeout(next, 320);
          state.timers.push(pause);
        });
      }
      next();
    });
  }

  function speakLine(line, voice, token, done) {
    const spoken = speakable(line);
    const words = String(spoken || "").split(/\s+/).filter(Boolean).length;
    let finished = false;
    function finish() {
      if (finished || token !== state.token) return;
      finished = true;
      done();
    }
    const watchdog = window.setTimeout(finish, Math.min(18000, Math.max(4200, words * 640 + 1400)));
    state.timers.push(watchdog);
    const utter = new SpeechSynthesisUtterance(spoken);
    const name = voice ? voice.name : "";
    utter.rate = /premium|enhanced/i.test(name) ? 0.86 : /flo|eddy/i.test(name) ? 0.92 : 0.9;
    utter.pitch = 1;
    if (voice) utter.voice = voice;
    utter.onboundary = function (event) {
      if (!event || typeof event.charIndex !== "number") return;
      const scale = String(line || "").length / Math.max(String(spoken || "").length, 1);
      state.talk.charIndex = Math.round(event.charIndex * scale);
    };
    utter.onend = finish;
    utter.onerror = finish;
    state.timers.push(window.setTimeout(function () {
      if (token !== state.token || finished) return;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    }, 30));
  }

  function additionInk(scene) {
    return (scene || []).some(function (op) { return op.added && op.ink === "green"; }) ? "red" : "green";
  }

  function withInk(ops, color) {
    return (ops || []).map(function (op) {
      const copy = Object.assign({}, op);
      if (copy.op !== "figure" && copy.op !== "title") {
        copy.added = true;
        copy.ink = copy.ink || color;
      }
      return copy;
    });
  }

  function diagramOf(ops) {
    return (ops || []).find(function (op) {
      return op && op.op === "figure" && op.kind && op.kind !== "list";
    }) || null;
  }

  function baseDiagram(beats) {
    const beat = (beats || []).find(function (row) {
      return diagramOf(row.board || []);
    });
    if (!beat) return null;
    return (beat.board || []).filter(function (op) {
      return op.op === "title" || op.op === "figure" || (op.op === "hand" && !op.added);
    });
  }

  function drawPlan(scene, incoming, place) {
    const current = diagramOf(scene);
    if (place === "page" || !current) {
      if (place === "add" && !current) {
        const base = baseDiagram(state.beats);
        if (base) return { replace: true, ops: base.concat(withInk(incoming, additionInk(scene))) };
      }
      return { replace: true, ops: incoming };
    }
    if (place === "add" || place === "ask") {
      const notes = (incoming || []).filter(function (op) {
        return op.op !== "figure" && op.op !== "title";
      });
      const color = additionInk(scene);
      const ops = withInk(notes, color);
      if (current.kind === "fabric" && !notes.some(function (op) { return op.op === "emphasis"; })) {
        ops.unshift({ op: "emphasis", target: "tunnel", text: "VXLAN", ink: color, added: true });
      }
      return { replace: false, ops: ops };
    }
    return { replace: true, ops: incoming };
  }

  function playOps(ops, token, done, replace, speech, resume) {
    const list = asPage(Array.isArray(ops) ? ops : []);
    if (replace) state.scene = [];
    else state.scene = state.scene.filter(function (op) { return op.op !== "hand"; });
    const startIndex = resume && Number.isFinite(resume.index) ? resume.index : 0;
    const startT = resume && Number.isFinite(resume.t) ? Math.max(0, Math.min(0.98, resume.t)) : 0;
    state.draw = { list: list, index: startIndex, t: startT, handIndex: 0 };
    if (!list.length || startIndex >= list.length) {
      paintScene(null);
      if (done) done();
      return;
    }
    const words = String(speech || "").split(/\s+/).filter(Boolean).length;
    const budget = Math.max(1400, words * 120);
    const weights = list.map(function (op) {
      if (op.op === "figure") return 2.4;
      if (op.op === "table") return 1.6;
      if (op.op === "title") return 0.7;
      return 1;
    });
    const weightTotal = weights.reduce(function (sum, weight) { return sum + weight; }, 0) || 1;
    let index = startIndex;

    function step(initialT) {
      if (token !== state.token || state.paused) return;
      if (index >= list.length) {
        state.draw = { list: list, index: index, t: 1, handIndex: 0 };
        if (done) done();
        return;
      }
      const op = list[index];
      const handIndex = list.slice(0, index).filter(function (row) {
        return row.op === "hand";
      }).length;
      const dur = Math.max(280, Math.min(2800, budget * (weights[index] / weightTotal)));
      const start = performance.now() - (initialT || 0) * dur;
      function frame(now) {
        if (token !== state.token || state.paused) return;
        const t = Math.min(1, (now - start) / dur);
        state.draw = { list: list, index: index, t: t, handIndex: handIndex };
        paintScene({ op: op, t: t, handIndex: handIndex, nib: t < 1 });
        if (t < 1) {
          requestAnimationFrame(frame);
          return;
        }
        state.scene = state.scene.concat([op]);
        index += 1;
        step(0);
      }
      requestAnimationFrame(frame);
    }
    step(startT);
  }

  function asPage(ops) {
    const known = { title: 1, figure: 1, hand: 1, table: 1, emphasis: 1 };
    if (ops.length && ops.every(function (op) { return op && known[op.op]; })) return ops;
    let title = "";
    const labels = [];
    const hands = [];
    let table = null;
    let kind = "";
    let explicit = false;
    let packet = false;
    ops.slice(0, 14).forEach(function (row) {
      if (!row || typeof row !== "object") return;
      const op = String(row.op || "").toLowerCase();
      const text = String(row.text || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
      if (op === "title" && text.length > 1 && !title) title = text.slice(0, 80);
      else if (op === "table" && !table) table = row;
      else if (op === "figure") {
        const requested = String(row.kind || "");
        if (requested) {
          kind = requested;
          explicit = true;
        }
        (Array.isArray(row.labels) ? row.labels : []).forEach(function (label) {
          const line = String(label || "").trim();
          if (line.length > 1 && labels.length < 6) labels.push(line.slice(0, 48));
        });
      } else if (op === "hand" || op === "bullet" || op === "write") {
        if (text.length > 1 && hands.length < 6) hands.push(text.slice(0, 110));
      } else if (op === "label" || op === "box" || op === "sketch" || op === "circle" || op === "arrow") {
        if (text.length > 1 && labels.length < 6) labels.push(text.slice(0, 48));
        if (op === "sketch" && row.kind === "packet") packet = true;
      }
    });
    let promoted = false;
    let pageLabels = labels.slice();
    let pageHands = hands.slice();
    if (!pageLabels.length && pageHands.length) {
      pageLabels = pageHands.slice(0, 5).map(function (line) { return line.slice(0, 48); });
      pageHands = [];
      if (!explicit) {
        kind = "list";
        promoted = true;
      }
    }
    if (!explicit && !promoted) {
      if (pageLabels.some(function (label) { return /\d+\s*%/.test(label); })) kind = "pie";
      else if (pageLabels.length === 1 && /^[^=]{1,28}=[^=]{1,28}$/.test(pageLabels[0])) kind = "equation";
      else if (packet) kind = "packet";
      else if (pageLabels.length >= 2) kind = "flow";
      else if (pageLabels.length === 1) kind = "layers";
      else kind = "";
    }
    const caps = { flow: 3, packet: 6, layers: 6, pie: 4, cycle: 4, equation: 1, graph: 1, list: 5 };
    if (!caps[kind]) kind = "";
    pageLabels = kind ? pageLabels.slice(0, caps[kind]) : [];
    const page = [];
    if (title) page.push({ op: "title", text: title });
    if (kind && pageLabels.length) {
      const figure = { op: "figure", kind: kind, labels: pageLabels };
      if (ops.some(function (row) { return row && row.key; })) {
        const key = String((ops.find(function (row) { return row && row.key; }) || {}).key || "");
        if (pageLabels.indexOf(key) >= 0) figure.key = key;
      }
      page.push(figure);
    }
    pageHands.slice(0, 2).forEach(function (line) {
      if (pageLabels.indexOf(line) < 0) page.push({ op: "hand", text: line });
    });
    if (table && Array.isArray(table.columns) && Array.isArray(table.rows)) {
      page.push({ op: "table", columns: table.columns, rows: table.rows });
    }
    return page;
  }

  function paintScene(partial) {
    const view = sizeCanvas(canvas);
    const shown = state.scene.slice();
    if (partial && partial.op) shown.push(partial.op);
    view.box = pageBox(view, shown);
    paintBackground(view);
    let hands = 0;
    state.scene.forEach(function (op) {
      drawOp(view, op, 1, op.op === "hand" ? hands : 0, false);
      if (op.op === "hand") hands += 1;
    });
    if (!partial || !partial.op) return;
    drawOp(view, partial.op, partial.t, partial.handIndex || 0, partial.nib !== false);
  }

  function pageBox(view, ops) {
    const table = (ops || []).filter(function (op) { return op.op === "table"; })[0];
    const hands = (ops || []).filter(function (op) { return op.op === "hand"; }).length;
    const tableRows = table && Array.isArray(table.rows) ? table.rows.length + 1 : 0;
    const tableH = tableRows ? tableRows * 28 + 16 : 0;
    const handH = hands ? hands * 54 + 8 : 0;
    return {
      figureTop: 88,
      figureBottom: Math.max(168, view.h - 18 - tableH - handH),
      handTop: view.h - 10 - tableH - handH,
      tableTop: view.h - 8 - tableH,
    };
  }

  function sizeCanvas(board) {
    const rect = board.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(320, rect.width || 640);
    const h = Math.max(240, rect.height || 420);
    board.width = Math.floor(w * dpr);
    board.height = Math.floor(h * dpr);
    const ctx = board.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx: ctx, w: w, h: h };
  }

  function paintBackground(view) {
    view.ctx.fillStyle = "#f3eee4";
    view.ctx.fillRect(0, 0, view.w, view.h);
  }

  const INK = { black: "#243044", blue: "#1e4d86", red: "#9d2c2c", green: "#1d6b45" };
  const HAND = '"Marker Felt", Noteworthy, "Segoe Print", "Bradley Hand", cursive';
  const TYPED = 'ui-sans-serif, system-ui, -apple-system, sans-serif';
  const WASH = "rgba(198, 220, 242, 0.9)";
  const REDWASH = "rgba(242, 196, 196, 0.75)";
  const HILITE = "rgba(246, 208, 92, 0.82)";

  function drawOp(view, op, t, handIndex, showNib) {
    drawCompiled(view, compile(view, op, handIndex), t, showNib && t < 1);
  }

  function seedOf(op, extra) {
    const text = (op.op || "") + (op.kind || "") + (op.text || "") + String((op.labels || []).join("|")) + String(extra || 0);
    let hash = 0;
    for (let i = 0; i < text.length; i++) hash = (hash * 33 + text.charCodeAt(i)) >>> 0;
    return hash || 1;
  }

  function wobble(pts, seed, amount) {
    return pts.map(function (pt, index) {
      const n = Math.sin(index * 0.85 + seed) * amount;
      const m = Math.cos(index * 0.47 + seed * 0.2) * amount * 0.65;
      return { x: pt.x + n, y: pt.y + m };
    });
  }

  function circlePts(cx, cy, r, n) {
    const pts = [];
    for (let i = 0; i <= n; i++) {
      const angle = (i / n) * Math.PI * 2;
      pts.push({ x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r });
    }
    return pts;
  }

  function roundBox(x, y, w, h, radius, seed) {
    const r = Math.max(2, Math.min(radius, w / 2, h / 2));
    const pts = [];
    function corner(cx, cy, a0, a1) {
      for (let i = 0; i <= 5; i++) {
        const angle = a0 + (a1 - a0) * (i / 5);
        pts.push({ x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r });
      }
    }
    pts.push({ x: x + r, y: y });
    pts.push({ x: x + w - r, y: y });
    corner(x + w - r, y + r, -Math.PI / 2, 0);
    pts.push({ x: x + w, y: y + h - r });
    corner(x + w - r, y + h - r, 0, Math.PI / 2);
    pts.push({ x: x + r, y: y + h });
    corner(x + r, y + h - r, Math.PI / 2, Math.PI);
    pts.push({ x: x, y: y + r });
    corner(x + r, y + r, Math.PI, Math.PI * 1.5);
    pts.push({ x: x + r, y: y });
    return wobble(pts, seed, 0.55);
  }

  function arrowPts(x1, y1, x2, y2, seed) {
    const shaft = [];
    for (let i = 0; i <= 10; i++) {
      const t = i / 10;
      shaft.push({ x: x1 + (x2 - x1) * t, y: y1 + (y2 - y1) * t });
    }
    const angle = Math.atan2(y2 - y1, x2 - x1);
    const len = 12;
    return [
      wobble(shaft, seed, 0.45),
      [
        { x: x2, y: y2 },
        { x: x2 - len * Math.cos(angle - 0.45), y: y2 - len * Math.sin(angle - 0.45) },
      ],
      [
        { x: x2, y: y2 },
        { x: x2 - len * Math.cos(angle + 0.45), y: y2 - len * Math.sin(angle + 0.45) },
      ],
    ];
  }

  function pathLength(pts) {
    let length = 0;
    for (let i = 1; i < pts.length; i++) {
      length += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
    }
    return length || 1;
  }

  function layoutLetters(ctx, text, x, y, font, color, maxWidth, align, style, maxLines) {
    ctx.save();
    ctx.font = font;
    const words = String(text || "").split(/\s+/).filter(Boolean);
    const lines = [];
    let line = "";
    words.forEach(function (word) {
      const trial = line ? line + " " + word : word;
      if (ctx.measureText(trial).width > maxWidth && line) {
        lines.push(line);
        line = word;
      } else {
        line = trial;
      }
    });
    if (line) lines.push(line);
    const letters = [];
    const gap = style === "hand" ? 26 : 20;
    const used = lines.slice(0, maxLines || 2);
    const block = (used.length - 1) * gap;
    used.forEach(function (row, rowIndex) {
      const rowWidth = ctx.measureText(row).width;
      let cursor = align === "center" ? x - rowWidth / 2 : x;
      const baseline = y - block / 2 + rowIndex * gap;
      for (let i = 0; i < row.length; i++) {
        const ch = row[i];
        const width = ctx.measureText(ch).width;
        letters.push({
          ch: ch,
          x: cursor,
          y: baseline,
          w: width,
          font: font,
          color: color,
          style: style,
          i: i + rowIndex * 9,
        });
        cursor += width;
      }
    });
    ctx.restore();
    return letters;
  }

  function compile(view, op, handIndex) {
    const seed = seedOf(op, handIndex);
    const items = [];
    function addStroke(pts, color, width) {
      if (pts && pts.length > 1) items.push({ type: "stroke", pts: pts, color: color, width: width || 2.4 });
    }
    function addWords(text, x, y, font, color, maxWidth, align, style, maxLines) {
      const letters = layoutLetters(view.ctx, text, x, y, font, color, maxWidth, align, style, maxLines);
      if (letters.length) items.push({ type: "letters", letters: letters });
    }
    if (!op || !op.op) return items;
    if (op.op === "title") {
      const text = op.text || "";
      const font = "32px " + HAND;
      view.ctx.save();
      view.ctx.font = font;
      const width = Math.min(view.w - 72, Math.max(80, view.ctx.measureText(text).width + 22));
      view.ctx.restore();
      items.push({ type: "fill", x: 28, y: 18, w: width, h: 40, r: 8, color: HILITE });
      addWords(text, 36, 46, font, "#1a3358", view.w - 64, "left", "hand", 1);
      addStroke(wobble([{ x: 34, y: 64 }, { x: 34 + width - 8, y: 66 }], seed, 0.8), "#1a3358", 2);
      return items;
    }
    if (op.op === "hand") {
      const color = INK[op.ink] || INK.black;
      const y = view.box.handTop + 28 + handIndex * 54;
      addWords(op.text, 36, y, "18px " + HAND, color, view.w - 72, "left", "hand", 2);
      return items;
    }
    if (op.op === "emphasis") return compileEmphasis(view, op, seed, items, addStroke, addWords);
    if (op.op === "table") return compileTable(view, op, items, addStroke, addWords);
    if (op.op === "figure") return compileFigure(view, op, seed, items, addStroke, addWords);
    return items;
  }

  function compileFigure(view, op, seed, items, addStroke, addWords) {
    const labels = Array.isArray(op.labels) ? op.labels : [];
    const kind = op.kind;
    if (kind === "fabric") return compileFabric(view, op, seed, items, addStroke, addWords);
    if (kind === "list") return compileList(view, op, seed, items, addStroke, addWords);
    if (kind === "flow") return compileFlow(view, op, seed, items, addStroke, addWords);
    if (kind === "layers") return compileLayers(view, op, seed, items, addStroke, addWords);
    if (kind === "packet") return compilePacket(view, op, seed, items, addStroke, addWords);
    if (kind === "pie") return compilePie(view, op, seed, items, addStroke, addWords);
    if (kind === "equation") return compileEquation(view, op, seed, items, addStroke, addWords);
    if (kind === "graph") return compileGraph(view, op, seed, items, addStroke, addWords);
    if (kind === "cycle") return compileCycle(view, op, seed, items, addStroke, addWords);
    return compileList(view, op, seed, items, addStroke, addWords);
  }

  function isKey(op, label) {
    return op.key && label === op.key;
  }

  function compileFabric(view, op, seed, items, addStroke, addWords) {
    const spines = op.spines && op.spines.length ? op.spines.slice(0, 2) : ["Spine", "Spine"];
    const leaves = op.leaves && op.leaves.length ? op.leaves.slice(0, 3) : ["Leaf A", "Leaf B"];
    const hosts = op.hosts && op.hosts.length ? op.hosts.slice(0, 4) : ["Host A", "Host B"];
    const tunnelName = op.tunnel || "VXLAN";
    const top = view.box.figureTop + 6;
    const bottom = Math.max(top + 180, view.box.figureBottom - 8);
    const boxW = Math.min(112, (view.w - 64) / Math.max(spines.length, leaves.length, hosts.length) - 28);
    const boxH = 36;

    function slots(names, y) {
      const n = names.length;
      const span = view.w - 36;
      return names.map(function (label, index) {
        const gap = span / n;
        return { label: label, x: 18 + gap * index + (gap - boxW) / 2, y: y, w: boxW, h: boxH };
      });
    }
    function mid(slot, edge) {
      return {
        x: slot.x + slot.w / 2,
        y: edge === "top" ? slot.y : slot.y + slot.h,
      };
    }
    function link(a, b, color) {
      const pts = [];
      for (let i = 0; i <= 8; i++) {
        const t = i / 8;
        pts.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });
      }
      addStroke(wobble(pts, seed + pts[0].x, 0.4), color, 1.7);
    }

    const spineY = top;
    const leafY = top + (bottom - top) * 0.4;
    const hostY = top + (bottom - top) * 0.74;
    const spineSlots = slots(spines, spineY);
    const leafSlots = slots(leaves, leafY);
    const hostSlots = slots(hosts, hostY);

    spineSlots.forEach(function (spine) {
      leafSlots.forEach(function (leaf) {
        link(mid(spine, "bottom"), mid(leaf, "top"), INK.blue);
      });
    });
    hostSlots.forEach(function (host, index) {
      const leaf = leafSlots[Math.min(index, leafSlots.length - 1)];
      link(mid(leaf, "bottom"), mid(host, "top"), INK.black);
    });

    let tunnel = null;
    if (leafSlots.length >= 2) {
      const y = leafSlots[0].y + boxH + 16;
      tunnel = {
        a: { x: leafSlots[0].x + 8, y: y },
        b: { x: leafSlots[leafSlots.length - 1].x + leafSlots[leafSlots.length - 1].w - 8, y: y },
      };
      addStroke([tunnel.a, tunnel.b], INK.red, 2.6);
      addWords(tunnelName, (tunnel.a.x + tunnel.b.x) / 2, y - 6, "16px " + HAND, INK.red, 140, "center", "hand", 1);
    }

    function node(slot, index, key) {
      items.push({
        type: "fill",
        x: slot.x,
        y: slot.y,
        w: slot.w,
        h: slot.h,
        r: 9,
        color: key ? REDWASH : WASH,
      });
      addStroke(roundBox(slot.x, slot.y, slot.w, slot.h, 9, seed + index), key ? INK.red : INK.blue, 2.2);
      addWords(slot.label, slot.x + slot.w / 2, slot.y + slot.h / 2 + 4, "15px " + HAND, key ? INK.red : INK.black, slot.w - 10, "center", "hand", 1);
    }
    spineSlots.forEach(function (slot, index) { node(slot, index, isKey(op, slot.label)); });
    leafSlots.forEach(function (slot, index) { node(slot, index + 4, isKey(op, slot.label)); });
    hostSlots.forEach(function (slot, index) { node(slot, index + 8, isKey(op, slot.label)); });

    state.layout = {
      tunnel: tunnel,
      leaves: leafSlots,
      noteY: hostY + boxH + 28,
    };
    return items;
  }

  function compileEmphasis(view, op, seed, items, addStroke, addWords) {
    const layout = state.layout;
    const color = INK[op.ink] || INK.green;
    if (!layout) return items;
    if ((op.target || "tunnel") === "tunnel" && layout.tunnel) {
      addStroke([
        { x: layout.tunnel.a.x, y: layout.tunnel.a.y + 6 },
        { x: layout.tunnel.b.x, y: layout.tunnel.b.y + 6 },
      ], color, 3);
    }
    if (op.target === "leaves" && layout.leaves) {
      layout.leaves.forEach(function (slot, index) {
        addStroke(roundBox(slot.x - 5, slot.y - 5, slot.w + 10, slot.h + 10, 12, seed + index), color, 2.4);
      });
      if (op.text) {
        const slot = layout.leaves[0];
        addWords(op.text, slot.x + slot.w / 2, slot.y - 8, "16px " + HAND, color, 80, "center", "hand", 1);
      }
    }
    return items;
  }

  function compileList(view, op, seed, items, addStroke, addWords) {
    const labels = op.labels || [];
    const room = Math.max(28, (view.box.figureBottom - view.box.figureTop - 12) / Math.max(1, labels.length));
    const gap = Math.min(40, room);
    labels.forEach(function (label, index) {
      const y = view.box.figureTop + 28 + index * gap;
      const color = isKey(op, label) ? INK.red : INK.black;
      addStroke(wobble(circlePts(42, y - 6, 4, 8), seed + index, 0.3), color, 2);
      addWords(label, 60, y, "22px " + HAND, color, view.w - 96, "left", "hand", 1);
    });
    return items;
  }

  function compileFlow(view, op, seed, items, addStroke, addWords) {
    const labels = op.labels || [];
    const n = Math.max(1, labels.length);
    const gap = 48;
    const outer = 28;
    const w = (view.w - outer * 2 - gap * (n - 1)) / n;
    const h = 74;
    const y = view.box.figureTop + Math.max(12, (view.box.figureBottom - view.box.figureTop - h) / 2);
    labels.forEach(function (label, index) {
      const x = outer + index * (w + gap);
      const key = isKey(op, label);
      items.push({ type: "fill", x: x, y: y, w: w, h: h, r: 12, color: key ? REDWASH : WASH });
      addStroke(roundBox(x, y, w, h, 12, seed + index), key ? INK.red : INK.blue, 2.5);
      addWords(label, x + w / 2, y + h / 2 + 4, "20px " + HAND, key ? INK.red : INK.black, w - 18, "center", "hand", 2);
      if (index < n - 1) {
        arrowPts(x + w + 6, y + h / 2, x + w + gap - 8, y + h / 2, seed + 20 + index).forEach(function (pts) {
          addStroke(pts, INK.black, 2.3);
        });
      }
    });
    return items;
  }

  function compileLayers(view, op, seed, items, addStroke, addWords) {
    const labels = op.labels || [];
    const n = Math.max(1, labels.length);
    const gap = 8;
    const band = Math.min(52, (view.box.figureBottom - view.box.figureTop - gap * (n - 1) - 8) / n);
    const w = Math.min(460, view.w * 0.7);
    const x = (view.w - w) / 2;
    let y = view.box.figureTop + 10;
    labels.forEach(function (label, index) {
      const key = isKey(op, label);
      items.push({ type: "fill", x: x, y: y, w: w, h: band, r: 10, color: key ? REDWASH : (index % 2 ? "#f7f3ea" : WASH) });
      addStroke(roundBox(x, y, w, band, 10, seed + index), key ? INK.red : INK.blue, 2.4);
      addWords(label, x + w / 2, y + band / 2 + 4, "20px " + HAND, key ? INK.red : INK.black, w - 20, "center", "hand", 1);
      y += band + gap;
    });
    return items;
  }

  function compilePacket(view, op, seed, items, addStroke, addWords) {
    const labels = op.labels || [];
    const n = Math.max(1, labels.length);
    const x = 24;
    const y = view.box.figureTop + Math.max(16, (view.box.figureBottom - view.box.figureTop - 78) / 2);
    const w = view.w - 48;
    const h = 78;
    const cell = w / n;
    items.push({ type: "fill", x: x, y: y, w: w, h: h, r: 12, color: WASH });
    addStroke(roundBox(x, y, w, h, 12, seed), INK.blue, 2.5);
    labels.forEach(function (label, index) {
      const key = isKey(op, label);
      const left = x + index * cell;
      if (key) items.push({ type: "fill", x: left + 3, y: y + 3, w: cell - 6, h: h - 6, r: 8, color: REDWASH });
      if (index > 0) addStroke([{ x: left, y: y + 8 }, { x: left, y: y + h - 8 }], INK.blue, 1.6);
      addWords(label, left + cell / 2, y + h / 2 + 4, "16px " + HAND, key ? INK.red : INK.black, cell - 12, "center", "hand", 2);
    });
    return items;
  }

  function compilePie(view, op, seed, items, addStroke, addWords) {
    const labels = op.labels || [];
    const weights = labels.map(function (label) {
      const match = String(label).match(/(\d+(?:\.\d+)?)\s*%/);
      return match ? Number(match[1]) : 1;
    });
    const total = weights.reduce(function (sum, weight) { return sum + weight; }, 0) || 1;
    const colors = ["#8ebbe3", "#f0c56a", "#e08a8a", "#86c9a4"];
    const cx = Math.min(view.w * 0.3, 180);
    const cy = (view.box.figureTop + view.box.figureBottom) / 2;
    const radius = Math.max(48, Math.min(86, (view.box.figureBottom - view.box.figureTop) / 2 - 8));
    let angle = -Math.PI / 2;
    labels.forEach(function (label, index) {
      const sweep = (weights[index] / total) * Math.PI * 2;
      items.push({
        type: "wedge",
        cx: cx,
        cy: cy,
        r: radius,
        a0: angle,
        a1: angle + sweep,
        color: colors[index % colors.length],
      });
      angle += sweep;
    });
    addStroke(wobble(circlePts(cx, cy, radius, 36), seed, 0.6), INK.black, 2.2);
    labels.forEach(function (label, index) {
      const y = view.box.figureTop + 28 + index * 32;
      const color = isKey(op, label) ? INK.red : INK.black;
      items.push({ type: "fill", x: cx + radius + 28, y: y - 16, w: 14, h: 14, r: 3, color: colors[index % colors.length] });
      addWords(label, cx + radius + 50, y, "18px " + HAND, color, view.w - (cx + radius + 70), "left", "hand", 1);
    });
    return items;
  }

  function compileEquation(view, op, seed, items, addStroke, addWords) {
    const text = (op.labels || [])[0] || "";
    const font = "40px " + HAND;
    const y = (view.box.figureTop + view.box.figureBottom) / 2;
    view.ctx.save();
    view.ctx.font = font;
    const width = Math.min(view.w - 80, Math.max(120, view.ctx.measureText(text).width + 28));
    view.ctx.restore();
    const x = (view.w - width) / 2;
    items.push({ type: "fill", x: x, y: y - 36, w: width, h: 52, r: 8, color: HILITE });
    addWords(text, view.w / 2, y, font, isKey(op, text) ? INK.red : INK.red, width - 12, "center", "hand", 1);
    addStroke(wobble([{ x: x + 8, y: y + 22 }, { x: x + width - 8, y: y + 24 }], seed, 0.7), INK.red, 2);
    return items;
  }

  function compileGraph(view, op, seed, items, addStroke, addWords) {
    const left = 64;
    const right = view.w - 48;
    const top = view.box.figureTop + 16;
    const bottom = view.box.figureBottom - 28;
    addStroke([{ x: left, y: top }, { x: left, y: bottom }, { x: right, y: bottom }], INK.black, 2.2);
    const curve = [];
    const span = right - left - 16;
    for (let i = 0; i <= 24; i++) {
      const t = i / 24;
      curve.push({
        x: left + 10 + span * t,
        y: bottom - 12 - (bottom - top - 24) * (0.15 + 0.75 * Math.sin(t * Math.PI * 0.9)),
      });
    }
    addStroke(wobble(curve, seed, 0.5), INK.blue, 2.6);
    const label = (op.labels || [])[0] || "";
    if (label) addWords(label, (left + right) / 2, bottom + 22, "18px " + HAND, isKey(op, label) ? INK.red : INK.black, right - left, "center", "hand", 1);
    return items;
  }

  function compileCycle(view, op, seed, items, addStroke, addWords) {
    const labels = op.labels || [];
    const n = Math.max(1, labels.length);
    const cx = view.w / 2;
    const cy = (view.box.figureTop + view.box.figureBottom) / 2;
    const ring = Math.min(100, (view.box.figureBottom - view.box.figureTop) / 2 - 28);
    labels.forEach(function (label, index) {
      const angle = -Math.PI / 2 + (index / n) * Math.PI * 2;
      const x = cx + Math.cos(angle) * ring;
      const y = cy + Math.sin(angle) * ring;
      const key = isKey(op, label);
      items.push({ type: "fill", x: x - 28, y: y - 18, w: 56, h: 36, r: 16, color: key ? REDWASH : WASH });
      addStroke(wobble(circlePts(x, y, 22, 16), seed + index, 0.5), key ? INK.red : INK.blue, 2.3);
      addWords(label, x, y + 40, "15px " + HAND, key ? INK.red : INK.black, 110, "center", "hand", 1);
      const next = -Math.PI / 2 + ((index + 1) / n) * Math.PI * 2;
      const x2 = cx + Math.cos(next) * ring;
      const y2 = cy + Math.sin(next) * ring;
      const midA = (angle + next) / 2 + (index === n - 1 ? Math.PI : 0);
      const mx = cx + Math.cos(midA) * (ring + 18);
      const my = cy + Math.sin(midA) * (ring + 18);
      const pts = [];
      for (let i = 0; i <= 12; i++) {
        const t = i / 12;
        const u = 1 - t;
        pts.push({
          x: u * u * (x + Math.cos(angle) * 24) + 2 * u * t * mx + t * t * (x2 - Math.cos(next) * 24),
          y: u * u * (y + Math.sin(angle) * 24) + 2 * u * t * my + t * t * (y2 - Math.sin(next) * 24),
        });
      }
      addStroke(wobble(pts, seed + 30 + index, 0.4), INK.black, 1.8);
    });
    return items;
  }

  function compileTable(view, op, items, addStroke, addWords) {
    const columns = Array.isArray(op.columns) ? op.columns.slice(0, 2) : [];
    const body = Array.isArray(op.rows) ? op.rows.slice(0, 4) : [];
    const rows = [columns].concat(body);
    const x = 28;
    const y = view.box.tableTop;
    const w = view.w - 56;
    const rowH = 28;
    const colW = w / 2;
    items.push({ type: "fill", x: x, y: y, w: w, h: rowH, r: 4, color: "rgba(226, 220, 208, 0.95)" });
    rows.forEach(function (row, index) {
      const top = y + index * rowH;
      addStroke([{ x: x, y: top }, { x: x + w, y: top }], INK.black, 1.4);
      const cells = Array.isArray(row) ? row : [];
      for (let col = 0; col < 2; col++) {
        addWords(String(cells[col] || ""), x + col * colW + 10, top + 19, "16px " + HAND, INK.black, colW - 16, "left", "hand", 1);
      }
    });
    addStroke([{ x: x, y: y + rows.length * rowH }, { x: x + w, y: y + rows.length * rowH }], INK.black, 1.4);
    addStroke([{ x: x + colW, y: y }, { x: x + colW, y: y + rows.length * rowH }], INK.black, 1.3);
    return items;
  }

  function drawCompiled(view, items, t, showNib) {
    const costs = items.map(function (item) {
      if (item.type === "stroke") return pathLength(item.pts);
      if (item.type === "letters") return Math.max(1, item.letters.length) * 5;
      if (item.type === "wedge") return 36;
      return 10;
    });
    const total = costs.reduce(function (sum, cost) { return sum + cost; }, 0) || 1;
    let budget = total * Math.max(0, Math.min(1, t));
    let pen = null;
    let penColor = INK.blue;
    items.forEach(function (item, index) {
      const cost = costs[index];
      if (budget <= 0) return;
      const local = Math.min(1, budget / cost);
      budget -= cost;
      if (item.type === "stroke") {
        pen = trace(view.ctx, item.pts, local, item.color, item.width);
        penColor = item.color;
      } else if (item.type === "letters") {
        const count = local >= 1 ? item.letters.length : Math.max(0, Math.floor(item.letters.length * local));
        writeLetters(view.ctx, item.letters, count);
        if (item.letters.length && count > 0) {
          const letter = item.letters[Math.min(count, item.letters.length) - 1];
          pen = { x: letter.x + letter.w, y: letter.y - 4 };
          penColor = letter.color;
        }
      } else if (item.type === "wedge") {
        drawWedge(view.ctx, item, local);
      } else if (local > 0.04) {
        fillRound(view.ctx, item);
      }
    });
    if (showNib && pen) drawNib(view.ctx, pen.x, pen.y, penColor);
  }

  function fillRound(ctx, item) {
    const r = Math.max(0, item.r || 0);
    ctx.save();
    ctx.fillStyle = item.color;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(item.x, item.y, item.w, item.h, r);
    else ctx.rect(item.x, item.y, item.w, item.h);
    ctx.fill();
    ctx.restore();
  }

  function drawWedge(ctx, item, t) {
    const sweep = item.a0 + (item.a1 - item.a0) * Math.max(0, Math.min(1, t));
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(item.cx, item.cy);
    ctx.arc(item.cx, item.cy, item.r, item.a0, sweep);
    ctx.closePath();
    ctx.fillStyle = item.color;
    ctx.fill();
    ctx.clip();
    ctx.strokeStyle = "rgba(36, 48, 68, 0.18)";
    ctx.lineWidth = 1;
    for (let line = -item.r; line < item.r; line += 7) {
      ctx.beginPath();
      ctx.moveTo(item.cx - item.r, item.cy + line);
      ctx.lineTo(item.cx + item.r, item.cy + line + 12);
      ctx.stroke();
    }
    ctx.restore();
  }

  function trace(ctx, pts, t, color, width) {
    if (!pts.length) return null;
    const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    const target = pathLength(pts) * eased;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    let walked = 0;
    let pen = pts[0];
    for (let i = 1; i < pts.length; i++) {
      const seg = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
      if (walked + seg <= target || t >= 1) {
        ctx.lineTo(pts[i].x, pts[i].y);
        pen = pts[i];
        walked += seg;
      } else {
        const local = seg ? (target - walked) / seg : 1;
        pen = {
          x: pts[i - 1].x + (pts[i].x - pts[i - 1].x) * local,
          y: pts[i - 1].y + (pts[i].y - pts[i - 1].y) * local,
        };
        ctx.lineTo(pen.x, pen.y);
        break;
      }
    }
    ctx.stroke();
    ctx.restore();
    return pen;
  }

  function writeLetters(ctx, letters, count) {
    letters.slice(0, count).forEach(function (letter) {
      ctx.save();
      ctx.font = letter.font;
      ctx.fillStyle = letter.color;
      if (letter.style === "hand") {
        ctx.translate(letter.x, letter.y);
        ctx.rotate(Math.sin(letter.i * 1.7) * 0.03);
        ctx.fillText(letter.ch, 0, 0);
      } else {
        ctx.fillText(letter.ch, letter.x, letter.y);
      }
      ctx.restore();
    });
  }

  function drawNib(ctx, x, y, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(-0.7);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.ellipse(0, 0, 7, 2.6, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  function syncHand() {
    handBtn.setAttribute("aria-pressed", state.hand ? "true" : "false");
    handBtn.textContent = state.hand ? "Hand raised" : "Raise hand";
  }

  function syncPause() {
    if (!pauseBtn) return;
    const live = state.mode === "teaching" || state.mode === "answering";
    pauseBtn.disabled = !state.lesson || (!live && !state.paused);
    pauseBtn.textContent = state.paused ? "Resume" : "Pause";
    pauseBtn.setAttribute("aria-pressed", state.paused ? "true" : "false");
  }

  function remainingSpeech() {
    const talk = state.talk;
    if (!talk || !talk.sentences || !talk.sentences.length) return state.script || "";
    const line = talk.sentences[talk.index] || "";
    let cut = talk.charIndex || 0;
    if (cut <= 0 && talk.started) {
      const elapsed = performance.now() - talk.started;
      const words = line.split(/\s+/).filter(Boolean).length || 1;
      const expected = Math.max(1200, words * (state.voice ? 480 : 260));
      cut = Math.floor(line.length * Math.min(0.92, elapsed / expected));
    }
    if (cut > 0 && cut < line.length) {
      const space = line.lastIndexOf(" ", cut);
      if (space > 0) cut = space + 1;
    }
    const rest = line.slice(cut).trim();
    return [rest].concat(talk.sentences.slice(talk.index + 1)).filter(Boolean).join(" ");
  }

  function pauseInstructor() {
    if (state.paused) return;
    if (state.mode !== "teaching" && state.mode !== "answering") return;
    const draw = state.draw || { list: [], index: 0, t: 0, handIndex: 0 };
    state.hold = {
      kind: state.mode === "answering" ? "answer" : "beat",
      speech: remainingSpeech(),
      board: (draw.list || []).slice(),
      scene: state.scene.slice(),
      index: draw.index || 0,
      t: draw.t || 0,
      handIndex: draw.handIndex || 0,
      after: state.after,
    };
    state.paused = true;
    halt();
    const hold = state.hold;
    const partial = hold.index < hold.board.length
      ? { op: hold.board[hold.index], t: hold.t, handIndex: hold.handIndex, nib: false }
      : null;
    paintScene(partial);
    syncPause();
    setStatus("Paused.");
  }

  function resumeInstructor() {
    const hold = state.hold;
    if (!hold) return;
    state.paused = false;
    state.hold = null;
    halt();
    const token = state.token;
    state.mode = hold.kind === "answer" ? "answering" : "teaching";
    state.scene = hold.scene.slice();
    state.after = hold.after || "stay";
    state.script = hold.speech || "";
    syncPause();
    setStatus(state.mode === "answering" ? "The instructor is answering." : "Teaching.");
    let speechDone = !hold.speech;
    let drawDone = hold.index >= hold.board.length;
    function check() {
      if (token !== state.token || state.paused) return;
      if (speechDone && drawDone) {
        if (hold.kind === "answer") afterAnswer();
        else afterBeat();
      }
    }
    if (!speechDone) {
      speak(hold.speech, token, function () {
        speechDone = true;
        check();
      });
    }
    if (!drawDone) {
      playOps(hold.board, token, function () {
        drawDone = true;
        check();
      }, false, hold.speech, { index: hold.index, t: hold.t });
    } else {
      paintScene(null);
    }
    if (speechDone && drawDone) check();
  }

  if (pauseBtn) {
    pauseBtn.addEventListener("click", function () {
      if (state.paused) resumeInstructor();
      else pauseInstructor();
    });
  }

  handBtn.addEventListener("click", function () {
    if (!state.lesson) {
      setStatus("Start class before raising your hand.");
      return;
    }
    state.hand = !state.hand;
    state.paused = false;
    state.hold = null;
    syncHand();
    syncPause();
    if (state.hand) {
      halt();
      state.mode = "paused";
      syncPause();
      setStatus("Hand raised. Ask your question.");
      questionInput.focus();
      return;
    }
    setStatus("Hand down.");
    if (state.beats.length) playBeat(state.index);
  });

  voiceBtn.addEventListener("click", function () {
    state.voice = !state.voice;
    voiceBtn.setAttribute("aria-pressed", state.voice ? "true" : "false");
    voiceBtn.textContent = state.voice ? "Voice on" : "Voice off";
    if (!state.voice && window.speechSynthesis) window.speechSynthesis.cancel();
  });

  questionForm.addEventListener("submit", function (event) {
    event.preventDefault();
    submitQuestion(false);
  });

  noteBtn.addEventListener("click", function () {
    submitQuestion(true);
  });

  function submitQuestion(later) {
    const text = questionInput.value.trim();
    if (!text) {
      setStatus("Write a question first.");
      questionInput.focus();
      return;
    }
    if (!state.lesson) {
      setStatus("Start class before asking.");
      return;
    }
    questionInput.value = "";
    if (later && (state.mode === "teaching" || state.mode === "answering")) {
      state.queue.push(text);
      addTurn("You", text);
      setStatus("Posted. The instructor will take it after this part.");
      return;
    }
    let after = "stay";
    if (state.mode === "teaching" || state.mode === "answering") after = "replay";
    else if (state.mode === "paused") after = state.beatDone ? "next" : "replay";
    state.hand = false;
    state.paused = false;
    state.hold = null;
    syncHand();
    syncPause();
    halt();
    state.after = after;
    askNow(text, false);
  }

  function wantsFreshBoard(text) {
    return /\b(clean slate|clean (diagram|board|page|slate|drawing)|start over|start fresh|from scratch|redraw|re-draw|draw (it|that|this) again|clear the (board|slate|diagram|page))\b/i.test(text || "");
  }

  function askNow(text, listed) {
    const lesson = state.lesson;
    const beat = state.beats[state.index] || {};
    state.mode = "answering";
    state.paused = false;
    state.hold = null;
    syncPause();
    state.askId += 1;
    const req = state.askId;
    if (!listed) addTurn("You", text);
    setStatus("The instructor is answering.");
    fetch("/v1/classroom/questions", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({
        topic: lesson.topic || lesson.title || "",
        question: text,
        segment_title: beat.title || "",
        recent_speech: beat.speech || "",
      }),
    })
      .then(function (response) {
        return jsonBody(response).then(function (body) {
          if (!response.ok) throw new Error(errorText(response, body));
          return body;
        });
      })
      .then(function (answer) {
        if (req !== state.askId) return;
        addTurn("Instructor", answer.speech || "");
        halt();
        const token = state.token;
        state.mode = "answering";
        state.script = answer.speech || "";
        syncPause();
        let speechDone = false;
        let drawDone = false;
        function check() {
          if (token !== state.token || state.paused) return;
          if (speechDone && drawDone) afterAnswer();
        }
        speak(answer.speech || "", token, function () {
          speechDone = true;
          check();
        });
        const plan = drawPlan(state.scene, answer.board || [], wantsFreshBoard(text) ? "page" : "ask");
        if (!plan.replace && !plan.ops.some(function (op) { return op.op === "hand"; })) {
          const line = String(answer.speech || "").split(/[.!?]/)[0].trim();
          if (line) plan.ops.push({ op: "hand", text: line.slice(0, 110), ink: additionInk(state.scene), added: true });
        }
        playOps(plan.ops, token, function () {
          drawDone = true;
          check();
        }, plan.replace, answer.speech || "");
      })
      .catch(function (err) {
        if (req !== state.askId) return;
        setStatus(err.message || "The instructor could not answer.");
      });
  }

  function afterAnswer() {
    if (state.hand) {
      state.mode = "paused";
      syncPause();
      setStatus("Hand raised.");
      return;
    }
    if (state.queue.length) {
      askNow(state.queue.shift(), true);
      return;
    }
    if (state.after === "replay" && state.beats.length) {
      playBeat(state.index);
      return;
    }
    if (state.after === "next" && state.index + 1 < state.beats.length) {
      playBeat(state.index + 1);
      return;
    }
    state.mode = "idle";
    syncPause();
    setStatus("Ask another question, or continue when you are ready.");
  }

  function addTurn(who, text) {
    state.transcript.push({ who: who, text: text });
    const empty = discussion.querySelector(".empty");
    if (empty) empty.remove();
    const li = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = who;
    const body = document.createElement("p");
    body.textContent = text;
    li.append(name, body);
    discussion.appendChild(li);
    discussion.scrollTop = discussion.scrollHeight;
  }

  function setAskingEnabled(on) {
    askBtn.disabled = !on;
    noteBtn.disabled = !on;
    handBtn.disabled = !on;
    const postBtn = document.getElementById("post-lesson");
    if (postBtn) postBtn.disabled = !on;
    syncPause();
  }

  const postBtn = document.getElementById("post-lesson");
  const postedList = document.getElementById("posted");
  if (postBtn) {
    postBtn.addEventListener("click", postClass);
  }

  function postClass() {
    if (!state.lesson || !postBtn) return;
    postBtn.disabled = true;
    setStatus("Posting this class…");
    let image = "";
    try {
      const data = canvas.toDataURL("image/png");
      image = data.indexOf(",") >= 0 ? data.split(",")[1] : "";
    } catch (err) {
      image = "";
    }
    fetch("/v1/classroom/posts", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({
        topic: state.lesson.topic || "",
        title: state.lesson.title || state.lesson.topic || "Class",
        lesson: state.lesson,
        discussion: state.transcript,
        image_png: image,
      }),
    })
      .then(function (response) {
        return jsonBody(response).then(function (body) {
          if (!response.ok) throw new Error(errorText(response, body));
          return body;
        });
      })
      .then(function () {
        setStatus("Posted. It is in the list on the left.");
        loadPosts();
      })
      .catch(function (err) {
        setStatus(err.message || "The class could not be posted.");
      })
      .then(function () {
        postBtn.disabled = !state.lesson;
      });
  }

  function loadPosts() {
    if (!postedList) return;
    fetch("/v1/classroom/posts", { headers: headers() })
      .then(function (response) {
        return jsonBody(response).then(function (body) {
          if (!response.ok) throw new Error(errorText(response, body));
          return body;
        });
      })
      .then(function (body) {
        postedList.replaceChildren();
        (body.posts || []).forEach(function (post) {
          const item = document.createElement("li");
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "item";
          btn.textContent = post.title || post.topic || "Class";
          btn.addEventListener("click", function () {
            openPost(post.id);
          });
          item.appendChild(btn);
          postedList.appendChild(item);
        });
      })
      .catch(function () {
        postedList.replaceChildren();
      });
  }

  function openPost(postId) {
    state.paused = false;
    state.hold = null;
    halt();
    syncPause();
    fetch("/v1/classroom/posts/" + encodeURIComponent(postId), { headers: headers() })
      .then(function (response) {
        return jsonBody(response).then(function (body) {
          if (!response.ok) throw new Error(errorText(response, body));
          return body;
        });
      })
      .then(function (post) {
        if (post.lesson && Array.isArray(post.lesson.segments)) {
          state.lesson = post.lesson;
          state.beats = post.lesson.segments;
          state.mode = "idle";
          renderPlan(post.lesson);
          setAskingEnabled(true);
        }
        setStatus("Posted class. Choose a part to teach it again.");
        if (!post.image) return null;
        return fetch("/v1/classroom/posts/" + encodeURIComponent(postId) + "/image", { headers: headers() });
      })
      .then(function (response) {
        if (!response) return null;
        if (!response.ok) return null;
        return response.blob();
      })
      .then(function (blob) {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = function () {
          const view = sizeCanvas(canvas);
          paintBackground(view);
          view.ctx.drawImage(img, 0, 0, view.w, view.h);
          URL.revokeObjectURL(url);
        };
        img.src = url;
      })
      .catch(function (err) {
        setStatus(err.message || "That post could not be opened.");
      });
  }

  document.addEventListener("keydown", function (event) {
    const tag = event.target && event.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "BUTTON") return;
    if (!state.lesson) return;
    if (event.key === "h" || event.key === "H") {
      event.preventDefault();
      handBtn.click();
      return;
    }
    if (event.key === " " || event.key === "p" || event.key === "P") {
      event.preventDefault();
      if (state.paused) resumeInstructor();
      else pauseInstructor();
    }
  });

  window.addEventListener("resize", function () {
    paintScene(null);
  });

  if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = function () {
      window.speechSynthesis.getVoices();
    };
  }

  setAskingEnabled(false);
  paintScene(null);
  loadPosts();
  setStatus("Name a topic. The instructor will draw the lesson, then teach it.");
})();
