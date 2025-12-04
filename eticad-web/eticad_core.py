import os
import sys
import importlib.util

LETTER_SPACING_FACTOR = 0.1


def app_dir():
    """Programın çalıştığı klasör (exe veya .py)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def load_glyphs():
    """
    glyph_kutuphane.py içinden GLYPHS sözlüğünü yükler.
    """
    external = os.path.join(app_dir(), "glyph_kutuphane.py")
    if os.path.exists(external):
        try:
            spec = importlib.util.spec_from_file_location("glyph_ext", external)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.GLYPHS
        except Exception as e:
            raise RuntimeError(f"glyph_kutuphane.py yüklenemedi: {e}")

    raise RuntimeError("glyph_kutuphane.py bulunamadı.")


GLYPHS = load_glyphs()


# =========================
# ÖZEL KARAKTERLER: . : -
# =========================

def build_special_glyph(ch, height_mm, cursor_x):
    segs = []
    spacing = height_mm * LETTER_SPACING_FACTOR

    if ch == '.':
        size = height_mm * 0.18
        y0 = height_mm * 0.08
        x0 = cursor_x
        segs += [
            ((x0,         y0),          (x0 + size, y0)),
            ((x0 + size,  y0),          (x0 + size, y0 + size)),
            ((x0 + size,  y0 + size),   (x0,        y0 + size)),
            ((x0,         y0 + size),   (x0,        y0)),
        ]
        advance = size + spacing
        return segs, advance

    if ch == ':':
        size = height_mm * 0.16
        gap = height_mm * 0.10
        y0 = height_mm * 0.08
        x0 = cursor_x

        # alt nokta
        segs += [
            ((x0,         y0),          (x0 + size, y0)),
            ((x0 + size,  y0),          (x0 + size, y0 + size)),
            ((x0 + size,  y0 + size),   (x0,        y0 + size)),
            ((x0,         y0 + size),   (x0,        y0)),
        ]
        # üst nokta
        y1 = y0 + size + gap
        segs += [
            ((x0,         y1),          (x0 + size, y1)),
            ((x0 + size,  y1),          (x0 + size, y1 + size)),
            ((x0 + size,  y1 + size),   (x0,        y1 + size)),
            ((x0,         y1 + size),   (x0,        y1)),
        ]
        advance = size + spacing
        return segs, advance

    if ch == '-':
        width = height_mm * 0.6
        thickness = height_mm * 0.18
        y_mid = height_mm * 0.5
        y0 = y_mid - thickness / 2.0
        y1 = y_mid + thickness / 2.0
        x0 = cursor_x
        x1 = cursor_x + width

        segs += [
            ((x0, y0), (x1, y0)),
            ((x1, y0), (x1, y1)),
            ((x1, y1), (x0, y1)),
            ((x0, y1), (x0, y0)),
        ]
        advance = width + spacing
        return segs, advance

    return [], 0.0


# =========================
# METNİ SEGMENTLERE ÇEVİRME
# =========================

def build_text_segments(text, height_mm):
    segments = []
    cursor_x = 0.0

    for ch in text:
        if ch == " ":
            cursor_x += height_mm * 0.5
            continue

        if ch in [".", ":", "-"]:
            sp_segs, adv = build_special_glyph(ch, height_mm, cursor_x)
            segments.extend(sp_segs)
            cursor_x += adv
            continue

        if ch not in GLYPHS:
            # bilinmeyen karakteri atla
            continue

        g = GLYPHS[ch]
        gh = g["height"] or 1.0
        scale = height_mm / gh
        spacing = height_mm * LETTER_SPACING_FACTOR

        for (x1, y1), (x2, y2) in g["segments"]:
            sx1 = x1 * scale + cursor_x
            sy1 = y1 * scale
            sx2 = x2 * scale + cursor_x
            sy2 = y2 * scale
            segments.append(((sx1, sy1), (sx2, sy2)))

        cursor_x += g["width"] * scale + spacing

    return segments


def center_horizontal(segments, cx):
    if not segments:
        return []
    xs = []
    for (x1, y1), (x2, y2) in segments:
        xs.extend([x1, x2])
    minx, maxx = min(xs), max(xs)
    tx = cx - (minx + maxx) / 2.0
    shifted = []
    for (x1, y1), (x2, y2) in segments:
        shifted.append(((x1 + tx, y1), (x2 + tx, y2)))
    return shifted


# =========================
# ETİKET YERLEŞİMİ
# =========================

def layout_label(width, height, line1, h1, line2, h2):
    cx = width / 2.0

    seg1 = build_text_segments(line1, h1) if (line1.strip() and h1 > 0) else []
    seg2 = build_text_segments(line2, h2) if (line2.strip() and h2 > 0) else []

    seg1_final = []
    seg2_final = []

    if seg1 and not seg2:
        baseline = height / 2.0 - h1 / 2.0
        seg1_shift = [((x1, y1 + baseline), (x2, y2 + baseline))
                      for (x1, y1), (x2, y2) in seg1]
        seg1_final = center_horizontal(seg1_shift, cx)

    elif seg2 and not seg1:
        baseline = height / 2.0 - h2 / 2.0
        seg2_shift = [((x1, y1 + baseline), (x2, y2 + baseline))
                      for (x1, y1), (x2, y2) in seg2]
        seg2_final = center_horizontal(seg2_shift, cx)

    elif seg1 and seg2:
        gap = 0.2 * min(h1, h2)
        total_text_height = h1 + h2 + gap
        margin = (height - total_text_height) / 2.0
        if margin < 0:
            margin = 0
            gap = max(0, height - (h1 + h2))

        baseline2 = margin
        baseline1 = margin + h2 + gap

        seg1_shift = [((x1, y1 + baseline1), (x2, y2 + baseline1))
                      for (x1, y1), (x2, y2) in seg1]
        seg2_shift = [((x1, y1 + baseline2), (x2, y2 + baseline2))
                      for (x1, y1), (x2, y2) in seg2]

        seg1_final = center_horizontal(seg1_shift, cx)
        seg2_final = center_horizontal(seg2_shift, cx)

    return seg1_final, seg2_final


# =========================
# DXF YAZICI
# =========================

def _dxf_add(lines, code, value):
    lines.append(str(code))
    lines.append(str(value))


def build_single_dxf(width_mm, height_mm, seg1, seg2, hole_mode):
    """
    DXF içeriğini string olarak döner.
    """
    lines = []

    def add_line(x1, y1, x2, y2):
        _dxf_add(lines, 0, "LINE")
        _dxf_add(lines, 8, "0")
        _dxf_add(lines, 10, f"{x1:.4f}")
        _dxf_add(lines, 20, f"{y1:.4f}")
        _dxf_add(lines, 30, "0.0")
        _dxf_add(lines, 11, f"{x2:.4f}")
        _dxf_add(lines, 21, f"{y2:.4f}")
        _dxf_add(lines, 31, "0.0")

    def add_circle(cx, cy, r=3.25):
        _dxf_add(lines, 0, "CIRCLE")
        _dxf_add(lines, 8, "0")
        _dxf_add(lines, 10, f"{cx:.4f}")
        _dxf_add(lines, 20, f"{cy:.4f}")
        _dxf_add(lines, 30, "0.0")
        _dxf_add(lines, 40, f"{r:.4f}")

    def add_segments(segs):
        for (x1, y1), (x2, y2) in segs:
            add_line(x1, y1, x2, y2)

    def add_holes(mode):
        if mode == 2:
            cx1, cy1 = 8.0, height_mm / 2.0
            cx2, cy2 = width_mm - 8.0, height_mm / 2.0
            add_circle(cx1, cy1)
            add_circle(cx2, cy2)
        elif mode == 4:
            cx1, cy1 = 8.0, 8.0
            cx2, cy2 = width_mm - 8.0, 8.0
            cx3, cy3 = 8.0, height_mm - 8.0
            cx4, cy4 = width_mm - 8.0, height_mm - 8.0
            add_circle(cx1, cy1)
            add_circle(cx2, cy2)
            add_circle(cx3, cy3)
            add_circle(cx4, cy4)

    # HEADER
    _dxf_add(lines, 0, "SECTION")
    _dxf_add(lines, 2, "HEADER")
    _dxf_add(lines, 9, "$ACADVER")
    _dxf_add(lines, 1, "AC1009")
    _dxf_add(lines, 0, "ENDSEC")

    # TABLES
    _dxf_add(lines, 0, "SECTION")
    _dxf_add(lines, 2, "TABLES")
    _dxf_add(lines, 0, "ENDSEC")

    # ENTITIES
    _dxf_add(lines, 0, "SECTION")
    _dxf_add(lines, 2, "ENTITIES")

    # Kutu
    add_line(0, 0, width_mm, 0)
    add_line(width_mm, 0, width_mm, height_mm)
    add_line(width_mm, height_mm, 0, height_mm)
    add_line(0, height_mm, 0, 0)

    # Yazılar
    add_segments(seg1)
    add_segments(seg2)

    # Delikler
    add_holes(hole_mode)

    # ENDSEC / EOF
    _dxf_add(lines, 0, "ENDSEC")
    _dxf_add(lines, 0, "EOF")

    return "\n".join(lines)


def save_single_dxf(width_mm, height_mm, seg1, seg2, hole_mode, filename):
    content = build_single_dxf(width_mm, height_mm, seg1, seg2, hole_mode)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


# =========================
# SVG ÖNİZLEME
# =========================

def build_svg_preview(width_mm, height_mm, seg1, seg2, hole_mode):
    """
    Verilen segmentler ve delik moduna göre etiketin SVG önizlemesini üretir.
    """
    def t_y(y):
        # SVG'de y aşağı büyüdüğü için aynalıyoruz
        return height_mm - y

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width_mm:.2f} {height_mm:.2f}" '
        f'width="{width_mm*3:.0f}" height="{height_mm*3:.0f}" '
        f'style="background:#f9fafb;border:1px solid #cbd5e1;">'
        '<g stroke="black" stroke-width="0.4" fill="none">'
    ]

    # Dış kutu
    parts.append(
        f'<rect x="0" y="0" width="{width_mm:.2f}" height="{height_mm:.2f}" '
        'stroke="black" stroke-width="0.5" fill="none" />'
    )

    # Yazı segmentleri
    for (x1, y1), (x2, y2) in (seg1 + seg2):
        parts.append(
            f'<line x1="{x1:.2f}" y1="{t_y(y1):.2f}" '
            f'x2="{x2:.2f}" y2="{t_y(y2):.2f}" />'
        )

    # Delikler
    def add_circle(cx, cy, r=3.25):
        parts.append(
            f'<circle cx="{cx:.2f}" cy="{t_y(cy):.2f}" r="{r:.2f}" '
            'stroke="black" stroke-width="0.4" fill="none" />'
        )

    if hole_mode == 2:
        cx1, cy1 = 8.0, height_mm / 2.0
        cx2, cy2 = width_mm - 8.0, height_mm / 2.0
        add_circle(cx1, cy1)
        add_circle(cx2, cy2)
    elif hole_mode == 4:
        cx1, cy1 = 8.0, 8.0
        cx2, cy2 = width_mm - 8.0, 8.0
        cx3, cy3 = 8.0, height_mm - 8.0
        cx4, cy4 = width_mm - 8.0, height_mm - 8.0
        add_circle(cx1, cy1)
        add_circle(cx2, cy2)
        add_circle(cx3, cy3)
        add_circle(cx4, cy4)

    parts.append("</g></svg>")
    return "".join(parts)
