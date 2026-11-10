"""M3 public artifact acceptance tests; offline, standard library only."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_site import RELEASE_SCHEMA, SiteBuildError, build_site, validate_local_links


ROOT = Path(__file__).resolve().parents[1]


class ReleaseArtifactTests(unittest.TestCase):
    def test_clean_build_contains_all_public_pages_feeds_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "preview"
            manifest = build_site(ROOT, out, "test-revision")
            self.assertEqual(manifest["schema"], RELEASE_SCHEMA)
            self.assertEqual(manifest["sourceRevision"], "test-revision")
            self.assertGreater(manifest["localLinksValidated"], 5)
            required = [
                "index.html", "workspace.html", "documents.html",
                "regulatory-library.html", "global-signals.html",
                "api/v1/updates.json", "api/v1/status.json",
                "api/v1/knowledge.json", "api/v1/openapi.json",
                "api/v1/build-manifest.json",
                "data/regulatory_library.json",
                "brand/lexsignal-sphere-approved.webp",
            ]
            for name in required:
                self.assertTrue((out / name).is_file(), name)
            published = json.loads((out / "api/v1/build-manifest.json").read_text())
            self.assertEqual(published, manifest)
            self.assertNotIn("api/v1/build-manifest.json", published["files"])
            self.assertEqual(published["artifactFileCount"], len(published["files"]))
            for rel, digest in published["files"].items():
                self.assertEqual(hashlib.sha256((out / rel).read_bytes()).hexdigest(), digest)

    def test_same_inputs_produce_same_manifest_and_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            one = build_site(ROOT, first, "fixed-sha")
            two = build_site(ROOT, second, "fixed-sha")
            self.assertEqual(one, two)
            self.assertEqual(
                (first / "api/v1/build-manifest.json").read_bytes(),
                (second / "api/v1/build-manifest.json").read_bytes()
            )

    def test_refuses_preexisting_nonempty_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            (out / "sentinel.txt").write_text("do not remove", encoding="utf-8")
            with self.assertRaisesRegex(SiteBuildError, "not empty"):
                build_site(ROOT, out)
            self.assertEqual((out / "sentinel.txt").read_text(), "do not remove")

    def test_missing_local_links_and_path_escapes_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            (out / "index.html").write_text(
                '<a href="missing.html">Missing</a>', encoding="utf-8"
            )
            with self.assertRaisesRegex(SiteBuildError, "Missing local target"):
                validate_local_links(out)
            (out / "index.html").write_text(
                '<img src="../secrets.txt">', encoding="utf-8"
            )
            with self.assertRaisesRegex(SiteBuildError, "escapes site root"):
                validate_local_links(out)
            (out / "index.html").write_text(
                '<a href="javascript:alert(1)">bad</a>', encoding="utf-8"
            )
            with self.assertRaisesRegex(SiteBuildError, "Disallowed link protocol"):
                validate_local_links(out)

    def test_known_project_prefix_resolves_to_index(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            (out / "index.html").write_text(
                '<a href="/lexsignal/">Home</a><a href="https://eur-lex.europa.eu/">Outside</a>',
                encoding="utf-8",
            )
            self.assertEqual(validate_local_links(out), 1)


if __name__ == "__main__":
    unittest.main()
