# M8: Private document pipeline — extraction contract (not deployed)

**Status:** backend-library prototype only. No public endpoint, browser upload, authentication, object store, data processing service or customer production use.

## Available safe primitive

`backend/document_extract.py` provides `extract_docx(data: bytes, filename: str, declared_mime: str)`. It accepts bounded OOXML DOCX archives and yields in-memory text paragraphs with ordinal evidence locators and a SHA-256 content digest. It rejects unsupported types, masquerading PDFs, path traversal, macro/ActiveX binaries, suspicious expansion ratios, DTDs, malformed XML and empty/scanned text. Table cell text is traversed in document order.

This does **not** extract PDF, guarantee original page numbers, support OCR, validate legal claims or prove that an uploaded file is trustworthy. A paragraph ordinal can change if document text is edited. The digest is useful for integrity comparison only; it is not cryptographic proof of document authorship.

## Endpoint deployment gate

Before ANY personal/client data access:
1. Use a genuinely authenticated backend and server-checked tenant membership on every route and object read.
2. Verify content type and file signature; run malware scanning and strict size limits in an isolated execution environment. DOCX parsing in the application process alone is not a substitute for sandboxing.
3. Use private object storage and least-privileged signed access; no public Pages uploads, no browser-local copies of customer files.
4. Implement explicit customer consent, retention period, access logs, deletion/export, provider/security policy and GDPR materials.
5. Attach text excerpts to source digest, paragraph ordinal and upload-version ID. Where PDF is introduced later, use a vetted sandboxed PDF parser and page-number-specific locators; distinguish OCR uncertainty.
6. Run 20+ valid, malformed, encrypted, scanned, multi-page and table-heavy source fixtures and tenant isolation tests in CI.
7. Complete independent security review before any endpoint or customer file is enabled.

The UI's current Document Lab still processes only limited text-like files locally, as described in README. Do not claim server-side processing exists.
