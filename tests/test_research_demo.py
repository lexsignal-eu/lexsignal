"""Regression and red-team checks for public synthetic evidence worksheets."""
import copy
import json
import unittest
from pathlib import Path

from knowledge_index import KnowledgeValidationError, build_index
from research_demo import build_example_research

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


class ExampleResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = read("regulatory_library.json")
        cls.snapshot = read("regulatory_snapshot.json")
        cls.registry = read("source_registry.json")
        cls.lenses = read("example_profile_lenses.json")
        cls.index = build_index(cls.library, cls.snapshot, cls.registry)

    def render(self, library=None, lenses=None, index=None):
        return build_example_research(
            self.library if library is None else library,
            self.lenses if lenses is None else lenses,
            self.index if index is None else index,
        )

    def test_demo_is_all_synthetic_and_requires_human_review(self):
        data = self.render()
        self.assertEqual(data["schema"], "lexsignal-example-research-v1")
        self.assertEqual(len(data["profiles"]), 2)
        for p in data["profiles"]:
            self.assertIn("illustrative", p["name"].lower())
            for item in p["items"]:
                self.assertEqual(item["evidenceStatus"], "reference_only_provision_not_verified")
                self.assertEqual(item["applicabilityStatus"], "not_assessed")
                self.assertTrue(item["humanReviewRequired"])
                self.assertEqual(item["provenanceStatus"], "curated_reference_metadata")
                self.assertNotIn("legalObligation", item)
                self.assertNotIn("verifiedProvision", item)
                self.assertTrue(item["sourceUrl"].startswith("https://"))
                for milestone in item["milestones"]:
                    self.assertIn("scopeNote", milestone)
                    self.assertIn("sourceUrl", milestone)

    def test_deterministic_output_and_distinct_profiles(self):
        self.assertEqual(self.render(), self.render())
        result = self.render()
        self.assertNotEqual(result["profiles"][0]["id"], result["profiles"][1]["id"])
        self.assertEqual(len(result["profiles"][0]["items"]), 4)
        self.assertEqual(len(result["profiles"][1]["items"]), 6)

    def test_unknown_duplicate_or_spoofed_sources_fail_closed(self):
        for bad_id in ["not-a-law", "unknown-candidate", "attacker-policy"]:
            with self.subTest(bad_id=bad_id):
                lens = copy.deepcopy(self.lenses)
                lens["profiles"][0]["candidates"][0]["actId"] = bad_id
                with self.assertRaises(KnowledgeValidationError):
                    self.render(lenses=lens)
        for bad in [
            "https://evil.tld/act",
            "https://eur-lex.europa.eu.evil.tld/eli/reg/2024/1689/oj",
            "http://eur-lex.europa.eu/eli/reg/2024/1689/oj",
            "https://user:password@eur-lex.europa.eu/eli/reg/2024/1689/oj",
        ]:
            with self.subTest(url=bad):
                law = copy.deepcopy(self.library)
                law["acts"][0]["source"] = bad
                with self.assertRaises(KnowledgeValidationError):
                    self.render(library=law)

    def test_missing_canonical_binding_or_unreviewed_status_fail_closed(self):
        index = copy.deepcopy(self.index)
        row = next(e for e in index["entities"] if e["id"] == "act:dora")
        row["officialSourceUrl"] = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
        with self.assertRaises(KnowledgeValidationError):
            self.render(index=index)
        index = copy.deepcopy(self.index)
        row = next(e for e in index["entities"] if e["id"] == "act:dora")
        row["reviewStatus"] = "unreviewed_automated"
        with self.assertRaises(KnowledgeValidationError):
            self.render(index=index)

    def test_30_independently_mutated_invalid_inputs_are_rejected(self):
        # Multiple original source records, multiple profiles, varied hostile edits.
        for i in range(30):
            with self.subTest(case=i):
                lens = copy.deepcopy(self.lenses)
                profile = lens["profiles"][i % len(lens["profiles"])]
                target = profile["candidates"][i % len(profile["candidates"])]
                mode = i % 6
                if mode == 0:
                    target["actId"] = "invented-" + str(i)
                elif mode == 1:
                    target["why"] = ""
                elif mode == 2:
                    target["verify"] = "x"
                elif mode == 3:
                    target["actId"] = profile["candidates"][0]["actId"]
                    # Ensure duplicate against a *different* candidate.
                    if target is profile["candidates"][0]:
                        target = profile["candidates"][1]
                        target["actId"] = profile["candidates"][0]["actId"]
                elif mode == 4:
                    profile["id"] = "invalid id!"
                else:
                    target["why"] = None
                with self.assertRaises(KnowledgeValidationError):
                    self.render(lenses=lens)


if __name__ == "__main__":
    unittest.main()
