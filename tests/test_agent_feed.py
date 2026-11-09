import unittest
from build_agent_feed import normalise, build_documents, official_url, openapi_spec

class AgentFeedTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "id": "rss-0123456789abcdef", "date": "2026-11-09", "authority": "ESMA",
            "title": "Regulator publishes guidelines", "category": "Financial regulation",
            "eventType": "guidance", "signalTier": "high",
            "summary": "An official publication.", "sectors": ["fin"],
            "url": "https://www.esma.europa.eu/news/example",
        }
        self.snapshot = {"schema": "lexsignal-snapshot-v1",
                         "generatedAt": "2026-11-09T18:00:00+00:00",
                         "records": [self.record],
                         "sources": [{"authority":"ESMA","status":"ok","matched":1}]}

    def test_all_items_unreviewed(self):
        item=build_documents(self.snapshot)["updates.json"]["items"][0]
        self.assertEqual(item["reviewStatus"], "unreviewed")
        self.assertEqual(item["applicabilityAssessment"], "not_performed")
        self.assertEqual(item["sourceUrl"], self.record["url"])

    def test_high_tier_not_interpreted_as_approval(self):
        docs=build_documents(self.snapshot)
        self.assertEqual(docs["signals.json"]["count"],1)
        self.assertEqual(docs["signals.json"]["reviewStatus"],"all_items_unreviewed")

    def test_invalid_source_rejected(self):
        bad={**self.record,"url":"https://example.com/evil"}
        self.assertIsNone(normalise(bad))
        self.assertFalse(official_url("http://www.esma.europa.eu/notsecure"))

    def test_background_excluded_from_high_signals(self):
        record={**self.record,"signalTier":"background"}
        self.snapshot["records"]=[record]
        docs=build_documents(self.snapshot)
        self.assertEqual(docs["updates.json"]["count"],1)
        self.assertEqual(docs["signals.json"]["count"],0)

    def test_unknown_schema_rejected(self):
        self.snapshot["schema"]="untrusted"
        with self.assertRaises(ValueError):
            build_documents(self.snapshot)

    def test_openapi_paths_are_static(self):
        spec=openapi_spec()
        self.assertEqual(spec["openapi"],"3.1.2")
        self.assertIn("/api/v1/updates.json",spec["paths"])
        self.assertIn("/api/v1/status.json",spec["paths"])
        self.assertIn("/api/v1/knowledge.json",spec["paths"])

    def test_duplicates_collapse(self):
        self.snapshot["records"].append(dict(self.record))
        self.assertEqual(build_documents(self.snapshot)["updates.json"]["count"],1)

if __name__=="__main__":
    unittest.main()
