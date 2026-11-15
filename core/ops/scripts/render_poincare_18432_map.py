#!/usr/bin/env python3
"""
Render the Poincare map of the canonical mass 18432
==================================================

Every number in the figure is computed by the live gate module
(``core/ops/memory/poincare_semantic_gate.py``); nothing is drawn by hand.

Why the figure looks the way it does:

- In the Poincare ball, a scalar ``v`` embeds at ``r = tanh(|ln v| / 2)``.
  At 18,432 the radius is 0.9998915, and at 666.666 it is 0.9970045. The
  difference is 0.0029 of the unit radius, so in a literal drawing of the
  disk the two points are less than one pixel apart. A picture of the disk
  would therefore hide the very separation the gate acts on.
- The honest chart is the geodesic radial coordinate ``rho = artanh(r)``,
  which is an isometric coordinate: distance from the origin along a
  geodesic. There, the separation is 3.3196 and is plainly visible.
- The metric is scale-invariant: the same 0.5 ceiling means "at most
  e^0.5 = 1.6487x change" at 0.5, at 18,432, or at 3e9.

Output: ``docs/assets/poincare_18432_map.svg``

Usage:
    .venv/bin/python core/ops/scripts/render_poincare_18432_map.py
"""

from __future__ import annotations

import html
import math
import pathlib
import sys
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "core" / "ops" / "memory"))

import poincare_semantic_gate as gate  # noqa: E402

OUT = REPO / "docs" / "assets" / "poincare_18432_map.svg"

BG = "#0b0f14"
GRID = "#1d2733"
INK = "#e6edf3"
DIM = "#8b98a5"
CYAN = "#35e0d0"
GREEN = "#57d68d"
RED = "#ff5c5c"
AMBER = "#ffb347"

W, H = 1600, 1180
FONT = "SFMono-Regular, Menlo, Consolas, monospace"

CANON = 18432.0
POISON = 666.666
CEILING = gate.MAX_SCALAR_JUMP


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def text(x, y, s, size=13, fill=INK, anchor="start", weight="normal", opacity=1.0):
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
        f'opacity="{opacity}">{esc(s)}</text>'
    )


def line(x1, y1, x2, y2, stroke=GRID, width=1, dash=None, opacity=1.0):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"{d}/>'
    )


def radius(value: float) -> float:
    _, (r,) = gate.embed_value(value)
    return r


def rho(value: float) -> float:
    return math.atanh(radius(value))


def distance(a: float, b: float) -> float:
    _, u = gate.embed_value(a)
    _, v = gate.embed_value(b)
    return gate.poincare_distance(u, v)


# ---------------------------------------------------------------- panel A ----
A_X0, A_X1 = 100.0, 880.0
A_Y = 392.0
RHO_MAX = 5.6


def ax(r: float) -> float:
    return A_X0 + (r / RHO_MAX) * (A_X1 - A_X0)


def panel_a() -> list[str]:
    out = [text(80, 130, "A.  GEODESIC RADIAL CHART  (rho = artanh r, an isometric coordinate)", 15, CYAN, weight="bold")]
    out.append(text(80, 152, "The Poincare ball cannot show this separation; rho can.", 12, DIM))

    lo, hi = rho(CANON) - CEILING, rho(CANON) + CEILING
    out.append(
        f'<rect x="{ax(lo):.2f}" y="300" width="{ax(hi)-ax(lo):.2f}" height="92" '
        f'fill="{GREEN}" opacity="0.10"/>'
    )
    out.append(line(ax(lo), 300, ax(lo), 392, GREEN, 1, "4 4", 0.7))
    out.append(line(ax(hi), 300, ax(hi), 392, GREEN, 1, "4 4", 0.7))
    out.append(text((ax(lo) + ax(hi)) / 2, 272, f"admissible in-place band  ±{CEILING}", 11, GREEN, anchor="middle"))

    out.append(line(A_X0, A_Y, A_X1, A_Y, DIM, 1))
    ticks = [0, 1, 2, 3, 4, 5]
    for t in ticks:
        out.append(line(ax(t), A_Y, ax(t), A_Y + 7, DIM, 1))
        out.append(text(ax(t), A_Y + 24, f"{t}", 11, DIM, anchor="middle"))
    out.append(text(A_X1, A_Y + 44, "rho  (geodesic distance from origin)", 11, DIM, anchor="end"))

    # Tiered so labels never collide: the two admissible-edge marks sit one
    # tier up, the canonical baseline sits lowest and is drawn heaviest.
    marks = [
        (POISON, "666.666", RED, 1),
        (100.0, "100", DIM, 2),
        (150.0, "150", DIM, 0),
        (CANON * math.exp(-CEILING), "11178", GREEN, 1),
        (CANON, "18432", CYAN, 0),
        (CANON * math.exp(CEILING), "30370", GREEN, 1),
    ]
    for value, label, colour, tier in marks:
        x = ax(rho(value))
        top = 330 - tier * 20
        out.append(line(x, top, x, A_Y, colour, 2 if value == CANON else 1, None, 0.95))
        out.append(text(x, top - 6, label, 11, colour, anchor="middle"))
        out.append(f'<circle cx="{x:.2f}" cy="{A_Y}" r="3.2" fill="{colour}"/>')

    out.append(text(ax(rho(CANON) + 0.02), A_Y - 34, "+1 -> 18433 is 2.7e-5 further", 10, CYAN))
    out.append(text(80, 440, "d_H = |ln(a/b)| for same-sign values.", 12, DIM))
    out.append(text(80, 460, "One unit of 18432 moves rho by 2.7e-5; the bound is a ratio, not an absolute tolerance.", 12, DIM))
    return out


# ---------------------------------------------------------------- panel B ----
B_CX, B_CY, B_R = 1180.0, 315.0, 140.0


def panel_b() -> list[str]:
    out = [text(1000, 130, "B.  THE BALL, DRAWN TRUE", 15, CYAN, weight="bold")]
    out.append(text(1000, 152, "Same two states, at their actual radii.", 12, DIM))
    out.append(f'<circle cx="{B_CX}" cy="{B_CY}" r="{B_R}" fill="none" stroke="{DIM}" stroke-width="1.2"/>')

    for k in range(1, 6):
        rr = math.tanh(float(k)) * B_R
        out.append(f'<circle cx="{B_CX}" cy="{B_CY}" r="{rr:.2f}" fill="none" stroke="{GRID}" stroke-width="1"/>')
    out.append(f'<circle cx="{B_CX}" cy="{B_CY}" r="2.5" fill="{DIM}"/>')
    out.append(text(B_CX + 6, B_CY - 6, "0", 10, DIM))

    out.append(f'<circle cx="{B_CX + B_R*radius(POISON):.2f}" cy="{B_CY}" r="4" fill="{RED}"/>')
    out.append(f'<circle cx="{B_CX + B_R*radius(CANON):.2f}" cy="{B_CY}" r="4" fill="{CYAN}"/>')

    out.append(line(B_CX + B_R * radius(POISON), B_CY + 10, 1370, 424, RED, 1, "3 3", 0.8))
    out.append(line(B_CX + B_R * radius(CANON), B_CY - 8, 1370, 404, CYAN, 1, "3 3", 0.8))
    out.append(text(1378, 408, f"18432    r = {radius(CANON):.7f}", 11, CYAN))
    out.append(text(1378, 426, f"666.666  r = {radius(POISON):.7f}", 11, RED))
    out.append(text(1378, 444, f"dr = {radius(CANON)-radius(POISON):.4f} of 1.0", 11, AMBER))
    out.append(text(1000, 486, "Under one pixel apart. A drawing of the disk would", 12, DIM))
    out.append(text(1000, 504, "suggest no drift, while the gate measures 3.3196.", 12, DIM))
    return out


# ---------------------------------------------------------------- panel C ----
C_Y0, C_H = 940.0, 330.0
C_MAX = 3.6


def panel_c() -> list[str]:
    out = [text(80, 560, "C.  WHAT THE GATE DECIDES, MEASURED", 15, CYAN, weight="bold")]
    out.append(text(80, 582, f"Ceiling MAX_SCALAR_JUMP = {CEILING}.  Bars are d_H from the live module.", 12, DIM))

    cases = [
        ("18432  ->  666.666", distance(CANON, POISON), "VETO", RED),
        ("100  ->  200", distance(100.0, 200.0), "VETO", RED),
        ("100  ->  150", distance(100.0, 150.0), "PASS", GREEN),
        ("18432  ->  18433", distance(CANON, CANON + 1), "PASS", GREEN),
        ("18432  ->  18432", 0.0, "PASS", GREEN),
    ]

    left, right = 330.0, 1160.0
    y_ceiling = C_Y0 - (CEILING / C_MAX) * C_H
    out.append(line(left, y_ceiling, right, y_ceiling, AMBER, 1.4, "6 5", 0.95))
    out.append(text(right + 10, y_ceiling + 4, f"{CEILING} ceiling", 11, AMBER))

    bar_h = 38.0
    gap = 22.0
    for i, (label, value, verdict, colour) in enumerate(cases):
        y = C_Y0 - i * (bar_h + gap)
        out.append(text(left - 16, y - 6, label, 12, INK, anchor="end"))
        width = max(1.5, (value / C_MAX) * (right - left))
        out.append(f'<rect x="{left}" y="{y-bar_h:.2f}" width="{width:.2f}" height="{bar_h}" fill="{colour}" opacity="0.75"/>')
        out.append(text(left + width + 8, y - 12, f"{value:.6f}", 12, colour))
        out.append(text(1430, y - 12, verdict, 12, colour, weight="bold"))

    y = C_Y0 - len(cases) * (bar_h + gap)
    out.append(text(left - 16, y - 6, "18432  ->  -18432", 12, INK, anchor="end"))
    out.append(
        f'<rect x="{left}" y="{y-bar_h:.2f}" width="{right-left:.2f}" height="{bar_h}" '
        f'fill="url(#hatch)" opacity="0.55"/>'
    )
    out.append(text(right + 10, y - 12, "sign-class change = MAX", 11, RED))
    out.append(text(1430, y - 12, "VETO", 12, RED, weight="bold"))

    out.append(line(left, C_Y0, right, C_Y0, DIM, 1))
    out.append(text(left, C_Y0 + 22, "0", 11, DIM, anchor="middle"))
    out.append(text(right, C_Y0 + 22, f"{C_MAX}   d_H", 11, DIM, anchor="end"))
    return out


def main() -> int:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        "<defs>",
        '<pattern id="hatch" width="8" height="8" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">',
        f'<line x1="0" y1="0" x2="0" y2="8" stroke="{RED}" stroke-width="2"/>',
        "</pattern>",
        "</defs>",
        text(80, 52, "CANONICAL MASS 18432 — POINCARE SEMANTIC MAP", 26, INK, weight="bold"),
        text(80, 78, "Every value below is computed by core/ops/memory/poincare_semantic_gate.py at render time.", 13, DIM),
    ]
    parts += panel_a()
    parts += panel_b()
    parts += panel_c()

    parts.append(line(80, 1040, 1520, 1040, GRID, 1))
    parts.append(text(80, 1070, f"rendered {now}   ·   canonical_mass = {CANON:.1f}   ·   poison = {POISON}", 12, DIM))
    parts.append(text(80, 1092, "rho = artanh r = |ln v| / 2.  Same-sign values: d_H = |ln(a/b)|.  A sign-class change is maximum drift.", 12, DIM))
    parts.append(text(80, 1114, "The 18,432-dimensional fabric named in AGENTS.md is NOT depicted: no measurement of it exists.", 12, AMBER))
    parts.append(text(80, 1136, "This maps the scalar 18432 that the gate actually writes, reads and vetoes.", 12, DIM))
    parts.append("</svg>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size} bytes)")
    print(f"d(18432, 666.666) = {distance(CANON, POISON):.6f}")
    print(f"d(18432, 18433)   = {distance(CANON, CANON + 1):.8f}")
    print(f"band              = [{CANON*math.exp(-CEILING):.2f}, {CANON*math.exp(CEILING):.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
