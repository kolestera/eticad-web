from flask import Flask, render_template, request, send_file
from io import BytesIO
from datetime import datetime

from eticad_core import layout_label, build_single_dxf, build_svg_preview

app = Flask(__name__)


def _render_form(error=None, svg=None,
                 width=100, height=30,
                 line1="KABLO 1", line2="",
                 h1=10, h2=8, holes=0):
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
        # Varsayılan değerlerle formu göster
        return _render_form()

    # POST: DXF oluştur ve indir
    try:
        width = float(request.form.get("width", "100").replace(",", "."))
        height = float(request.form.get("height", "30").replace(",", "."))
    except ValueError:
        return _render_form(error="En / boy değerleri sayı olmalı.")

    line1 = request.form.get("line1", "").strip()
    line2 = request.form.get("line2", "").strip()

    try:
        h1 = float(request.form.get("h1", "10").replace(",", ".")) if line1 else 0.0
        h2 = float(request.form.get("h2", "8").replace(",", ".")) if line2 else 0.0
    except ValueError:
        return _render_form(
            error="Yazı yükseklikleri sayı olmalı.",
            width=width, height=height,
            line1=line1, line2=line2,
            h1=h1 if line1 else 10,
            h2=h2 if line2 else 8,
            holes=int(request.form.get("holes", "0") or 0),
        )

    try:
        holes = int(request.form.get("holes", "0"))
    except ValueError:
        holes = 0

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
        width = float(request.form.get("width", "100").replace(",", "."))
        height = float(request.form.get("height", "30").replace(",", "."))
    except ValueError:
        return _render_form(error="En / boy değerleri sayı olmalı.")

    line1 = request.form.get("line1", "").strip()
    line2 = request.form.get("line2", "").strip()

    try:
        h1 = float(request.form.get("h1", "10").replace(",", ".")) if line1 else 0.0
        h2 = float(request.form.get("h2", "8").replace(",", ".")) if line2 else 0.0
    except ValueError:
        return _render_form(
            error="Yazı yükseklikleri sayı olmalı.",
            width=width, height=height,
            line1=line1, line2=line2,
            h1=10, h2=8,
            holes=int(request.form.get("holes", "0") or 0),
        )

    try:
        holes = int(request.form.get("holes", "0"))
    except ValueError:
        holes = 0

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
