# Static SVG charts in the Task Board brand: one accent (brand red) against slate neutrals.
# Every chart carries direct labels so no value depends on colour alone.
from html import escape

RED = "#EF5350"      # brand red: the quarter-end / highlighted series
SLATE = "#596975"    # slate: the quarter-start / comparison series
INK = "#0F1A22"      # primary text (light theme)
MUTED = "#596975"    # secondary text
GRID = "#DAE1E7"     # hairline grid
SURFACE = "#FFFFFF"
FONT = "'Be Vietnam Pro', system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, monospace"


def fmt_m(v, digits=1):
    """Format a token amount in millions/thousands for labels."""
    a = abs(v)
    if a >= 1e9: s = f"{v/1e9:.2f}B"
    elif a >= 1e6: s = f"{v/1e6:.{digits}f}M"
    elif a >= 1e3: s = f"{v/1e3:.0f}K"
    else: s = f"{v:.0f}"
    return s


def _text(x, y, s, size=12, anchor="start", fill=INK, weight=400, mono=False):
    fam = MONO if mono else FONT
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')


def legend(items, x, y):
    out, cx = [], x
    for label, color in items:
        out.append(f'<rect x="{cx}" y="{y-9}" width="10" height="10" rx="2" fill="{color}"/>')
        out.append(_text(cx + 15, y, label, 12, fill=MUTED))
        cx += 22 + 7.2 * len(label)
    return "".join(out)


def _bar(x, y, w, h, color):
    """Horizontal bar, square at the baseline, 4px rounded data end."""
    if w <= 0.5: return ""
    r = min(4, h / 2, w)
    return (f'<path d="M{x:.1f},{y:.1f} h{w-r:.1f} a{r},{r} 0 0 1 {r},{r} v{h-2*r:.1f} '
            f'a{r},{r} 0 0 1 -{r},{r} h-{w-r:.1f} z" fill="{color}"/>')


def paired_hbar(rows, title_id, width=760, label_w=230, unit_fmt=fmt_m, start_label="1 Jul 2026", end_label="30 Sep 2026"):
    """rows: [(label, start_value, end_value)]. Two thin bars per row: start (slate), end (red)."""
    bh, gap, row_h = 11, 2, 40
    top = 34
    h = top + row_h * len(rows) + 10
    vmax = max(max(s, e) for _, s, e in rows) or 1
    plot_w = width - label_w - 90
    o = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-labelledby="{title_id}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{width}" height="{h}" fill="{SURFACE}"/>',
         legend([(start_label, SLATE), (end_label, RED)], label_w, 16)]
    for i, (lab, s, e) in enumerate(rows):
        y = top + i * row_h
        o.append(_text(label_w - 12, y + bh + 4, lab, 13, "end"))
        ws, we = plot_w * s / vmax, plot_w * e / vmax
        o.append(_bar(label_w, y, ws, bh, SLATE))
        o.append(_bar(label_w, y + bh + gap, we, bh, RED))
        o.append(_text(label_w + ws + 6, y + bh - 1, unit_fmt(s), 11, fill=MUTED, mono=True))
        o.append(_text(label_w + we + 6, y + 2 * bh + gap - 1, unit_fmt(e), 11, fill=INK, mono=True))
    o.append(f'<line x1="{label_w}" x2="{label_w}" y1="{top-6}" y2="{h-8}" stroke="{GRID}" stroke-width="1"/>')
    o.append("</svg>")
    return "".join(o)


def diverging_hbar(rows, title_id, width=760, label_w=230, unit_fmt=fmt_m):
    """rows: [(label, change)]. Increases to the right in red, decreases to the left in slate."""
    row_h, bh, top = 30, 14, 12
    h = top + row_h * len(rows) + 12
    vmax = max(abs(v) for _, v in rows) or 1
    plot_w = width - label_w - 40
    mid = label_w + plot_w / 2
    half = plot_w / 2 - 70
    o = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-labelledby="{title_id}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{width}" height="{h}" fill="{SURFACE}"/>']
    for i, (lab, v) in enumerate(rows):
        y = top + i * row_h
        o.append(_text(label_w - 12, y + bh - 2, lab, 13, "end"))
        w = half * abs(v) / vmax
        sign = "+" if v > 0 else ("−" if v < 0 else "±")
        txt = sign + unit_fmt(abs(v))
        if v >= 0:
            o.append(_bar(mid, y, w, bh, RED))
            o.append(_text(mid + w + 6, y + bh - 2, txt, 11, mono=True))
        else:
            o.append(f'<g transform="translate({2*mid:.1f},0) scale(-1,1)">{_bar(mid, y, w, bh, SLATE)}</g>')
            o.append(_text(mid - w - 6, y + bh - 2, txt, 11, "end", mono=True))
    o.append(f'<line x1="{mid}" x2="{mid}" y1="4" y2="{h-6}" stroke="{MUTED}" stroke-width="1"/>')
    o.append("</svg>")
    return "".join(o)


def stacked_share(cols, segments, title_id, width=760, bh=34, row_gap=26):
    """100% stacked horizontal bars. cols: [(label, {segment: value})]; segments: [(name, color)].
    Segment labels are drawn inside when they fit, and the legend carries the rest."""
    top, label_w = 40, 110
    h = top + len(cols) * (bh + row_gap) + 4
    plot_w = width - label_w - 10
    o = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-labelledby="{title_id}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{width}" height="{h}" fill="{SURFACE}"/>']
    # legend, wrapped across two lines if needed
    lx, ly = label_w, 14
    for name, color in segments:
        wlen = 22 + 6.9 * len(name)
        if lx + wlen > width: lx, ly = label_w, ly + 18
        o.append(f'<rect x="{lx}" y="{ly-9}" width="10" height="10" rx="2" fill="{color}"/>')
        o.append(_text(lx + 15, ly, name, 11.5, fill=MUTED)); lx += wlen + 6
    top = ly + 18
    h = top + len(cols) * (bh + row_gap) + 4
    o[0] = f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-labelledby="{title_id}" xmlns="http://www.w3.org/2000/svg">'
    o[1] = f'<rect width="{width}" height="{h}" fill="{SURFACE}"/>'
    for i, (lab, vals) in enumerate(cols):
        y = top + i * (bh + row_gap)
        tot = sum(vals.values())
        o.append(_text(label_w - 12, y + bh / 2 + 4, lab, 13, "end", weight=600))
        x = label_w
        for name, color in segments:
            v = vals.get(name, 0); w = plot_w * v / tot
            if w <= 0: continue
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w-2,0.5):.1f}" height="{bh}" rx="2" fill="{color}"/>')
            pct = f"{100*v/tot:.0f}%"
            dark = color in (RED, "#1d3140", "#3F4C6B", SLATE, "#0F1A22")
            if w > 34:
                o.append(_text(x + w / 2 - 1, y + bh / 2 + 4, pct, 11, "middle", fill="#FFFFFF" if dark else INK, weight=600, mono=True))
            x += w
    o.append("</svg>")
    return "".join(o)


def columns(cats, series, title_id, width=760, height=260, unit_fmt=lambda v: f"{v:,.0f}"):
    """Grouped columns. cats: [label]; series: [(name, color, [values])]."""
    top, bottom, left = 30, 44, 20
    plot_h = height - top - bottom
    n, k = len(cats), len(series)
    slot = (width - left * 2) / n
    bw = min(34, (slot - 30) / k)
    gap = 8
    vmax = max(max(v) for _, _, v in series) or 1
    o = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-labelledby="{title_id}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>',
         legend([(nm, c) for nm, c, _ in series], left, 14)]
    base = top + plot_h
    o.append(f'<line x1="{left}" x2="{width-left}" y1="{base}" y2="{base}" stroke="{GRID}" stroke-width="1"/>')
    for i, c in enumerate(cats):
        cx = left + slot * i + slot / 2
        gx = cx - (bw * k + gap * (k - 1)) / 2
        for j, (nm, color, vals) in enumerate(series):
            v = vals[i]; hh = plot_h * v / vmax; x = gx + j * (bw + gap)
            if hh > 0.5:
                r = min(4, bw / 2, hh)
                o.append(f'<path d="M{x:.1f},{base} v-{hh-r:.1f} a{r},{r} 0 0 1 {r},-{r} h{bw-2*r:.1f} a{r},{r} 0 0 1 {r},{r} v{hh-r:.1f} z" fill="{color}"/>')
            o.append(_text(x + bw / 2, base - hh - 5, unit_fmt(v), 9.5, "middle", fill=INK if j == k - 1 else MUTED, mono=True))
        o.append(_text(cx, base + 18, c, 11.5, "middle", fill=MUTED))
    o.append("</svg>")
    return "".join(o)
