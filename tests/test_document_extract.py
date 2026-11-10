"""M8 future-backend DOCX extraction: offline security and provenance tests."""
import io
import unittest
import zipfile
from backend.document_extract import (
    DOCX_MIME, DocumentRejected, extract_docx, MAX_INPUT_BYTES
)

CONTENT = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
           '<Override PartName="/word/document.xml" '
           'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
           '</Types>').encode()
XML = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
       '<w:body><w:p><w:r><w:t>First paragraph</w:t></w:r></w:p>'
       '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
       '<w:p><w:r><w:t>Final paragraph</w:t></w:r></w:p></w:body></w:document>').encode()


def docx(xml=XML, extra=None, types=CONTENT):
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", types)
            z.writestr("word/document.xml", xml)
            z.writestr("_rels/.rels", "<Relationships/>")
            for name, content in (extra or {}).items():
                z.writestr(name, content)
        return buffer.getvalue()


class DocumentExtractionTests(unittest.TestCase):
    def test_extract_paragraph_and_table_text_with_ordinals(self):
        data = docx()
        result = extract_docx(data, "illustrative.docx")
        self.assertEqual(result["schema"], "lexsignal-document-extract-v1")
        self.assertEqual(result["paragraphCount"], 3)
        self.assertEqual([p["text"] for p in result["paragraphs"]],
                         ["First paragraph", "Table cell", "Final paragraph"])
        self.assertEqual(result["paragraphs"][1]["locator"], "word/document.xml#paragraph-2")
        self.assertEqual(len(result["contentSha256"]), 64)
        self.assertEqual(result["evidenceKind"], "document_paragraph_ordinal_not_page_number")
        self.assertEqual(result["extractionStatus"], "unverified_source_text")
        self.assertNotIn("privateObjectKey", result)

    def test_reject_unsafe_names_types_and_pdf_masquerading_as_docx(self):
        data = docx()
        for name in ["../secret.docx", "dir/file.docx", "invoice.docm", "a.pdf", "bad\x00.docx", ""]:
            with self.subTest(name=name), self.assertRaises(DocumentRejected):
                extract_docx(data, name)
        for media in ["application/pdf", "", None, "application/octet-stream"]:
            with self.subTest(media=media), self.assertRaises(DocumentRejected):
                extract_docx(data, "test.docx", media)
        for data in [b"%PDF-1.7 fake", b"PKgarbage", b"", None, "strings", b"x"*(MAX_INPUT_BYTES+1)]:
            with self.subTest(data_type=type(data)), self.assertRaises(DocumentRejected):
                extract_docx(data, "test.docx")

    def test_reject_bomb_dtd_macro_path_traversal_and_empty_text(self):
        variants = [
            docx(xml=b'<!DOCTYPE doc [<!ENTITY x "bad">]>'+XML),
            docx(extra={"word/vbaProject.bin":b"bad"}),
            docx(extra={"word/activeX/activeX1.xml":b"bad"}),
            docx(extra={"../unexpected":b"bad"}),
            docx(xml=XML.replace(b"First paragraph", b"").replace(b"Table cell", b"").replace(b"Final paragraph", b"")),
            docx(xml=b"<not-xml>"),
            docx(types=b"<Types/>"),
            docx(xml=b"<root/>"),
        ]
        for i,bad in enumerate(variants):
            with self.subTest(case=i), self.assertRaises(DocumentRejected):
                extract_docx(bad,"test.docx")

    def test_reject_20_malformed_document_and_scope_variants(self):
        for i in range(20):
            with self.subTest(case=i):
                if i % 4 == 0:
                    payload=docx(xml=(b"<root" + b"a"*i + b"/>"))
                    fn="test.docx"
                elif i % 4 == 1:
                    payload=docx(types=b"<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'/>")
                    fn="test.docx"
                elif i % 4 == 2:
                    payload=docx()
                    fn="../client"+str(i)+".docx"
                else:
                    payload=docx()
                    fn="test.docx"
                with self.assertRaises(DocumentRejected):
                    extract_docx(payload,fn,"application/pdf" if i % 4 == 3 else DOCX_MIME)

if __name__=="__main__":
    unittest.main()
