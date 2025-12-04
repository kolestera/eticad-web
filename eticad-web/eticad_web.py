from flask import Flask, render_template, request, send_file
from io import BytesIO
from datetime import datetime

from eticad_core import layout_label, build_single_dxf

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Formdan değerleri al
        try:
            width = float(request.form.get("width", "100").replace(",", "."))
            height = float(request.form.get("height", "30").replace(",", "."))
        except ValueError:
            return render_template("index.html", error="En / boy değerleri sayı olmalı.")

        line1 = request.form.get("line1", "").strip()
        line2 = request.form.get("line2", "").strip()

        try:
            h1 = float(request.form.get("h1", "10").replace(",", ".")) if line1 else 0.0
            h2 = float(request.form.get("h2", "8").replace(",", ".")) if line2 else 0.0
        except ValueError:
            return render_template("index.html", error="Yazı yükseklikleri sayı olmalı.")

        try:
            holes = int(request.form.get("holes", "0"))
        except ValueError:
            holes = 0

        # Segmentleri oluştur
        seg1, seg2 = layout_label(width, height, line1, h1, line2, h2)

        # DXF içeriğini üret
        dxf_text = build_single_dxf(width, height, seg1, seg2, holes)

        # Bellekten dosya gönder
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

    # GET isteği: sadece formu göster
    return render_template("index.html", error=None)


# Render / gunicorn için giriş noktası
if __name__ == "__main__":
    # Lokal test için
    app.run(debug=True, host="0.0.0.0", port=5000)
