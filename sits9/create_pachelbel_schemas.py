#!/usr/bin/env python3
"""
Generate three schema figures for the Pachelbel Canon demonstration:
  Figure 2 — Harmonic progression (score-like schematic)
  Figure 3 — Textile schema (back-stitch pattern)
  Figure 4 — Cooking schema (heat/method timeline)

Output: SVG + PNG in sits9/output/
"""

from pathlib import Path

import svgwrite
import cairosvg

OUT_DIR = Path(__file__).parent / "output"

# Pachelbel progression data
CHORDS = [
    {"name": "D",   "degree": "I",   "tension": 0.2, "dir": "anchor", "n": 0},
    {"name": "A",   "degree": "V",   "tension": 0.8, "dir": "fwd",    "n": 5},
    {"name": "Bm",  "degree": "vi",  "tension": 0.5, "dir": "fwd",    "n": 2},
    {"name": "F♯m", "degree": "iii", "tension": 0.4, "dir": "ret",    "n": 5},
    {"name": "G",   "degree": "IV",  "tension": 0.3, "dir": "fwd",    "n": 1},
    {"name": "D",   "degree": "I",   "tension": 0.2, "dir": "ret",    "n": 5},
    {"name": "G",   "degree": "IV",  "tension": 0.3, "dir": "fwd",    "n": 3},
    {"name": "A",   "degree": "V",   "tension": 0.8, "dir": "fwd",    "n": 2},
]

# Pitch positions (semitones from D4, for visual layout)
DEGREE_Y = {"I": 0, "ii": 1, "iii": 2, "IV": 3, "V": 4, "vi": 5, "vii": 6}


def build_score_schema() -> str:
    """Figure 2: Harmonic progression diagram."""
    w, h = 720, 320
    dwg = svgwrite.Drawing(size=(w, h))

    # Background
    dwg.add(dwg.rect((0, 0), (w, h), fill="white"))

    # Staff area
    staff_x0, staff_x1 = 80, 680
    staff_y0 = 60
    staff_h = 180
    n_chords = len(CHORDS)
    col_w = (staff_x1 - staff_x0) / n_chords

    # Draw tension graph background
    dwg.add(dwg.rect(
        (staff_x0, staff_y0), (staff_x1 - staff_x0, staff_h),
        fill="#F8F8F8", stroke="#CCCCCC", stroke_width=1
    ))

    # Y-axis labels (tension)
    for tv, label in [(0.0, "0.0"), (0.5, "0.5"), (1.0, "1.0")]:
        y = staff_y0 + staff_h - tv * staff_h
        dwg.add(dwg.line(
            (staff_x0, y), (staff_x1, y),
            stroke="#E0E0E0", stroke_width=0.5
        ))
        dwg.add(dwg.text(
            label, insert=(staff_x0 - 8, y + 4),
            text_anchor="end", font_size="10px", fill="#666666",
            font_family="Helvetica"
        ))

    # Y-axis title
    dwg.add(dwg.text(
        "TENSION", insert=(15, staff_y0 + staff_h / 2),
        text_anchor="middle", font_size="10px", fill="#666666",
        font_family="Helvetica",
        transform=f"rotate(-90, 15, {staff_y0 + staff_h / 2})"
    ))

    # Plot chords as bars + connecting line
    points = []
    colors_dir = {"anchor": "#2196F3", "fwd": "#E53935", "ret": "#43A047"}

    for i, ch in enumerate(CHORDS):
        cx = staff_x0 + col_w * i + col_w / 2
        bar_h = ch["tension"] * staff_h
        bar_y = staff_y0 + staff_h - bar_h
        color = colors_dir[ch["dir"]]

        # Bar
        dwg.add(dwg.rect(
            (cx - 18, bar_y), (36, bar_h),
            fill=color, fill_opacity=0.7, rx=3, ry=3
        ))

        # Chord name
        dwg.add(dwg.text(
            ch["name"], insert=(cx, staff_y0 + staff_h + 20),
            text_anchor="middle", font_size="13px", font_weight="bold",
            fill="#333333", font_family="Helvetica"
        ))

        # Degree
        dwg.add(dwg.text(
            ch["degree"], insert=(cx, staff_y0 + staff_h + 35),
            text_anchor="middle", font_size="11px", fill="#666666",
            font_family="Helvetica"
        ))

        # Direction arrow label
        if ch["dir"] == "fwd":
            arrow = f"FWD({ch['n']})"
        elif ch["dir"] == "ret":
            arrow = f"RET({ch['n']})"
        else:
            arrow = "ANCHOR"
        dwg.add(dwg.text(
            arrow, insert=(cx, bar_y - 6),
            text_anchor="middle", font_size="8px", fill=color,
            font_family="Courier New", font_weight="bold"
        ))

        points.append((cx, bar_y + 2))

    # Connecting line through bar tops
    for i in range(len(points) - 1):
        dwg.add(dwg.line(
            points[i], points[i + 1],
            stroke="#333333", stroke_width=1.5,
            stroke_dasharray="4,3"
        ))

    # Legend
    legend_x, legend_y = staff_x1 - 180, staff_y0 - 2
    for label, color in [("ANCHOR", "#2196F3"), ("FWD", "#E53935"), ("RET", "#43A047")]:
        dwg.add(dwg.rect((legend_x, legend_y - 8), (12, 12), fill=color, fill_opacity=0.7, rx=2))
        dwg.add(dwg.text(
            label, insert=(legend_x + 16, legend_y + 2),
            font_size="9px", fill="#333333", font_family="Helvetica"
        ))
        legend_x += 60

    # Title
    dwg.add(dwg.text(
        "Pachelbel Canon — Harmonic Tension Profile",
        insert=(w / 2, 25), text_anchor="middle",
        font_size="14px", font_weight="bold", fill="#222222",
        font_family="Helvetica"
    ))
    dwg.add(dwg.text(
        "(SITS9 instruction mapping: direction + tension per chord)",
        insert=(w / 2, 42), text_anchor="middle",
        font_size="10px", fill="#888888", font_family="Helvetica"
    ))

    return dwg.tostring()


def build_textile_schema() -> str:
    """Figure 3: Back-stitch schematic showing needle path."""
    w, h = 720, 300
    dwg = svgwrite.Drawing(size=(w, h))
    dwg.add(dwg.rect((0, 0), (w, h), fill="white"))

    # Fabric representation: two horizontal bands (surface / back)
    fabric_x0, fabric_x1 = 60, 680
    surface_y = 100
    back_y = 200
    mid_y = (surface_y + back_y) / 2

    # Fabric bands
    dwg.add(dwg.rect(
        (fabric_x0, surface_y - 20), (fabric_x1 - fabric_x0, 40),
        fill="#FFF3E0", stroke="#FFB74D", stroke_width=1, rx=3
    ))
    dwg.add(dwg.rect(
        (fabric_x0, back_y - 20), (fabric_x1 - fabric_x0, 40),
        fill="#E3F2FD", stroke="#64B5F6", stroke_width=1, rx=3
    ))

    # Labels
    dwg.add(dwg.text(
        "Surface (表)", insert=(fabric_x0 - 5, surface_y + 5),
        text_anchor="end", font_size="11px", fill="#E65100",
        font_family="Helvetica"
    ))
    dwg.add(dwg.text(
        "Back (裏)", insert=(fabric_x0 - 5, back_y + 5),
        text_anchor="end", font_size="11px", fill="#1565C0",
        font_family="Helvetica"
    ))

    # Stitch path: follows the Pachelbel progression
    # Each chord = one stitch segment, alternating surface/back
    col_w = (fabric_x1 - fabric_x0) / len(CHORDS)
    stitch_points = []
    on_surface = True

    for i, ch in enumerate(CHORDS):
        cx = fabric_x0 + col_w * i + col_w / 2
        y = surface_y if on_surface else back_y

        if ch["dir"] == "anchor":
            # Anchor = knot at current position
            stitch_points.append((cx, y, "anchor", ch))
        else:
            stitch_points.append((cx, y, ch["dir"], ch))
            on_surface = not on_surface

    # Draw stitch lines
    for i in range(len(stitch_points) - 1):
        x1, y1, _, _ = stitch_points[i]
        x2, y2, _, _ = stitch_points[i + 1]

        is_surface = (y1 == surface_y or y2 == surface_y) and abs(y1 - y2) < 10
        if y1 == y2 == surface_y:
            color, dash = "#E53935", "none"
            sw = 2.5
        elif y1 == y2 == back_y:
            color, dash = "#90A4AE", "5,3"
            sw = 2.0
        else:
            # CROSS: line goes between surface and back
            color = "#FF9800"
            dash = "none"
            sw = 1.5

        line = dwg.line((x1, y1), (x2, y2), stroke=color, stroke_width=sw)
        if dash != "none":
            line["stroke-dasharray"] = dash
        dwg.add(line)

    # Draw nodes and labels
    for i, (x, y, dir_type, ch) in enumerate(stitch_points):
        if dir_type == "anchor":
            dwg.add(dwg.circle((x, y), 6, fill="#333333"))
        elif dir_type == "fwd":
            dwg.add(dwg.circle((x, y), 5, fill="#E53935", stroke="white", stroke_width=1))
        elif dir_type == "ret":
            dwg.add(dwg.circle((x, y), 5, fill="#43A047", stroke="white", stroke_width=1))

        # Chord label above/below
        label_y = y - 28 if y == surface_y else y + 35
        dwg.add(dwg.text(
            f"{ch['name']}", insert=(x, label_y),
            text_anchor="middle", font_size="11px", font_weight="bold",
            fill="#333333", font_family="Helvetica"
        ))
        dwg.add(dwg.text(
            f"({ch['degree']})", insert=(x, label_y + 13),
            text_anchor="middle", font_size="9px", fill="#666666",
            font_family="Helvetica"
        ))

        # Direction annotation
        if dir_type != "anchor" and ch["n"] > 0:
            arrow_label = f"{'FWD' if dir_type == 'fwd' else 'RET'}({ch['n']})"
            ann_y = mid_y + 5
            color = "#E53935" if dir_type == "fwd" else "#43A047"
            dwg.add(dwg.text(
                arrow_label, insert=(x, ann_y),
                text_anchor="middle", font_size="7px", fill=color,
                font_family="Courier New", font_weight="bold"
            ))

    # CROSS labels on transition lines
    for i in range(len(stitch_points) - 1):
        x1, y1, _, _ = stitch_points[i]
        x2, y2, _, _ = stitch_points[i + 1]
        if y1 != y2:
            mx = (x1 + x2) / 2 + 12
            my = (y1 + y2) / 2
            dwg.add(dwg.text(
                "CROSS", insert=(mx, my),
                text_anchor="middle", font_size="7px", fill="#FF9800",
                font_family="Courier New", font_weight="bold",
                transform=f"rotate(-45, {mx}, {my})"
            ))

    # Legend
    leg_y = 265
    items = [
        ("Surface stitch (FWD)", "#E53935", "none", 2.5),
        ("Back stitch (RET)", "#90A4AE", "5,3", 2.0),
        ("CROSS (needle passes through fabric)", "#FF9800", "none", 1.5),
    ]
    leg_x = 100
    for label, color, dash, sw in items:
        line = dwg.line((leg_x, leg_y), (leg_x + 30, leg_y), stroke=color, stroke_width=sw)
        if dash != "none":
            line["stroke-dasharray"] = dash
        dwg.add(line)
        dwg.add(dwg.text(
            label, insert=(leg_x + 36, leg_y + 4),
            font_size="9px", fill="#333333", font_family="Helvetica"
        ))
        leg_x += 210

    # Anchor legend
    dwg.add(dwg.circle((leg_x + 5, leg_y), 5, fill="#333333"))
    dwg.add(dwg.text(
        "ANCHOR (knot)", insert=(leg_x + 16, leg_y + 4),
        font_size="9px", fill="#333333", font_family="Helvetica"
    ))

    # Title
    dwg.add(dwg.text(
        "Pachelbel Canon — Textile Schema (Back-Stitch Pattern)",
        insert=(w / 2, 25), text_anchor="middle",
        font_size="14px", font_weight="bold", fill="#222222",
        font_family="Helvetica"
    ))
    dwg.add(dwg.text(
        "(Needle path alternating between surface and back of fabric)",
        insert=(w / 2, 42), text_anchor="middle",
        font_size="10px", fill="#888888", font_family="Helvetica"
    ))

    return dwg.tostring()


def build_cooking_schema() -> str:
    """Figure 4: Cooking process schematic."""
    w, h = 720, 340
    dwg = svgwrite.Drawing(size=(w, h))
    dwg.add(dwg.rect((0, 0), (w, h), fill="white"))

    # Axes
    chart_x0, chart_x1 = 90, 680
    chart_y0, chart_y1 = 70, 240
    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0

    # Background
    dwg.add(dwg.rect(
        (chart_x0, chart_y0), (chart_w, chart_h),
        fill="#FAFAFA", stroke="#CCCCCC", stroke_width=1
    ))

    # Y-axis: Heat level (TENSION)
    for tv, label in [(0.0, "Off"), (0.25, "Low"), (0.5, "Med"), (0.75, "High"), (1.0, "Max")]:
        y = chart_y1 - tv * chart_h
        dwg.add(dwg.line(
            (chart_x0, y), (chart_x1, y),
            stroke="#E8E8E8", stroke_width=0.5
        ))
        dwg.add(dwg.text(
            label, insert=(chart_x0 - 8, y + 4),
            text_anchor="end", font_size="9px", fill="#666666",
            font_family="Helvetica"
        ))

    dwg.add(dwg.text(
        "Heat Level (TENSION)", insert=(20, chart_y0 + chart_h / 2),
        text_anchor="middle", font_size="10px", fill="#666666",
        font_family="Helvetica",
        transform=f"rotate(-90, 20, {chart_y0 + chart_h / 2})"
    ))

    # Cooking method zones (alternating background strips)
    methods = ["—", "Grill", "Grill", "Simmer", "Simmer", "Grill", "Steam", "Grill"]
    method_colors = {
        "Grill": "#FFEBEE",
        "Simmer": "#E3F2FD",
        "Steam": "#E8F5E9",
        "—": "#F5F5F5",
    }

    col_w = chart_w / len(CHORDS)
    for i, method in enumerate(methods):
        x = chart_x0 + col_w * i
        color = method_colors.get(method, "#F5F5F5")
        dwg.add(dwg.rect(
            (x, chart_y0), (col_w, chart_h),
            fill=color, fill_opacity=0.4
        ))

    # Plot heat curve
    points = []
    for i, ch in enumerate(CHORDS):
        cx = chart_x0 + col_w * i + col_w / 2
        cy = chart_y1 - ch["tension"] * chart_h
        points.append((cx, cy))

    # Fill area under curve
    fill_points = [(points[0][0], chart_y1)]
    fill_points.extend(points)
    fill_points.append((points[-1][0], chart_y1))
    fill_path = "M " + " L ".join(f"{x},{y}" for x, y in fill_points) + " Z"
    dwg.add(dwg.path(d=fill_path, fill="#FF5722", fill_opacity=0.12))

    # Draw curve
    for i in range(len(points) - 1):
        dwg.add(dwg.line(
            points[i], points[i + 1],
            stroke="#FF5722", stroke_width=2.5
        ))

    # Nodes + labels
    colors_dir = {"anchor": "#2196F3", "fwd": "#E53935", "ret": "#43A047"}
    for i, ch in enumerate(CHORDS):
        cx, cy = points[i]
        color = colors_dir[ch["dir"]]

        # Node
        dwg.add(dwg.circle((cx, cy), 5, fill=color, stroke="white", stroke_width=1.5))

        # SITS9 instruction
        if ch["dir"] == "anchor":
            label = "ANCHOR"
        elif ch["dir"] == "fwd":
            label = f"FWD({ch['n']})"
        else:
            label = f"RET({ch['n']})"

        dwg.add(dwg.text(
            label, insert=(cx, cy - 10),
            text_anchor="middle", font_size="7px", fill=color,
            font_family="Courier New", font_weight="bold"
        ))

        # Chord + cooking method below x-axis
        dwg.add(dwg.text(
            f"{ch['name']} ({ch['degree']})", insert=(cx, chart_y1 + 16),
            text_anchor="middle", font_size="10px", font_weight="bold",
            fill="#333333", font_family="Helvetica"
        ))

        # Method label
        method = methods[i]
        if method != "—":
            method_color = {"Grill": "#C62828", "Simmer": "#1565C0", "Steam": "#2E7D32"}
            dwg.add(dwg.text(
                method, insert=(cx, chart_y1 + 30),
                text_anchor="middle", font_size="9px",
                fill=method_color.get(method, "#666"),
                font_family="Helvetica"
            ))

    # CROSS markers (method switches)
    prev_method = methods[0]
    for i in range(1, len(methods)):
        if methods[i] != prev_method and methods[i] != "—":
            x = chart_x0 + col_w * i
            dwg.add(dwg.line(
                (x, chart_y0), (x, chart_y1),
                stroke="#FF9800", stroke_width=1.5, stroke_dasharray="4,3"
            ))
            dwg.add(dwg.text(
                "CROSS", insert=(x + 3, chart_y0 + 12),
                font_size="7px", fill="#FF9800",
                font_family="Courier New", font_weight="bold"
            ))
        if methods[i] != "—":
            prev_method = methods[i]

    # Legend
    leg_y = 290
    leg_items = [
        ("Grill zone", "#FFEBEE", "#C62828"),
        ("Simmer zone", "#E3F2FD", "#1565C0"),
        ("Steam zone", "#E8F5E9", "#2E7D32"),
    ]
    leg_x = 120
    for label, bg, fg in leg_items:
        dwg.add(dwg.rect((leg_x, leg_y - 8), (14, 14), fill=bg, stroke=fg, stroke_width=1, rx=2))
        dwg.add(dwg.text(
            label, insert=(leg_x + 20, leg_y + 4),
            font_size="9px", fill="#333333", font_family="Helvetica"
        ))
        leg_x += 120

    # Heat curve legend
    dwg.add(dwg.line((leg_x, leg_y), (leg_x + 25, leg_y), stroke="#FF5722", stroke_width=2.5))
    dwg.add(dwg.text(
        "Heat level (TENSION)", insert=(leg_x + 30, leg_y + 4),
        font_size="9px", fill="#333333", font_family="Helvetica"
    ))

    # CROSS legend
    leg_x += 170
    dwg.add(dwg.line(
        (leg_x, leg_y - 6), (leg_x, leg_y + 6),
        stroke="#FF9800", stroke_width=1.5, stroke_dasharray="4,3"
    ))
    dwg.add(dwg.text(
        "CROSS (method switch)", insert=(leg_x + 8, leg_y + 4),
        font_size="9px", fill="#333333", font_family="Helvetica"
    ))

    # Cooking interpretation annotations
    ann_y = 318
    dwg.add(dwg.text(
        "FWD(n) = heat for n minutes  |  RET(n) = rest/cool for n minutes  |  "
        "CROSS = switch cooking method  |  ANCHOR = taste & season",
        insert=(w / 2, ann_y), text_anchor="middle",
        font_size="8.5px", fill="#888888", font_family="Helvetica"
    ))

    # Title
    dwg.add(dwg.text(
        "Pachelbel Canon — Cooking Schema (Heat & Method Timeline)",
        insert=(w / 2, 25), text_anchor="middle",
        font_size="14px", font_weight="bold", fill="#222222",
        font_family="Helvetica"
    ))
    dwg.add(dwg.text(
        "(Same SITS9 Deck rendered as a cooking process)",
        insert=(w / 2, 42), text_anchor="middle",
        font_size="10px", fill="#888888", font_family="Helvetica"
    ))

    return dwg.tostring()


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    schemas = [
        ("pachelbel_score_schema", build_score_schema),
        ("pachelbel_textile_schema", build_textile_schema),
        ("pachelbel_cooking_schema", build_cooking_schema),
    ]

    for name, builder in schemas:
        svg_str = builder()
        svg_path = OUT_DIR / f"{name}.svg"
        png_path = OUT_DIR / f"{name}.png"

        svg_path.write_text(svg_str, encoding="utf-8")
        print(f"SVG → {svg_path}")

        cairosvg.svg2png(bytestring=svg_str.encode(), write_to=str(png_path),
                         output_width=1440)
        print(f"PNG → {png_path}")


if __name__ == "__main__":
    main()
