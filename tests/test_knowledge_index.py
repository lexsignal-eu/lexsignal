"""P0 data contracts and provenance tests; all offline, stdlib-only."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import update_feeds
from knowledge_index import (
    KnowledgeValidationError, build_index, diff_metadata, official_url
)
from build_knowledge_index import main


ROOT = Path(__file__).resolve().parents[1]


def fixture():
    def read(name):
        return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
    return read("regulatory_library.json"), read("regulatory_snapshot.json"), read("source_registry.json")


class KnowledgeIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library, cls.snapshot, cls.registry = fixture()

    def built(self):
        return build_index(copy.deepcopy(self.library), copy.deepcopy(self.snapshot), copy.deepcopy(self.registry))

    def test_contract_and_entity_relationships(self):
        index = self.built()
        self.assertEqual(index["schema"], "lexsignal-knowledge-v1")
        counts = index["counts"]
        self.assertEqual(counts["legalInstruments"], len(self.library["acts"]))
        self.assertEqual(counts["regulatoryMilestones"], len(self.library["milestones"]))
        self.assertEqual(counts["rssPublications"], len(self.snapshot["records"]))
        self.assertEqual(counts["authorities"], 4)
        self.assertEqual(counts["relationships"], counts["regulatoryMilestones"] + counts["rssPublications"])
        ids = [item["id"] for item in index["entities"]]
        self.assertEqual(ids, sorted(set(ids)))
        self.assertEqual(len(ids), sum(counts[k] for k in ("legalInstruments","regulatoryMilestones","rssPublications","authorities")))
        for relation in index["relationships"]:
            self.assertIn(relation["from"], ids)
            self.assertIn(relation["to"], ids)

    def test_strictly_grounded_links_only(self):
        index = self.built()
        for relation in index["relationships"]:
            self.assertIn(relation["type"], ("milestone_of", "published_by"))
            self.assertNotIn("inferred", relation["basis"])
        # Even an RSS item mentioning MiCA should not be linked to the MiCA act
        # unless we have verifiable provision-level evidence.
        for r in index["relationships"]:
            if r["from"].startswith("publication:"):
                self.assertTrue(r["to"].startswith("authority:"))

    def test_unreviewed_rss_and_source_provenance_are_preserved(self):
        index = self.built()
        source = next(x for x in index["entities"] if x["type"] == "source_publication")
        self.assertEqual(source["reviewStatus"], "unreviewed_automated")
        self.assertEqual(source["provenance"]["method"], "unreviewed_official_rss_extract")
        self.assertIn(source["provenance"]["collectionState"], ("observed", "cached", "unknown"))
        act = next(x for x in index["entities"] if x["type"] == "legal_instrument")
        self.assertEqual(act["reviewStatus"], "curated_reference_metadata")
        self.assertNotEqual(act["reviewStatus"], "verified_legal_conclusion")

    def test_reproducible_fingerprint_across_timestamp_updates(self):
        base = self.built()
        changed = copy.deepcopy(self.snapshot)
        changed["generatedAt"] = "2026-11-10T10:00:00+00:00"
        for row in changed["records"]:
            row["lastObservedAt"] = "2026-11-10T10:00:00+00:00"
        other = build_index(self.library, changed, self.registry)
        self.assertNotEqual(base["provenance"]["rssSnapshotGeneratedAt"], other["provenance"]["rssSnapshotGeneratedAt"])
        self.assertEqual([e["metadataFingerprint"] for e in base["entities"]],
                         [e["metadataFingerprint"] for e in other["entities"]])
        self.assertEqual(diff_metadata(base, other)["events"], [])

    def test_real_metadata_edit_changes_fingerprint_but_does_not_assert_legal_change(self):
        before = self.built()
        edited = copy.deepcopy(self.library)
        edited["acts"][0]["summary"] += " Editorial metadata clarification."
        after = build_index(edited, self.snapshot, self.registry)
        events = diff_metadata(before, after)["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["eventType"], "metadata_changed")
        self.assertEqual(events[0]["entityId"], "act:" + edited["acts"][0]["id"])
        self.assertIs(events[0]["legalChangeVerified"], False)

    def test_record_removed_from_feed_is_not_reported_as_repealed(self):
        before = self.built()
        after_snap = copy.deepcopy(self.snapshot)
        old = after_snap["records"].pop()
        after = build_index(self.library, after_snap, self.registry)
        changes = diff_metadata(before, after)
        e = next(e for e in changes["events"] if e["entityId"] == "publication:" + old["id"])
        self.assertEqual(e["eventType"], "record_no_longer_indexed")
        self.assertIs(e["legalChangeVerified"], False)

    def test_authorities_match_existing_collector(self):
        actual = {name: url for name, url in update_feeds.SOURCES}
        declared = {r["name"]: r["rssEndpoint"] for r in self.registry["authorities"]}
        self.assertEqual(actual, declared)

    def test_malicious_and_arbitrary_urls_rejected(self):
        for u in [
            "https://www.esma.europa.eu.evil.example/doc",
            "http://www.esma.europa.eu/",
            "https://user:pass@www.esma.europa.eu/foo",
            "https://www.gov.ie:8443/x",
            "https://example.com/official-law",
            "https://europa.eu@example.com/",
        ]:
            self.assertFalse(official_url(u), u)
        for u in [
            "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
            "https://www.esma.europa.eu/rss.xml",
            "https://www.gov.ie/en/",
        ]:
            self.assertTrue(official_url(u), u)

    def test_duplicate_identifier_and_invalid_parent_are_rejected(self):
        lib = copy.deepcopy(self.library)
        lib["milestones"].append(copy.deepcopy(lib["milestones"][0]))
        with self.assertRaisesRegex(KnowledgeValidationError, "Duplicate"):
            build_index(lib, self.snapshot, self.registry)
        lib = copy.deepcopy(self.library)
        lib["milestones"][0]["act"] = "nonexistent-legal-instrument"
        with self.assertRaisesRegex(KnowledgeValidationError, "Unknown linked"):
            build_index(lib, self.snapshot, self.registry)

    def test_impossible_date_and_unknown_publisher_are_rejected(self):
        lib = copy.deepcopy(self.library)
        lib["milestones"][0]["date"] = "2026-02-30"
        with self.assertRaisesRegex(KnowledgeValidationError, "impossible"):
            build_index(lib, self.snapshot, self.registry)
        snap = copy.deepcopy(self.snapshot)
        snap["records"][0]["authority"] = "Unnamed source"
        with self.assertRaisesRegex(KnowledgeValidationError, "Unregistered"):
            build_index(self.library, snap, self.registry)

    def test_reject_non_official_publication_link(self):
        snap = copy.deepcopy(self.snapshot)
        snap["records"][0]["url"] = "https://www.esma.europa.eu.attacker.tld/item"
        with self.assertRaisesRegex(KnowledgeValidationError, "Non-official"):
            build_index(self.library, snap, self.registry)

    def test_cli_generates_valid_json_and_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "knowledge.json"
            self.assertEqual(main(["--out", str(output)]), 0)
            first = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(first["schema"], "lexsignal-knowledge-v1")
            changed = Path(temp) / "changes.json"
            new = Path(temp) / "later.json"
            self.assertEqual(main(["--out", str(new), "--previous", str(output),
                                    "--changes-out", str(changed)]), 0)
            diff = json.loads(changed.read_text(encoding="utf-8"))
            self.assertEqual(diff["schema"], "lexsignal-metadata-diff-v1")
            self.assertEqual(diff["events"], [])


if __name__ == "__main__":
    unittest.main()
