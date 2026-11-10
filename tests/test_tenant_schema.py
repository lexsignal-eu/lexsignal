"""SQLite/D1 draft tenant-scoped relationship tests. No deployed database."""
import sqlite3
import unittest
from pathlib import Path


SCHEMA = (Path(__file__).resolve().parents[1] / "backend/schema.sql").read_text(encoding="utf-8")


def database():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO organizations(id,name) VALUES (?,?)",
                     [("org-a","Alpha"), ("org-b","Beta")])
    conn.executemany("INSERT INTO users(id,email) VALUES (?,?)",
                     [("alice","alice@example.test"), ("bob","bob@example.test")])
    conn.executemany("INSERT INTO memberships(organization_id,user_id,role) VALUES (?,?,?)",
                     [("org-a","alice","analyst"), ("org-b","bob","admin")])
    conn.execute(
        "INSERT INTO regulatory_sources(id,authority,source_url,title) VALUES (?,?,?,?)",
        ("source-1","ESMA","https://www.esma.europa.eu/","Official release"))
    conn.commit()
    return conn


class TenantSchemaTests(unittest.TestCase):
    def test_same_tenant_reviewer_allowed(self):
        conn = database()
        try:
            conn.execute(
                "INSERT INTO review_decisions(id,organization_id,source_id,reviewer_user_id,inclusion_status) VALUES (?,?,?,?,?)",
                ("r1","org-a","source-1","alice","undecided"))
            conn.commit()
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM review_decisions").fetchone()[0],1)
        finally:
            conn.close()

    def test_cross_tenant_reviewer_and_owner_rejected(self):
        conn = database()
        try:
            conn.execute(
                "INSERT INTO review_decisions(id,organization_id,source_id,reviewer_user_id,inclusion_status) VALUES (?,?,?,?,?)",
                ("r1","org-a","source-1","bob","undecided"))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.commit()
            conn.rollback()
            conn.execute(
                "INSERT INTO review_decisions(id,organization_id,source_id,reviewer_user_id,owner_user_id,inclusion_status) VALUES (?,?,?,?,?,?)",
                ("r2","org-a","source-1","alice","bob","undecided"))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.commit()
            conn.rollback()
        finally:
            conn.close()

    def test_cross_tenant_document_uploader_rejected(self):
        conn = database()
        try:
            conn.execute(
                "INSERT INTO stored_documents(id,organization_id,uploaded_by_user_id,private_object_key,original_filename,content_type,byte_length) VALUES (?,?,?,?,?,?,?)",
                ("doc1","org-b","alice","private/key","file.txt","text/plain",15))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.commit()
            conn.rollback()
        finally:
            conn.close()

    def test_cross_tenant_connector_owner_rejected(self):
        conn = database()
        try:
            conn.execute(
                "INSERT INTO connector_accounts(id,organization_id,user_id,provider,provider_account_id,granted_scopes,encrypted_tokens) VALUES (?,?,?,?,?,?,?)",
                ("con1","org-b","alice","gmail","account-1","read","encrypted-placeholder"))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.commit()
            conn.rollback()
        finally:
            conn.close()

    def test_invalid_membership_role_rejected(self):
        conn = database()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE memberships SET role='owner' WHERE organization_id='org-a'")
        finally:
            conn.close()

    def test_deleting_organization_removes_scoped_records(self):
        conn = database()
        try:
            conn.execute(
                "INSERT INTO review_decisions(id,organization_id,source_id,reviewer_user_id,inclusion_status) VALUES (?,?,?,?,?)",
                ("r1","org-a","source-1","alice","include"))
            conn.execute(
                "INSERT INTO stored_documents(id,organization_id,uploaded_by_user_id,private_object_key,original_filename,content_type,byte_length) VALUES (?,?,?,?,?,?,?)",
                ("doc1","org-a","alice","private/key","file.txt","text/plain",15))
            conn.commit()
            conn.execute("DELETE FROM organizations WHERE id='org-a'")
            conn.commit()
            for table in ("memberships","review_decisions","stored_documents"):
                self.assertEqual(conn.execute(
                    "SELECT COUNT(*) FROM " + table + " WHERE organization_id='org-a'").fetchone()[0],0)
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM memberships WHERE organization_id='org-b'").fetchone()[0],1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
