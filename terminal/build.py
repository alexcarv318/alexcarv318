#!/usr/bin/env python3
"""Build assets/whoami.svg from terminal/config.json. No dependencies.

    python3 terminal/build.py

A row with "value" is static. A row with "values" rotates: each loop of the
animation shows the next entry. The animation runs as many loops as the
longest rotating list, and shorter lists repeat. Optional "color": "green".
"""
import json
import pathlib
from xml.sax.saxutils import escape

HERE = pathlib.Path(__file__).parent
cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))

CW, FS, LH = 9.0, 15, 25          # glyph width, font size, line height
X0, PY = 28, 64                   # left padding, first baseline
KEY_COLS = 13                     # width of the key column, in characters
CYCLE = float(cfg.get("loop_seconds", 20))
FADE = CYCLE - 3.0                # when the screen clears inside a loop

rows = cfg["rows"]
N = max([len(r["values"]) for r in rows if "values" in r] + [1])
TOTAL = N * CYCLE

longest = max(
    len(v)
    for r in rows
    for v in (r["values"] if "values" in r else [r["value"]])
)
W = int(max(860, X0 * 2 + (KEY_COLS + longest) * CW + 20))

anims, els = [], []


def pct(t, period):
    return round(t / period * 100, 4)


def appear(cls, t, period=CYCLE, off=0):
    anims.append((cls, [(0, "opacity:0"), (off + t, "opacity:1"), (off + FADE, "opacity:0")], period))


def add(cls, svg, t, period=CYCLE, off=0):
    els.append(f'<g class="a {cls}" style="animation-duration:{period}s">{svg}</g>')
    appear(cls, t, period, off)


def prompt_line(y):
    return (f'<text x="{X0}" y="{y}" class="mono"><tspan class="g">{escape(cfg["prompt"])}</tspan>'
            f'<tspan class="w">:</tspan><tspan class="b">~</tspan><tspan class="w">$</tspan></text>')


cmd = cfg["command"]
cx = X0 + (len(cfg["prompt"]) + 4) * CW
t0, step = 0.7, 0.16
els.append(prompt_line(PY))
for i, ch in enumerate(cmd):
    add(f"k{i}", f'<text x="{cx + i * CW}" y="{PY}" class="mono w">{escape(ch)}</text>', t0 + i * step)

# typing cursor: steps right with each character, vanishes on "enter"
cur = [(0, "opacity:1;transform:translateX(0px)")]
cur += [(t0 + (i - 1) * step + 0.001, f"opacity:1;transform:translateX({i * CW}px)") for i in range(1, len(cmd) + 1)]
enter = t0 + len(cmd) * step + 0.35
cur.append((enter, "opacity:0;transform:translateX(0px)"))
anims.append(("cur1", cur, CYCLE))
els.append(f'<rect class="a cur1" style="animation-duration:{CYCLE}s" x="{cx}" y="{PY - 14}" width="{CW}" height="18" fill="#e6edf3"/>')

t, oy = enter + 0.3, PY + LH + 6
add("o0", f'<text x="{X0}" y="{oy}" class="mono h">{escape(cfg["name"])} <tspan class="d">{escape(cfg["handle"])}</tspan></text>', t)
oy += LH - 4
t += 0.35
add("o1", f'<text x="{X0}" y="{oy}" class="mono d">{"─" * 44}</text>', t)
oy += LH

for ri, r in enumerate(rows):
    t += 0.55
    color = "g" if r.get("color") == "green" else "w"

    def row(val):
        return (f'<text y="{oy}" class="mono"><tspan x="{X0}" class="k">{escape(r["key"])}</tspan>'
                f'<tspan x="{X0 + KEY_COLS * CW}" class="{color}">{escape(val)}</tspan></text>')

    if "values" in r:
        for i in range(N):
            add(f"r{ri}v{i}", row(r["values"][i % len(r["values"])]), t, TOTAL, i * CYCLE)
    else:
        add(f"r{ri}", row(r["value"]), t)
    oy += LH

t += 0.6
oy += 6
add("ex", f'<text x="{X0}" y="{oy}" class="mono d">[exit 0]</text>', t)
oy += LH + 8
t += 0.5
add("p2", prompt_line(oy), t)
els.append(f'<g class="a p2" style="animation-duration:{CYCLE}s"><rect class="blink" x="{cx}" y="{oy - 14}" width="{CW}" height="18" fill="#e6edf3"/></g>')
H = int(oy + 34)

css = [
    "svg{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace}",
    f".mono{{font-size:{FS}px;white-space:pre}}",
    ".g{fill:#3fb950}.b{fill:#58a6ff}.w{fill:#e6edf3}.k{fill:#79c0ff}.d{fill:#6e7681}.h{fill:#f0f6fc;font-weight:700}",
    ".a{opacity:0;animation-iteration-count:infinite;animation-timing-function:step-end}",
    ".blink{animation:blink 1s step-end infinite}@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}",
]
for cls, pts, period in anims:
    body = "".join(f"{pct(tt, period)}%{{{p}}}" for tt, p in pts)
    body += (f"{pct(FADE, period)}%{{opacity:0}}" if cls == "cur1" else "") + "100%{opacity:0}"
    css.append(f"@keyframes kf-{cls}{{{body}}}.{cls}{{animation-name:kf-{cls}}}")
hide = "".join(f".r{ri}v{i}{{display:none}}" for ri, r in enumerate(rows) if "values" in r for i in range(1, N))
css.append(f"@media (prefers-reduced-motion:reduce){{.a{{animation:none!important;opacity:1!important}}.cur1,.blink{{display:none}}{hide}}}")

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Terminal session: {escape(cmd)} prints {escape(cfg["name"])}">
<style>{"".join(css)}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
<path d="M0.5 36 V10.5 a10 10 0 0 1 10 -10 H{W - 10.5} a10 10 0 0 1 10 10 V36 Z" fill="#161b22"/>
<line x1="0" y1="36.5" x2="{W}" y2="36.5" stroke="#30363d"/>
<circle cx="22" cy="18" r="6" fill="#ff5f56"/><circle cx="42" cy="18" r="6" fill="#ffbd2e"/><circle cx="62" cy="18" r="6" fill="#27c93f"/>
<text x="{W / 2}" y="23" text-anchor="middle" font-size="12.5" fill="#8b949e">{escape(cfg["prompt"])}: ~</text>
{"".join(els)}
</svg>
'''
out = HERE.parent / "assets" / "whoami.svg"
out.parent.mkdir(exist_ok=True)
out.write_text(svg, encoding="utf-8")
print(f"wrote {out}  {W}x{H}  loops={N}  total={TOTAL:.0f}s")
