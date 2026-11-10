"""Conservative DOCX-only in-memory extraction primitive for a FUTURE private backend.

No route, persistence or upload endpoint is deployed. Never ingest real client
documents on public GitHub Pages. PDF is NOT supported by this stdlib module.
Return paragraph locators, not fictitious PDF page coordinates.
"""
from __future__ import annotations

import hashlib
import io
import re
import zipfile
from xml.etree import ElementTree as ET

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAIN_DOC_MIME = DOCX_MIME + ".main+xml"
WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CT_NS = "{http://schemas.openxmlformats.org/package/2006/content-types}"
MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_EXPANDED_BYTES = 20 * 1024 * 1024
MAX_PARTS = 300
MAX_PARAGRAPHS = 2500
MAX_TEXT_CHARS = 250000


class DocumentRejected(ValueError):
    """Unsafe, unsupported or unverifiable source document."""


def _safe_filename(value):
    if not isinstance(value, str) or len(value) > 150:
        raise DocumentRejected("Invalid document name")
    if not re.fullmatch(r"[A-Za-z0-9 _.,()+-]+\.docx", value, re.IGNORECASE):
        raise DocumentRejected("Only simple DOCX filenames are accepted")
    return value


def _parse_xml(xml_bytes):
    if b"<!DOCTYPE" in xml_bytes.upper() or b"<!ENTITY" in xml_bytes.upper():
        raise DocumentRejected("Embedded DTD/entity definitions are not supported")
    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise DocumentRejected("Malformed DOCX XML") from exc


def extract_docx(data, filename, declared_mime=DOCX_MIME):
    """Extract paragraphs and their in-file ordinal locators, in memory only.

    Calls require a validated session + tenant membership in the future API.
    This helper itself does not authenticate users or store private bytes.
    """
    name = _safe_filename(filename)
    if declared_mime != DOCX_MIME:
        raise DocumentRejected("Invalid DOCX declared media type")
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_INPUT_BYTES:
        raise DocumentRejected("Document size or byte type rejected")
    if not data.startswith(b"PK\x03\x04"):
        raise DocumentRejected("DOCX must have an OOXML ZIP signature")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            if not 2 <= len(infos) <= MAX_PARTS:
                raise DocumentRejected("Unexpected DOCX archive size")
            names = set()
            expanded = 0
            for info in infos:
                if info.filename in names or info.filename.startswith("/") or ".." in info.filename.split("/"):
                    raise DocumentRejected("Duplicate or unsafe DOCX entry name")
                names.add(info.filename)
                if info.flag_bits & 1:
                    raise DocumentRejected("Encrypted archive entries are unsupported")
                if info.filename.lower().endswith(("vbaproject.bin", ".exe", ".dll")) or "activex/" in info.filename.lower():
                    raise DocumentRejected("Macro/embedded executable content unsupported")
                expanded += info.file_size
                if expanded > MAX_EXPANDED_BYTES:
                    raise DocumentRejected("Expanded document exceeds size limit")
                if info.file_size > 0 and (info.compress_size == 0 or info.file_size > max(1,info.compress_size)*200):
                    raise DocumentRejected("Suspicious archive compression ratio")
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise DocumentRejected("Missing required DOCX parts")
            content_types = _parse_xml(z.read("[Content_Types].xml"))
            allowed = any(x.tag == CT_NS+"Override" and
                          x.attrib.get("PartName") == "/word/document.xml" and
                          x.attrib.get("ContentType") == MAIN_DOC_MIME
                          for x in content_types)
            if not allowed:
                raise DocumentRejected("Not a supported OOXML word-processing document")
            source = z.read("word/document.xml")
            tree = _parse_xml(source)
            if tree.tag != WORD_NS+"document":
                raise DocumentRejected("Unexpected Word document root")
            paragraphs = []
            total = 0
            for p in tree.iter(WORD_NS+"p"):
                text = "".join((t.text or "") for t in p.iter(WORD_NS+"t")).strip()
                if not text:
                    continue
                total += len(text)
                if len(paragraphs) >= MAX_PARAGRAPHS or total > MAX_TEXT_CHARS:
                    raise DocumentRejected("Too much extracted text")
                n = len(paragraphs)+1
                paragraphs.append({
                    "ordinal": n,
                    "locator": f"word/document.xml#paragraph-{n}",
                    "text": text,
                })
    except (zipfile.BadZipFile, EOFError, RuntimeError) as exc:
        raise DocumentRejected("Invalid DOCX ZIP archive") from exc
    if not paragraphs:
        raise DocumentRejected("No extractable text paragraphs; scanned/image-only content unsupported")
    return {
        "schema": "lexsignal-document-extract-v1",
        "extractionStatus": "unverified_source_text",
        "sourceType": "docx",
        "filename": name,
        "declaredContentType": declared_mime,
        "contentSha256": hashlib.sha256(data).hexdigest(),
        "evidenceKind": "document_paragraph_ordinal_not_page_number",
        "paragraphCount": len(paragraphs),
        "paragraphs": paragraphs,
        "limitations": "In-memory OOXML text extraction only. No provenance, signature, page coordinates, OCR, legal interpretation or safe API deployment is asserted.",
    }
