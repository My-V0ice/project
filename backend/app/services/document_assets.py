from __future__ import annotations

from base64 import b64decode
from pathlib import Path

from app.core.config import BASE_DIR


DOCUMENTS_DIR = BASE_DIR / "documents"

_MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 66>>stream
BT
/F1 14 Tf
36 92 Td
(TOGU Demo Document) Tj
ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000241 00000 n 
0000000357 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
427
%%EOF
"""

_MINIMAL_PNG = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAoMBgQf9xX0AAAAASUVORK5CYII="
)


def ensure_documents_dir() -> Path:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    return DOCUMENTS_DIR


def ensure_document_assets(document_number: str) -> None:
    docs_dir = ensure_documents_dir()
    pdf_path = docs_dir / f"{document_number}.pdf"
    pdfa_path = docs_dir / f"{document_number}.pdfa"
    png_path = docs_dir / f"{document_number}.png"

    if not pdf_path.exists():
        pdf_path.write_bytes(_MINIMAL_PDF)
    if not pdfa_path.exists():
        pdfa_path.write_bytes(_MINIMAL_PDF)
    if not png_path.exists():
        png_path.write_bytes(_MINIMAL_PNG)

