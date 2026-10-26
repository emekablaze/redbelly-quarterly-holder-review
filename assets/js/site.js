/* RBNT Holder Report: charts, live on-chain verification and page navigation.
   No dependencies. Every chart reads the JSON embedded in the page (#report-data); every value
   it shows is also in the table view next to it, so nothing depends on hovering. */
(() => {
  "use strict";
  const D = JSON.parse(document.getElementById("report-data").textContent);
  const NS = "http://www.w3.org/2000/svg";
  const RPC = "https://governors.mainnet.redbelly.network";
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  /* ---------------- formatting ---------------- */
  const fmt = {
    m(v, d = 1) {
      const a = Math.abs(v);
      if (a >= 1e9) return (v / 1e9).toFixed(2) + "B";
      if (a >= 1e6) return (v / 1e6).toFixed(d) + "M";
      if (a >= 1e3) return (v / 1e3).toFixed(1) + "K";
      return v.toFixed(0);
    },
    signed(v, f) { return (v > 0 ? "+" : v < 0 ? "−" : "±") + f(Math.abs(v)); },
    pct(v, d = 1) { return (v * 100).toFixed(d) + "%"; },
    int(v) { return Math.round(v).toLocaleString("en-US"); },
    rbnt(v) { return v.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + " RBNT"; },
  };

  /* ---------------- tiny SVG helper ---------------- */
  function svgEl(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function text(parent, x, y, str, cls, anchor = "start", extra = {}) {
    const t = svgEl("text", Object.assign({ x, y, class: cls, "text-anchor": anchor }, extra), parent);
    t.textContent = str;
    return t;
  }
  function measure(svg, str, cls) {
    const t = text(svg, -9999, -9999, str, cls);
    const w = t.getComputedTextLength();
    t.remove();
    return w;
  }
  /* horizontal bar: square at the baseline, 4px rounded data end */
  function hbarPath(x, y, w, h, toLeft = false) {
    if (w <= 0) return "";
    const r = Math.min(4, h / 2, w);
    if (!toLeft) return `M${x},${y}h${w - r}a${r},${r} 0 0 1 ${r},${r}v${h - 2 * r}a${r},${r} 0 0 1 -${r},${r}h-${w - r}z`;
    return `M${x},${y}h-${w - r}a${r},${r} 0 0 0 -${r},${r}v${h - 2 * r}a${r},${r} 0 0 0 ${r},${r}h${w - r}z`;
  }
  function vbarPath(x, base, w, h, down = false) {
    if (h <= 0) return "";
    const r = Math.min(4, w / 2, h);
    if (!down) return `M${x},${base}v-${h - r}a${r},${r} 0 0 1 ${r},-${r}h${w - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${h - r}z`;
    return `M${x},${base}v${h - r}a${r},${r} 0 0 0 ${r},${r}h${w - 2 * r}a${r},${r} 0 0 0 ${r},-${r}v-${h - r}z`;
  }
  function niceMax(v) {
    const raw = v / 4, p = Math.pow(10, Math.floor(Math.log10(raw)));
    for (const m of [1, 1.5, 2, 2.5, 3, 5, 10]) if (m * p >= raw) return 4 * m * p;
    return 40 * p;
  }

  /* ---------------- tooltip ---------------- */
  const tip = document.createElement("div");
  tip.className = "tip"; tip.setAttribute("role", "tooltip"); tip.id = "chart-tip";
  document.body.appendChild(tip);
  function fillTip(c) {
    tip.replaceChildren();
    if (c.title) { const t = document.createElement("div"); t.className = "tt"; t.textContent = c.title; tip.appendChild(t); }
    for (const r of c.rows || []) {
      const row = document.createElement("div"); row.className = "row";
      const i = document.createElement("i"); if (r.cls) i.className = "bg-" + r.cls; row.appendChild(i);
      const b = document.createElement("b"); b.textContent = r.value; row.appendChild(b);
      const s = document.createElement("span"); s.textContent = r.label; row.appendChild(s);
      tip.appendChild(row);
    }
    if (c.note) { const n = document.createElement("div"); n.className = "note"; n.textContent = c.note; tip.appendChild(n); }
  }
  function placeTip(x, y) {
    const r = tip.getBoundingClientRect();
    let left = x + 14, top = y + 14;
    if (left + r.width > window.innerWidth - 8) left = x - r.width - 14;
    if (top + r.height > window.innerHeight - 8) top = y - r.height - 14;
    tip.style.left = Math.max(8, left) + "px"; tip.style.top = Math.max(8, top) + "px";
  }
  function showTip(c, x, y) { fillTip(c); tip.classList.add("on"); placeTip(x, y); }
  function hideTip() { tip.classList.remove("on"); }
  /* make a mark (or its hit area) answer to pointer and keyboard */
  function bindTip(node, content, group) {
    node.setAttribute("tabindex", "0");
    node.setAttribute("role", "img");
    const c = content();
    node.setAttribute("aria-label", [c.title, ...(c.rows || []).map(r => `${r.label}: ${r.value}`), c.note || ""].filter(Boolean).join(". "));
    node.addEventListener("pointermove", e => showTip(content(), e.clientX, e.clientY));
    node.addEventListener("pointerleave", hideTip);
    node.addEventListener("focus", () => {
      const b = node.getBoundingClientRect();
      showTip(content(), b.right, b.top);
      if (group) { group.classList.add("has-focus"); node.classList.add("is-focus"); }
    });
    node.addEventListener("blur", () => { hideTip(); if (group) { group.classList.remove("has-focus"); node.classList.remove("is-focus"); } });
  }
  window.addEventListener("scroll", hideTip, { passive: true });

  /* ---------------- charts ---------------- */
  const CHARTS = {};

  /* paired horizontal bars: start (comparison) vs end (highlight) per row */
  CHARTS.paired = (box, cfg) => {
    const W = box.clientWidth, stacked = W < 560;
    const svg = svgEl("svg", { width: W, role: "group" });
    box.appendChild(svg);
    const labelW = stacked ? 0 : Math.min(240, Math.max(...cfg.rows.map(r => measure(svg, r.label, "t-label"))) + 16);
    const valW = 120, bh = 10, gap = 3;
    const rowH = stacked ? 58 : 44;
    const plotX = labelW, plotW = Math.max(60, W - labelW - valW);
    const max = Math.max(...cfg.rows.flatMap(r => [r.a, r.b])) || 1;
    let y = 4;
    for (const r of cfg.rows) {
      const g = svgEl("g", { class: "mark-group" }, svg);
      let by = y;
      if (stacked) { text(g, 0, y + 12, r.label, "t-label"); by = y + 22; }
      else text(g, labelW - 14, y + bh + 4, r.label, "t-label", "end");
      const wa = plotW * r.a / max, wb = plotW * r.b / max;
      svgEl("path", { d: hbarPath(plotX, by, wa, bh), class: "mark m-base grow-x" }, g);
      svgEl("path", { d: hbarPath(plotX, by + bh + gap, wb, bh), class: "mark m-accent grow-x" }, g);
      text(g, plotX + wb + 8, by + 2 * bh + gap - 1, cfg.label ? cfg.label(r) : fmt.m(r.b), "t-val");
      const hit = svgEl("rect", { x: 0, y: y - 4, width: W, height: rowH - 4, class: "hit" }, g);
      bindTip(hit, () => ({ title: r.label, rows: [
        { cls: "base", label: cfg.aName, value: cfg.tipFmt ? cfg.tipFmt(r.a, r, "a") : fmt.m(r.a) },
        { cls: "accent", label: cfg.bName, value: cfg.tipFmt ? cfg.tipFmt(r.b, r, "b") : fmt.m(r.b) }],
        note: r.note || (cfg.changeFmt ? "Change: " + cfg.changeFmt(r) : "") }), svg);
      y += rowH;
    }
    svg.setAttribute("height", y);
  };

  /* single-series horizontal bars */
  CHARTS.bars = (box, cfg) => {
    const W = box.clientWidth, stacked = W < 480 || cfg.stacked;
    const svg = svgEl("svg", { width: W, role: "group" });
    box.appendChild(svg);
    const labelW = stacked ? 0 : Math.min(220, Math.max(...cfg.rows.map(r => measure(svg, r.label, "t-label"))) + 16);
    const valW = cfg.valW || 90, bh = 16, rowH = stacked ? 48 : 32;
    const plotW = Math.max(40, W - labelW - valW), max = Math.max(...cfg.rows.map(r => r.v)) || 1;
    let y = 2;
    for (const r of cfg.rows) {
      const g = svgEl("g", { class: "mark-group" }, svg);
      let by = y;
      if (stacked) { text(g, 0, y + 12, r.label, "t-label"); by = y + 20; }
      else text(g, labelW - 14, y + bh - 3, r.label, "t-label", "end");
      const w = Math.max(r.v > 0 ? 2 : 0, plotW * r.v / max);
      svgEl("path", { d: hbarPath(labelW, by, w, bh), class: "mark grow-x " + (r.cls || cfg.cls || "m-accent") }, g);
      text(g, labelW + w + 8, by + bh - 4, cfg.label(r), "t-val");
      const hit = svgEl("rect", { x: 0, y: y - 2, width: W, height: rowH - 2, class: "hit" }, g);
      bindTip(hit, () => cfg.tip(r), svg);
      y += rowH;
    }
    svg.setAttribute("height", y);
  };

  /* diverging bars around zero: increases right (highlight), decreases left (comparison) */
  CHARTS.diverging = (box, cfg) => {
    const W = box.clientWidth, stacked = W < 560;
    const svg = svgEl("svg", { width: W, role: "group" });
    box.appendChild(svg);
    const labelW = stacked ? 0 : Math.min(230, Math.max(...cfg.rows.map(r => measure(svg, r.label, "t-label"))) + 16);
    const bh = 16, rowH = stacked ? 50 : 32, room = 76;
    const plotX = labelW + room, plotW = Math.max(80, W - labelW - 2 * room);
    const max = Math.max(...cfg.rows.map(r => Math.abs(r.v))) || 1;
    const hasNeg = cfg.rows.some(r => r.v < 0), hasPos = cfg.rows.some(r => r.v > 0);
    const zero = hasNeg && hasPos ? plotX + plotW / 2 : hasNeg ? plotX + plotW : plotX;
    const half = hasNeg && hasPos ? plotW / 2 : plotW;
    let y = 4;
    for (const r of cfg.rows) {
      const g = svgEl("g", { class: "mark-group" }, svg);
      let by = y;
      if (stacked) { text(g, 0, y + 12, r.label, "t-label"); by = y + 20; }
      else text(g, labelW - 14, y + bh - 3, r.label, "t-label", "end");
      const w = half * Math.abs(r.v) / max;
      const lbl = Math.abs(r.v) < 0.5 ? "no change" : fmt.signed(r.v, cfg.f || fmt.m);
      if (r.v >= 0) {
        svgEl("path", { d: hbarPath(zero, by, w, bh), class: "mark m-accent grow-x" }, g);
        text(g, zero + w + 8, by + bh - 4, lbl, "t-val");
      } else {
        svgEl("path", { d: hbarPath(zero, by, w, bh, true), class: "mark m-base grow-x-r" }, g);
        text(g, zero - w - 8, by + bh - 4, lbl, "t-val", "end");
      }
      const hit = svgEl("rect", { x: 0, y: y - 2, width: W, height: rowH - 2, class: "hit" }, g);
      bindTip(hit, () => cfg.tip ? cfg.tip(r) : { title: r.label, rows: [{ cls: r.v >= 0 ? "accent" : "base", label: "Change over the quarter", value: lbl }] }, svg);
      y += rowH;
    }
    svgEl("line", { x1: zero, x2: zero, y1: 0, y2: y, class: "axis-line" }, svg);
    svg.setAttribute("height", y);
  };

  /* grouped columns: start vs end per category */
  CHARTS.columns = (box, cfg) => {
    const W = box.clientWidth, H = cfg.height || 260;
    const svg = svgEl("svg", { width: W, height: H, role: "group" });
    box.appendChild(svg);
    const top = 26, bottom = 34, left = 40;
    const plotH = H - top - bottom, base = top + plotH;
    const n = cfg.cats.length, slot = (W - left) / n;
    const bw = Math.min(24, (slot - 28) / 2), gap = 6;
    const max = cfg.max || niceMax(Math.max(...cfg.cats.flatMap(c => [c.a, c.b])));
    for (let i = 0; i <= 4; i++) {
      const v = max * i / 4, yy = base - plotH * i / 4;
      svgEl("line", { x1: left, x2: W, y1: yy, y2: yy, class: i ? "grid-line" : "axis-line" }, svg);
      text(svg, left - 8, yy + 4, cfg.tick(v), "t-muted", "end");
    }
    cfg.cats.forEach((c, i) => {
      const g = svgEl("g", { class: "mark-group" }, svg);
      const cx = left + slot * i + slot / 2, x0 = cx - bw - gap / 2;
      const ha = plotH * c.a / max, hb = plotH * c.b / max;
      svgEl("path", { d: vbarPath(x0, base, bw, ha), class: "mark m-base grow-y" }, g);
      svgEl("path", { d: vbarPath(x0 + bw + gap, base, bw, hb), class: "mark m-accent grow-y" }, g);
      text(g, x0 + bw + gap + bw / 2, base - hb - 7, cfg.label(c.b), "t-val", "middle");
      text(g, cx, base + 20, c.label, "t-muted", "middle");
      const hit = svgEl("rect", { x: cx - slot / 2, y: top - 10, width: slot, height: plotH + bottom, class: "hit" }, g);
      bindTip(hit, () => ({ title: c.label, rows: [{ cls: "base", label: cfg.aName, value: cfg.label(c.a) }, { cls: "accent", label: cfg.bName, value: cfg.label(c.b) }], note: c.note }), svg);
    });
  };

  /* 100% stacked horizontal bars */
  CHARTS.stacked = (box, cfg) => {
    const W = box.clientWidth, stacked = W < 560;
    const svg = svgEl("svg", { width: W, role: "group" });
    box.appendChild(svg);
    const labelW = stacked ? 0 : Math.min(160, Math.max(...cfg.rows.map(r => measure(svg, r.label, "t-label"))) + 16);
    const bh = 22, rowH = stacked ? 56 : 38, plotW = W - labelW;
    let y = 4;
    for (const r of cfg.rows) {
      let by = y;
      if (stacked) { text(svg, 0, y + 12, r.label, "t-label"); by = y + 22; }
      else text(svg, labelW - 14, y + bh / 2 + 5, r.label, "t-label", "end");
      const tot = cfg.segs.reduce((s, k) => s + r[k.key], 0) || 1;
      let x = labelW;
      const g = svgEl("g", { class: "mark-group" }, svg);
      cfg.segs.forEach((s, j) => {
        const v = r[s.key], w = plotW * v / tot;
        if (w <= 0) return;
        const last = j === cfg.segs.length - 1 || cfg.segs.slice(j + 1).every(k => !r[k.key]);
        const first = x === labelW;
        const ww = Math.max(0.5, w - (last ? 0 : 2));
        const rx = svgEl("rect", { x, y: by, width: ww, height: bh, rx: (first || last) ? 3 : 0, class: "mark grow-x " + s.cls }, g);
        const lab = `${v}`;
        if (ww > measure(svg, lab, "t-in") + 12) text(g, x + ww / 2, by + bh / 2 + 4, lab, "t-in " + (s.cls === "m-neutral" ? "on-neutral" : "on-fill"), "middle");
        bindTip(rx, () => ({ title: r.label, rows: cfg.segs.map(k => ({ cls: k.cls.replace("m-", ""), label: k.name, value: `${r[k.key]} wallets (${fmt.pct(r[k.key] / tot, 0)})` })), note: r.note }), svg);
        x += w;
      });
      y += rowH;
    }
    svg.setAttribute("height", y);
  };

  /* daily line chart with crosshair; zero-based y so changes are not exaggerated */
  CHARTS.lines = (box, cfg) => {
    const W = box.clientWidth, H = cfg.height || 300;
    const svg = svgEl("svg", { width: W, height: H, role: "group" });
    box.appendChild(svg);
    const narrow = W < 560;
    const top = 16, bottom = 30, left = 52, right = narrow ? 12 : 120;
    const plotW = W - left - right, plotH = H - top - bottom, base = top + plotH;
    const n = cfg.dates.length;
    const max = niceMax(Math.max(...cfg.series.flatMap(s => s.values)) * 1.05);
    const X = i => left + plotW * i / (n - 1), Y = v => base - plotH * v / max;
    for (let i = 0; i <= 4; i++) {
      const v = max * i / 4, yy = Y(v);
      svgEl("line", { x1: left, x2: left + plotW, y1: yy, y2: yy, class: i ? "grid-line" : "axis-line" }, svg);
      text(svg, left - 8, yy + 4, cfg.tick(v), "t-muted", "end");
    }
    const ticks = cfg.xTicks || [];
    for (const t of ticks) {
      const i = cfg.dates.indexOf(t.date); if (i < 0) continue;
      text(svg, X(i), base + 20, t.label, "t-muted", i === 0 ? "start" : i === n - 1 ? "end" : "middle");
    }
    for (const s of cfg.series) {
      const d = s.values.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join("");
      if (s.area) svgEl("path", { d: `${d}L${X(n - 1)},${base}L${X(0)},${base}Z`, fill: `var(--c-${s.cls})`, opacity: .1 }, svg);
      const p = svgEl("path", { d, fill: "none", class: "l-" + s.cls + " draw", "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
      const len = p.getTotalLength();
      p.style.strokeDasharray = len; p.style.strokeDashoffset = box.closest(".in") || reduceMotion ? 0 : len;
      p.dataset.len = len;
      svgEl("circle", { cx: X(n - 1), cy: Y(s.values[n - 1]), r: 4, class: "dot", fill: `var(--c-${s.cls})` }, svg);
      if (!narrow) {
        text(svg, X(n - 1) + 10, Y(s.values[n - 1]) - 2, cfg.tick(s.values[n - 1], true), "t-val");
        text(svg, X(n - 1) + 10, Y(s.values[n - 1]) + 13, s.label, "t-val-muted");
      }
    }
    for (const a of cfg.annotations || []) {
      const i = cfg.dates.indexOf(a.date); if (i < 0) continue;
      svgEl("line", { x1: X(i), x2: X(i), y1: top, y2: base, class: "grid-line" }, svg);
      const fits = X(i) + 6 + measure(svg, a.label, "t-muted") <= left + plotW;
      text(svg, fits ? X(i) + 6 : X(i) - 6, top + 10, a.label, "t-muted", fits ? "start" : "end");
    }
    /* crosshair layer */
    const cross = svgEl("line", { x1: 0, x2: 0, y1: top, y2: base, class: "crosshair", opacity: 0 }, svg);
    const dots = cfg.series.map(s => svgEl("circle", { r: 4, class: "dot", fill: `var(--c-${s.cls})`, opacity: 0 }, svg));
    const hit = svgEl("rect", { x: left, y: top, width: plotW, height: plotH, class: "hit", tabindex: 0, role: "img",
      "aria-label": cfg.aria }, svg);
    let cur = n - 1;
    const content = i => ({ title: cfg.dateLabel(cfg.dates[i]), rows: cfg.series.map(s => ({ cls: s.cls, label: s.label, value: cfg.tick(s.values[i], true) }))
      .concat(cfg.total ? [{ label: "Total", value: cfg.tick(cfg.series.reduce((t, s) => t + s.values[i], 0), true) }] : []) });
    const show = (i, cx, cy) => {
      cur = i;
      cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("opacity", 1);
      dots.forEach((dt, k) => { dt.setAttribute("cx", X(i)); dt.setAttribute("cy", Y(cfg.series[k].values[i])); dt.setAttribute("opacity", 1); });
      showTip(content(i), cx, cy);
    };
    const hide = () => { cross.setAttribute("opacity", 0); dots.forEach(dt => dt.setAttribute("opacity", 0)); hideTip(); };
    hit.addEventListener("pointermove", e => {
      const b = svg.getBoundingClientRect();
      const i = Math.max(0, Math.min(n - 1, Math.round((e.clientX - b.left - left) / plotW * (n - 1))));
      show(i, e.clientX, e.clientY);
    });
    hit.addEventListener("pointerleave", hide);
    hit.addEventListener("blur", hide);
    hit.addEventListener("focus", () => { const b = svg.getBoundingClientRect(); show(cur, b.left + X(cur), b.top + top); });
    hit.addEventListener("keydown", e => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      const i = Math.max(0, Math.min(n - 1, cur + (e.key === "ArrowRight" ? 1 : -1)));
      const b = svg.getBoundingClientRect(); show(i, b.left + X(i), b.top + top);
    });
  };

  /* waterfall: opening total, increases, decreases, closing total */
  CHARTS.waterfall = (box, cfg) => {
    const W = box.clientWidth, H = cfg.height || 280;
    const svg = svgEl("svg", { width: W, height: H, role: "group" });
    box.appendChild(svg);
    const top = 28, bottom = 40, left = 52;
    const plotH = H - top - bottom, base = top + plotH;
    const n = cfg.steps.length, slot = (W - left) / n, bw = Math.min(56, slot * .5);
    let run = 0, maxv = 0;
    const geo = cfg.steps.map(s => {
      let lo, hi;
      if (s.kind === "total") { lo = 0; hi = s.value; run = s.value; }
      else if (s.value >= 0) { lo = run; hi = run + s.value; run = hi; }
      else { hi = run; lo = run + s.value; run = lo; }
      maxv = Math.max(maxv, hi);
      return { lo, hi };
    });
    const max = niceMax(maxv * 1.05), Y = v => base - plotH * v / max;
    for (let i = 0; i <= 4; i++) {
      const v = max * i / 4;
      svgEl("line", { x1: left, x2: W, y1: Y(v), y2: Y(v), class: i ? "grid-line" : "axis-line" }, svg);
      text(svg, left - 8, Y(v) + 4, cfg.tick(v), "t-muted", "end");
    }
    const g = svgEl("g", { class: "mark-group" }, svg);
    cfg.steps.forEach((s, i) => {
      const cx = left + slot * i + slot / 2, x = cx - bw / 2;
      const { lo, hi } = geo[i];
      const cls = s.kind === "total" ? "m-strong" : s.value >= 0 ? "m-accent" : "m-base";
      const rect = svgEl("rect", { x, y: Y(hi), width: bw, height: Math.max(1, Y(lo) - Y(hi)), rx: 3, class: "mark grow-y " + cls }, g);
      const lbl = s.kind === "total" ? cfg.tick(s.value, true) : fmt.signed(s.value, v => cfg.tick(v, true));
      text(svg, cx, Y(hi) - 8, lbl, "t-val", "middle");
      text(svg, cx, base + 18, s.label, "t-muted", "middle");
      if (s.sub) text(svg, cx, base + 32, s.sub, "t-val-muted", "middle");
      if (i < n - 1) {
        const level = s.kind === "total" ? s.value : s.value >= 0 ? hi : lo;
        svgEl("line", { x1: x + bw, x2: cx + slot - bw / 2, y1: Y(level), y2: Y(level), class: "crosshair", opacity: .6 }, svg);
      }
      bindTip(rect, () => ({ title: s.label, rows: [{ cls: cls.replace("m-", ""), label: s.tipLabel || s.label, value: lbl + " RBNT" }], note: s.note }), g);
    });
  };

  /* sparkline for stat tiles: de-emphasised line, current point in the accent */
  CHARTS.spark = (box, cfg) => {
    const W = box.clientWidth, H = box.clientHeight || 36;
    const svg = svgEl("svg", { width: W, height: H, "aria-hidden": "true" });
    box.appendChild(svg);
    const v = cfg.values, n = v.length, lo = Math.min(...v), hi = Math.max(...v);
    const pad = 4, X = i => pad + (W - 2 * pad) * i / (n - 1), Y = x => H - pad - (H - 2 * pad) * (hi === lo ? .5 : (x - lo) / (hi - lo));
    const d = v.map((x, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(x).toFixed(1)}`).join("");
    if (cfg.area) svgEl("path", { d: `${d}L${X(n - 1)},${H}L${X(0)},${H}Z`, fill: "var(--c-accent)", opacity: .12 }, svg);
    svgEl("path", { d, fill: "none", stroke: cfg.stroke || "var(--c-base)", "stroke-width": 2, "stroke-linejoin": "round" }, svg);
    svgEl("circle", { cx: X(n - 1), cy: Y(v[n - 1]), r: 4, fill: "var(--c-accent)", class: "dot" }, svg);
  };

  /* ---------------- chart registry (configs built from the embedded data) ---------------- */
  const dateLabel = d => new Date(d + "T12:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
  const xTicks = [["2026-06-30", "1 Jul"], ["2026-07-31", "1 Aug"], ["2026-08-31", "1 Sep"], ["2026-09-30", "1 Oct"]].map(([date, label]) => ({ date, label }));
  const mt = (v, full) => full ? fmt.m(v, 1) : fmt.m(v, 0);
  const CONFIGS = {
    supply: box => CHARTS.paired(box, {
      rows: D.supply.map(r => ({ label: r.label, a: r.start, b: r.end, r })),
      aName: "1 Jul 2026", bName: "30 Sep 2026",
      label: r => `${fmt.m(r.b)} · ${fmt.pct(r.r.share_end, r.r.share_end < .01 ? 2 : 1)}`,
      tipFmt: (v, r, k) => { const sh = k === "a" ? r.r.share_start : r.r.share_end; return `${fmt.m(v)} (${fmt.pct(sh, sh < .01 ? 2 : 1)})`; },
      changeFmt: r => fmt.signed(r.b - r.a, fmt.m) }),
    supplyChange: box => CHARTS.diverging(box, { rows: D.supply_change.map(r => ({ label: r.label, v: r.value })) }),
    topn: box => CHARTS.columns(box, { cats: D.topn.map(r => ({ label: r.label, a: r.start, b: r.end })), max: 1,
      tick: v => Math.round(v * 100) + "%", label: v => fmt.pct(v), aName: "1 Jul 2026", bName: "30 Sep 2026" }),
    bandsCount: box => CHARTS.bars(box, { rows: D.bands.map(b => ({ label: b.band, v: b.wallets_end, b })), cls: "m-base",
      label: r => fmt.int(r.v),
      tip: r => ({ title: r.label + " RBNT", rows: [{ cls: "base", label: "Wallets on 1 Jul", value: fmt.int(r.b.wallets_start) }, { cls: "base", label: "Wallets on 30 Sep", value: fmt.int(r.b.wallets_end) }] }) }),
    bandsShare: box => CHARTS.bars(box, { rows: D.bands.map(b => ({ label: b.band, v: b.share_end, b })), cls: "m-accent",
      label: r => fmt.pct(r.v, r.v < 0.01 ? 2 : 1),
      tip: r => ({ title: r.label + " RBNT", rows: [{ cls: "accent", label: "Share of unnamed-wallet RBNT, 30 Sep", value: fmt.pct(r.b.share_end, 2) }, { cls: "accent", label: "RBNT held, 30 Sep", value: fmt.m(r.b.rbnt_end) }] }) }),
    tiers: box => CHARTS.stacked(box, { rows: D.tiers.map(t => ({ label: t.tier, grew: t.grew, same: t.about_same, shrank: t.shrank, note: `${t.emptied} emptied (below 1 RBNT)` })),
      segs: [{ key: "grew", name: "Grew (more than +1%)", cls: "m-accent" }, { key: "same", name: "About the same (±1%)", cls: "m-neutral" }, { key: "shrank", name: "Shrank (more than −1%)", cls: "m-base" }] }),
    tierChange: box => CHARTS.diverging(box, { rows: D.tiers.map(t => ({ label: t.tier, v: t.change, t })),
      tip: r => ({ title: `${r.label} (${r.t.wallets} wallets)`, rows: [{ cls: "base", label: "Held on 1 Jul", value: fmt.m(r.t.start) }, { cls: "accent", label: "Held on 30 Sep", value: fmt.m(r.t.end) }], note: `Change ${fmt.signed(r.v, fmt.m)} (${fmt.signed(r.t.change_pct, x => fmt.pct(x))})` }) }),
    stakingDaily: box => CHARTS.lines(box, { dates: D.daily.dates, height: 320, xTicks, dateLabel: d => "End of " + dateLabel(d), total: true,
      series: [{ label: "No-lock pool", cls: "accent", values: D.daily.nolock }, { label: "365-day pool", cls: "base", values: D.daily.lock365 }],
      annotations: D.staking_jump ? [{ date: D.staking_jump.date, label: D.staking_jump.label }] : [], tick: mt, aria: "Daily RBNT staked in each Reddex pool through the quarter. Use left and right arrow keys to move between days." }),
    waterfall: box => CHARTS.waterfall(box, { steps: D.waterfall, tick: mt }),
    vestingDaily: box => CHARTS.lines(box, { dates: D.daily.dates, height: 220, xTicks, dateLabel: d => "End of " + dateLabel(d),
      series: [{ label: "Vesting contracts", cls: "base", values: D.daily.vesting, area: true }], tick: mt,
      aria: "Daily RBNT held by the token vesting contracts through the quarter." }),
    bridgeDaily: box => CHARTS.lines(box, { dates: D.daily.dates, height: 220, xTicks, dateLabel: d => "End of " + dateLabel(d),
      series: [{ label: "Bridge adapter", cls: "base", values: D.daily.bridge, area: true }], tick: mt,
      aria: "Daily RBNT locked in the bridge adapter through the quarter." }),
    reserved: box => CHARTS.diverging(box, { rows: D.reserved.map(r => ({ label: r.wallet, v: r.change, r })),
      tip: r => ({ title: r.label, rows: [{ cls: "base", label: "1 Jul 2026", value: fmt.m(r.r.start) }, { cls: "accent", label: "30 Sep 2026", value: fmt.m(r.r.end) }], note: Math.abs(r.v) < .5 ? "No change" : "Change " + fmt.signed(r.v, fmt.m) }) }),
    ecoOut: box => CHARTS.bars(box, { rows: D.eco_out.map(r => ({ label: r.label, v: r.value, r })), cls: "m-base", valW: 110,
      label: r => fmt.m(r.v, 2), tip: r => ({ title: r.label, rows: [{ cls: "base", label: "RBNT sent in Q3", value: fmt.rbnt(r.v) }], note: r.r.note }) }),
  };
  /* stat-tile sparklines */
  const SPARKS = {
    staked: { values: D.daily.nolock.map((v, i) => v + D.daily.lock365[i]), area: true, stroke: "var(--c-accent)" },
    vesting: { values: D.daily.vesting }, bridge: { values: D.daily.bridge }, wrbnt: { values: D.daily.wrbnt },
  };

  function renderAll() {
    for (const box of $$("[data-chart]")) {
      const f = CONFIGS[box.dataset.chart]; if (!f) continue;
      box.replaceChildren(); f(box);
    }
    for (const box of $$("[data-spark]")) { box.replaceChildren(); CHARTS.spark(box, SPARKS[box.dataset.spark]); }
  }

  /* ---------------- chart / table toggle ---------------- */
  for (const seg of $$(".seg")) {
    seg.addEventListener("click", e => {
      const b = e.target.closest("button"); if (!b) return;
      const card = seg.closest(".card");
      $$("button", seg).forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
      const table = b.dataset.view === "table";
      $$(".chart-view", card).forEach(x => x.hidden = table);
      $$(".table-view", card).forEach(x => x.hidden = !table);
    });
  }

  /* ---------------- reveal + grow-in ---------------- */
  function markIn(n) {
    n.classList.add("in");
    for (const p of $$(".draw", n)) p.style.strokeDashoffset = 0;
  }
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { markIn(e.target); io.unobserve(e.target); } }), { threshold: .18 });
    $$(".reveal, .anim").forEach(n => io.observe(n));
  } else $$(".reveal, .anim").forEach(markIn);

  /* ---------------- section index: scroll-spy ---------------- */
  const links = $$('.toc a[href^="#"], .top-nav a[href^="#"]');
  const sections = Array.from(new Set(links.map(a => a.getAttribute("href")))).map(h => $(h)).filter(Boolean);
  function spy() {
    /* the section whose top has passed 30% of the viewport, furthest down the page */
    const y = window.scrollY + window.innerHeight * .3;
    let cur = null;
    for (const s of sections) if (s.offsetTop <= y && (!cur || s.offsetTop > cur.offsetTop)) cur = s;
    for (const a of links) a.classList.toggle("active", a.getAttribute("href") === "#" + (cur && cur.id));
    $(".to-top").classList.toggle("on", window.scrollY > 900);
  }
  let ticking = false;
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { spy(); ticking = false; }); } }, { passive: true });

  /* ---------------- mobile sheet ---------------- */
  const sheet = $(".sheet");
  const openSheet = open => { sheet.classList.toggle("open", open); $(".menu-btn").setAttribute("aria-expanded", open); if (open) $("a", sheet).focus(); };
  $(".menu-btn").addEventListener("click", () => openSheet(true));
  sheet.addEventListener("click", e => { if (e.target.closest("a") || e.target.classList.contains("scrim") || e.target.closest(".close")) openSheet(false); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") openSheet(false); });

  /* ---------------- theme ---------------- */
  const root = document.documentElement;
  $(".theme-btn").addEventListener("click", () => {
    const next = root.dataset.theme === "light" ? "dark" : "light";
    root.dataset.theme = next;
    try { localStorage.setItem("rbnt-theme", next); } catch (e) { /* storage may be unavailable */ }
    $('meta[name="theme-color"]').setAttribute("content", next === "light" ? "#EDF1F4" : "#0c1317");
  });

  /* ---------------- copy buttons + toast ---------------- */
  const toast = $(".toast");
  let toastT;
  function say(msg) { toast.textContent = msg; toast.classList.add("on"); clearTimeout(toastT); toastT = setTimeout(() => toast.classList.remove("on"), 1800); }
  async function copy(str) {
    try { await navigator.clipboard.writeText(str); say("Copied"); }
    catch (e) { say("Copy not available in this browser"); }
  }
  document.addEventListener("click", e => {
    const c = e.target.closest("[data-copy]");
    if (c) { e.preventDefault(); copy(c.dataset.copy); }
    const t = e.target.closest("[data-copy-from]");
    if (t) { e.preventDefault(); copy($(t.dataset.copyFrom).textContent.trim()); }
  });

  /* ---------------- live on-chain verification ---------------- */
  const dlg = $("#verify-dialog");
  function formatWei(w) {
    const neg = w < 0n; if (neg) w = -w;
    const whole = w / 10n ** 18n, frac = (w % 10n ** 18n).toString().padStart(18, "0").slice(0, 6);
    return (neg ? "−" : "") + whole.toLocaleString("en-US") + "." + frac;
  }
  function openVerify(spec) {
    $("#v-title").textContent = spec.label;
    $("#v-what").textContent = spec.what;
    $("#v-method").textContent = spec.method;
    $("#v-block").textContent = `${spec.block.toLocaleString("en-US")} (${spec.blockLabel})`;
    $("#v-expect").textContent = formatWei(BigInt(spec.expect)) + " RBNT";
    const body = { jsonrpc: "2.0", id: 1, method: spec.method, params: spec.params };
    $("#v-curl").textContent = `curl -s -X POST ${RPC} \\\n  -H 'content-type: application/json' \\\n  -d '${JSON.stringify(body)}'`;
    const res = $("#v-result"); res.replaceChildren();
    const s = document.createElement("span"); s.className = "status"; s.textContent = "Not run yet";
    res.appendChild(s);
    dlg.dataset.spec = JSON.stringify(spec);
    dlg.showModal();
  }
  async function runVerify() {
    const spec = JSON.parse(dlg.dataset.spec);
    const res = $("#v-result"); res.replaceChildren();
    const s = document.createElement("span"); s.className = "status"; s.textContent = "Asking the chain…"; res.appendChild(s);
    try {
      const r = await fetch(RPC, { method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: spec.method, params: spec.params }) });
      const j = await r.json();
      if (j.error) throw new Error(j.error.message);
      const hex = spec.method === "eth_call" ? "0x" + j.result.slice(2, 66) : j.result;
      const got = BigInt(hex), ok = got === BigInt(spec.expect);
      s.className = "status " + (ok ? "ok" : "bad");
      s.textContent = ok ? "MATCH" : "DIFFERENT";
      const v = document.createElement("span"); v.className = "mono";
      v.textContent = `${formatWei(got)} RBNT returned by the chain`;
      res.appendChild(v);
    } catch (err) {
      s.className = "status warn"; s.textContent = "Could not reach the RPC";
      const v = document.createElement("span"); v.textContent = "Copy the command below and run it in a terminal instead.";
      res.appendChild(v);
    }
  }
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-verify]");
    if (b) openVerify(JSON.parse(b.dataset.verify));
  });
  if (dlg) {
    $("#v-run").addEventListener("click", runVerify);
    $("#v-close").addEventListener("click", () => dlg.close());
    dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
  }

  /* ---------------- boot ---------------- */
  renderAll();
  spy();
  let rw = window.innerWidth, rt;
  window.addEventListener("resize", () => {
    if (window.innerWidth === rw) return;
    rw = window.innerWidth; clearTimeout(rt);
    rt = setTimeout(renderAll, 150);
  });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(renderAll);
})();
