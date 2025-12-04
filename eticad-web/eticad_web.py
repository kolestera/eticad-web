from flask import Flask, render_template, request, send_file
from io import BytesIO
from datetime import datetime

from eticad_core import layout_label, build_single_dxf, build_svg_preview

app = Flask(__name__)

# Varsayılanlar (burayı değiştirmen yeterli)
DEFAULT_WIDTH = 200.0
DEFAULT_HEIGHT = 80.0
DEFAULT_LINE1 = "ETICAD"
DEFAULT_LINE2 = "NECATI PEHLIVAN"
DEFAULT_H1 = 40.0
DEFAULT_H2 = 20.0
DEFAULT_HOLES = 0


def _render_form(error=None, svg=None,
                 width=None, height=None,
                 line1=None, line2=None,
                 h1=None, h2=None, holes=None):
    """
    Formu render ederken boş gelenleri DEFAULT_* ile dolduruyoruz.
    """
    if width is None:
        width = DEFAULT_WIDTH
    if height is None:
        height = DEFAULT_HEIGHT
    if line1 is None:
        line1 = DEFAULT_LINE1
    if line2 is None:
        line2 = DEFAULT_LINE2
    if h1 is None:
        h1 = DEFAULT_H1
    if h2 is None:
        h2 = DEFAULT_H2
    if holes is None:
        holes = DEFAULT_HOLES

    return render_template(
        "index.html",
        error=error,
        svg=svg,
        width=width,
        height=height,
        line1=line1,
        line2=line2,
        h1=h1,
        h2=h2,
        holes=holes,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        # Sayfa ilk açılış: varsayılan değerlerle otomatik önizleme
        width = DEFAULT_WIDTH
        height = DEFAULT_HEIGHT
        line1 = DEFAULT_LINE1
        line2 = DEFAULT_LINE2
        h1 = DEFAULT_H1
        h2 = DEFAULT_H2
        holes = DEFAULT_HOLES

        seg1, seg2 = layout_label(width, height, line1, h1, line2, h2)
        svg = build_svg_preview(width, height, seg1, seg2, holes)

        return _render_form(
            error=None,
            svg=svg,
            width=width,
            height=height,
            line1=line1,
            line2=line2,
            h1=h1,
            h2=h2,
            holes=holes,
        )

    # POST: DXF oluştur ve indir
    try:
        width = float(request.form.get("width", str(DEFAULT_WIDTH)).replace(",", "."))
        height = float(request.form.get("height", str(DEFAULT_HEIGHT)).replace(",", "."))
    except ValueError:
        return _render_form(error="En / boy değerleri sayı olmalı.")

    line1 = request.form.get("line1", "").strip()
    line2 = request.form.get("line2", "").strip()

    try:
        h1 = float(request.form.get("h1", str(DEFAULT_H1)).replace(",", ".")) if line1 else 0.0
        h2 = float(request.form.get("h2", str(DEFAULT_H2)).replace(",", ".")) if line2 else 0.0
    except ValueError:
        return _render_form(
            error="Yazı yükseklikleri sayı olmalı.",
            width=width, height=height,
            line1=line1, line2=line2,
            h1=DEFAULT_H1,
            h2=DEFAULT_H2,
            holes=int(request.form.get("holes", str(DEFAULT_HOLES)) or DEFAULT_HOLES),
        )

    try:
        holes = int(request.form.get("holes", str(DEFAULT_HOLES)))
    except ValueError:
        holes = DEFAULT_HOLES

    seg1, seg2 = layout_label(width, height, line1, h1, line2, h2)

    dxf_text = build_single_dxf(width, height, seg1, seg2, holes)

    mem = BytesIO()
    mem.write(dxf_text.encode("utf-8"))
    mem.seek(0)

    filename = f"eticad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dxf"

    return send_file(
        mem,
        as_attachment=True,
        download_name=filename,
        mimetype="application/dxf"
    )


@app.route("/preview", methods=["POST"])
def preview():
    # Önizleme için formdan değerleri oku
    try:
        width = float(request.form.get("width", str(DEFAULT_WIDTH)).replace(",", "."))
        height = float(request.form.get("height", str(DEFAULT_HEIGHT)).replace(",", "."))
    except ValueError:
        return _render_form(error="En / boy değerleri sayı olmalı.")

    line1 = request.form.get("line1", "").strip()
    line2 = request.form.get("line2", "").strip()

    try:
        h1 = float(request.form.get("h1", str(DEFAULT_H1)).replace(",", ".")) if line1 else 0.0
        h2 = float(request.form.get("h2", str(DEFAULT_H2)).replace(",", ".")) if line2 else 0.0
    except ValueError:
        return _render_form(
            error="Yazı yükseklikleri sayı olmalı.",
            width=width, height=height,
            line1=line1, line2=line2,
            h1=DEFAULT_H1, h2=DEFAULT_H2,
            holes=int(request.form.get("holes", str(DEFAULT_HOLES)) or DEFAULT_HOLES),
        )

    try:
        holes = int(request.form.get("holes", str(DEFAULT_HOLES)))
    except ValueError:
        holes = DEFAULT_HOLES

    seg1, seg2 = layout_label(width, height, line1, h1, line2, h2)
    svg = build_svg_preview(width, height, seg1, seg2, holes)

    return _render_form(
        error=None,
        svg=svg,
        width=width,
        height=height,
        line1=line1,
        line2=line2,
        h1=h1,
        h2=h2,
        holes=holes,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

   

