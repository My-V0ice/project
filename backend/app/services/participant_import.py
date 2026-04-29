from __future__ import annotations

import csv
from io import BytesIO, StringIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET


FIELD_ALIASES = {
    "full_name": {"full_name", "fio", "фио", "фамилия имя отчество", "полное имя"},
    "email": {"email", "e-mail", "mail", "почта", "электронная почта"},
    "status": {"status", "статус"},
    "achievement": {"achievement", "достижение", "результат"},
    "hours": {"hours", "часы", "часов"},
    "award_category": {"award_category", "категория", "награда"},
}


def normalize_header(value: str) -> str:
    return value.strip().lower().replace("\ufeff", "")


def guess_mapping(headers: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    normalized = {normalize_header(header): header for header in headers}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def parse_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = content.decode("utf-8-sig")
    sample = text[:2048]
    dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    reader = csv.DictReader(StringIO(text), dialect=dialect)
    return list(reader.fieldnames or []), [dict(row) for row in reader]


def _xlsx_shared_strings(zip_file: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values = []
    for item in root.findall(".//x:si", ns):
        values.append("".join(text.text or "" for text in item.findall(".//x:t", ns)))
    return values


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    value = cell.find("x:v", ns)
    if value is None or value.text is None:
        inline = cell.find(".//x:t", ns)
        return inline.text if inline is not None and inline.text else ""
    if cell.attrib.get("t") == "s":
        index = int(value.text)
        return shared[index] if 0 <= index < len(shared) else ""
    return value.text


def parse_xlsx(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    with ZipFile(BytesIO(content)) as zip_file:
        shared = _xlsx_shared_strings(zip_file)
        sheet_name = next(name for name in zip_file.namelist() if name.startswith("xl/worksheets/sheet"))
        root = ET.fromstring(zip_file.read(sheet_name))
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows = []
        for row in root.findall(".//x:sheetData/x:row", ns):
            values = [_cell_value(cell, shared) for cell in row.findall("x:c", ns)]
            rows.append(values)
    if not rows:
        return [], []
    headers = [str(value).strip() for value in rows[0]]
    data = []
    for row in rows[1:]:
        data.append({header: row[index] if index < len(row) else "" for index, header in enumerate(headers)})
    return headers, data


def parse_participant_file(filename: str, content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if filename.lower().endswith(".xlsx"):
        return parse_xlsx(content)
    return parse_csv(content)
