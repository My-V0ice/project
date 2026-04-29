from __future__ import annotations

from pathlib import Path
import json
import os
from typing import Any

from app.core.config import BASE_DIR


DOCUMENTS_DIR = BASE_DIR / "documents"
BRAND_RED = "#9b2242"
BRAND_TEXT = "#1f2430"
_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c6360f8cf00000301010118dd8db00000000049454e44ae426082"
)


def ensure_documents_dir() -> Path:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    return DOCUMENTS_DIR


def _pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont

        return Image, ImageDraw, ImageFont
    except ModuleNotFoundError:
        return None, None, None


def _font(size: int, bold: bool = False):
    _, _, ImageFont = _pillow()
    if ImageFont is None:
        return None
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _write_minimal_png(path: Path) -> None:
    path.write_bytes(_MINIMAL_PNG)


def _draw_qr_fallback(draw, x: int, y: int, size: int, data: str) -> None:
    cell = size // 29
    draw.rectangle((x, y, x + size, y + size), fill="white", outline=BRAND_RED, width=2)
    seed = sum(ord(char) for char in data)
    for row in range(29):
        for col in range(29):
            finder = (
                (row < 7 and col < 7)
                or (row < 7 and col > 21)
                or (row > 21 and col < 7)
            )
            if finder or ((row * 17 + col * 31 + seed) % 7 in {0, 2, 5}):
                draw.rectangle(
                    (
                        x + col * cell,
                        y + row * cell,
                        x + (col + 1) * cell - 1,
                        y + (row + 1) * cell - 1,
                    ),
                    fill=BRAND_RED if finder else BRAND_TEXT,
                )


def create_qr_image(data: str, path: Path) -> None:
    Image, ImageDraw, _ = _pillow()
    try:
        import qrcode

        if Image is None:
            raise ModuleNotFoundError("Pillow is required by qrcode image rendering")
        qr = qrcode.QRCode(version=None, box_size=8, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        image = qr.make_image(fill_color=BRAND_RED, back_color="white").convert("RGB")
        image.save(path)
        return
    except Exception:
        if Image is None or ImageDraw is None:
            _write_minimal_png(path)
            return
        image = Image.new("RGB", (300, 300), "white")
        draw = ImageDraw.Draw(image)
        _draw_qr_fallback(draw, 20, 20, 260, data)
        image.save(path)


def _html_document(context: dict[str, Any], qr_url: str) -> str:
    return f"""
    <!doctype html>
    <html lang="ru">
      <head>
        <meta charset="utf-8">
        <style>
          @page {{ size: A4 landscape; margin: 22mm; }}
          body {{
            font-family: Arial, sans-serif;
            color: {BRAND_TEXT};
            margin: 0;
          }}
          .page {{
            min-height: 150mm;
            border: 3px solid {BRAND_RED};
            padding: 18mm 20mm;
            position: relative;
          }}
          .logo {{
            color: {BRAND_RED};
            font-size: 24px;
            font-weight: 700;
            line-height: .95;
            text-transform: uppercase;
          }}
          .title {{
            margin-top: 18mm;
            color: {BRAND_RED};
            font-size: 42px;
            font-weight: 700;
            text-transform: uppercase;
          }}
          .name {{
            margin-top: 12mm;
            font-size: 34px;
            font-weight: 700;
          }}
          .meta {{
            margin-top: 7mm;
            font-size: 18px;
            line-height: 1.45;
          }}
          .footer {{
            position: absolute;
            left: 20mm;
            right: 20mm;
            bottom: 16mm;
            display: flex;
            justify-content: space-between;
            align-items: end;
            font-size: 14px;
          }}
          .qr {{ width: 32mm; height: 32mm; }}
        </style>
      </head>
      <body>
        <main class="page">
          <div class="logo">Тихоокеанский<br>государственный<br>университет</div>
          <div class="title">{context.get("template_name", "Сертификат")}</div>
          <div class="name">{context.get("full_name", "")}</div>
          <div class="meta">
            <p>{context.get("award_category", "")}: {context.get("event_title", "")}</p>
            <p>{context.get("achievement", "")}</p>
            <p>Номер документа: {context.get("number", "")}</p>
          </div>
          <div class="footer">
            <div>
              <strong>{context.get("signatory_name", "")}</strong><br>
              {context.get("signatory_position", "")}<br>
              Подпись: {context.get("signature_status", "")}
            </div>
            <img class="qr" src="{qr_url}" alt="QR">
          </div>
        </main>
      </body>
    </html>
    """


def _pdf_escape(value: str) -> str:
    return (
        value.encode("ascii", "ignore")
        .decode("ascii")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _write_minimal_pdf(path: Path, context: dict[str, Any]) -> None:
    lines = [
        "Pacific National University",
        context.get("template_name", "TOGU document"),
        context.get("full_name", ""),
        context.get("event_title", ""),
        f"Number: {context.get('number', '')}",
        f"Verification: {context.get('qr_link', '')}",
    ]
    text_ops = []
    y = 520
    for line in lines:
        text_ops.append(f"72 {y} Td ({_pdf_escape(str(line))}) Tj")
        text_ops.append("0 -34 Td")
        y -= 34
    content = "BT /F1 20 Tf " + " ".join(text_ops) + " ET"
    objects = [
        "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
        "2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n",
        "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 842 595]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n",
        f"4 0 obj<</Length {len(content.encode('latin-1'))}>>stream\n{content}\nendstream\nendobj\n",
        "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n",
    ]
    pdf = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf.encode("latin-1")))
        pdf += obj
    xref = len(pdf.encode("latin-1"))
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF\n"
    path.write_bytes(pdf.encode("latin-1"))


def _write_pdf(path: Path, context: dict[str, Any], qr_path: Path, pdfa: bool = False) -> None:
    if os.getenv("ENABLE_WEASYPRINT", "").lower() not in {"1", "true", "yes"}:
        _write_minimal_pdf(path, context)
        return
    try:
        from weasyprint import HTML

        html = HTML(string=_html_document(context, qr_path.resolve().as_uri()), base_url=str(qr_path.parent))
        if pdfa:
            try:
                html.write_pdf(path, pdf_variant="pdf/a-2b")
                return
            except TypeError:
                pass
        html.write_pdf(path)
    except Exception:
        _write_minimal_pdf(path, context)


def _layout_config(context: dict[str, Any]) -> dict[str, Any]:
    layout = context.get("layout_config") or {}
    if isinstance(layout, str):
        try:
            layout = json.loads(layout)
        except json.JSONDecodeError:
            layout = {}
    return layout if isinstance(layout, dict) else {}


def _resolve_label(label: str, context: dict[str, Any]) -> str:
    value = str(label)
    replacements = {
        "full_name": context.get("full_name", ""),
        "status": context.get("participant_status", ""),
        "event_title": context.get("event_title", ""),
        "event_date": context.get("issued_at", ""),
        "hours": context.get("hours", ""),
        "document_number": context.get("number", ""),
        "qr_link": context.get("qr_link", ""),
        "signatory_name": context.get("signatory_name", ""),
        "signatory_position": context.get("signatory_position", ""),
    }
    for key, replacement in replacements.items():
        value = value.replace(f"{{{{ {key} }}}}", str(replacement))
        value = value.replace(f"{{{{{key}}}}}", str(replacement))
    return value


def render_document_assets(context: dict[str, Any]) -> dict[str, str]:
    docs_dir = ensure_documents_dir()
    number = context["number"]
    pdf_path = docs_dir / f"{number}.pdf"
    pdfa_path = docs_dir / f"{number}.pdfa"
    png_path = docs_dir / f"{number}.png"
    qr_path = docs_dir / f"{number}-qr.png"

    create_qr_image(context["qr_link"], qr_path)
    _write_pdf(pdf_path, context, qr_path, pdfa=False)
    _write_pdf(pdfa_path, context, qr_path, pdfa=True)

    Image, ImageDraw, _ = _pillow()
    if Image is None or ImageDraw is None:
        _write_minimal_png(png_path)
        return {
            "pdf_url": f"/documents/files/{number}/pdf",
            "archive_url": f"/documents/files/{number}/pdfa",
            "image_url": f"/documents/files/{number}/png",
            "qr_image_url": f"/documents/files/{number}/qr",
        }

    image = Image.new("RGB", (1600, 1100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((50, 50, 1550, 1050), outline=BRAND_RED, width=8)

    layout = _layout_config(context)
    elements = layout.get("elements") if isinstance(layout.get("elements"), list) else []
    if elements:
        for element in sorted(elements, key=lambda item: item.get("z", 0)):
            x = int(50 + (element.get("x", 0) / 100) * 1500)
            y = int(50 + (element.get("y", 0) / 100) * 1000)
            w = int((element.get("w", 20) / 100) * 1500)
            h = int((element.get("h", 8) / 100) * 1000)
            if element.get("type") == "qr":
                qr_img = Image.open(qr_path).resize((max(90, min(w, h)), max(90, min(w, h))))
                image.paste(qr_img, (x, y))
                continue
            text = _resolve_label(element.get("label", ""), context)
            fill = BRAND_RED if element.get("type") == "signature" else BRAND_TEXT
            draw.text((x, y), text, fill=fill, font=_font(int(element.get("fontSize", 18) * 1.35), True))
    else:
        draw.text((110, 105), "ТИХООКЕАНСКИЙ\nГОСУДАРСТВЕННЫЙ\nУНИВЕРСИТЕТ", fill=BRAND_RED, font=_font(42, True), spacing=2)
        draw.text((110, 320), context.get("template_name", "Сертификат").upper(), fill=BRAND_RED, font=_font(68, True))
        draw.text((110, 470), context.get("full_name", ""), fill=BRAND_TEXT, font=_font(58, True))
        draw.text((110, 570), context.get("event_title", ""), fill=BRAND_TEXT, font=_font(34))
        draw.text((110, 660), f"Номер: {number}", fill=BRAND_TEXT, font=_font(28))
        qr_img = Image.open(qr_path).resize((220, 220))
        image.paste(qr_img, (1250, 760))
    image.save(png_path)

    return {
        "pdf_url": f"/documents/files/{number}/pdf",
        "archive_url": f"/documents/files/{number}/pdfa",
        "image_url": f"/documents/files/{number}/png",
        "qr_image_url": f"/documents/files/{number}/qr",
    }


def ensure_document_assets(document_number: str, context: dict[str, Any] | None = None) -> None:
    docs_dir = ensure_documents_dir()
    if context:
        render_document_assets(context)
        return
    for suffix in (".pdf", ".pdfa", ".png", "-qr.png"):
        path = docs_dir / f"{document_number}{suffix}"
        if not path.exists():
            if suffix == "-qr.png":
                create_qr_image(document_number, path)
            elif suffix == ".png":
                Image, _, _ = _pillow()
                if Image is None:
                    _write_minimal_png(path)
                else:
                    Image.new("RGB", (1200, 800), "white").save(path)
            else:
                _write_minimal_pdf(path, {"number": document_number})
