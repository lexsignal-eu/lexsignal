import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import update_feeds
from build_agent_feed import build_documents

NOW=datetime(2026,11,9,18,0,tzinfo=timezone.utc)

def item(letter="a",days=1,authority="ESMA"):
    return {
        "id":"rss-"+letter*16,
        "date":(NOW-timedelta(days=days)).date().isoformat(),
        "authority":authority,
        "title":"Official regulator publication",
        "url":"https://www.esma.europa.eu/press-news/esma-news/test",
        "summary":"Example", "sourceType":"rss", "sectors":["fin"],
        "signalTier":"high",
    }

class ResilienceTests(unittest.TestCase):
    def test_failed_source_retains_recent_record(self):
        prior=item("a")
        status=[{"authority":"ESMA","status":"error","matched":0}]
        result=update_feeds.merge_observations({}, {prior["id"]:prior}, NOW,status)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["collectionState"],"cached")
        self.assertEqual(status[0]["cachedRecordCount"],1)
        self.assertEqual(status[0]["observedRecordCount"],0)

    def test_fresh_observation_preserves_first_seen(self):
        prior=item("a")
        prior["firstSeenAt"]="2026-11-05T09:00:00+00:00"
        prior["lastObservedAt"]="2026-11-07T09:00:00+00:00"
        result=update_feeds.merge_observations(
            {prior["id"]:dict(prior)}, {prior["id"]:prior}, NOW, [])
        self.assertEqual(result[0]["collectionState"],"observed")
        self.assertEqual(result[0]["firstSeenAt"],"2026-11-05T09:00:00+00:00")
        self.assertEqual(result[0]["lastObservedAt"],NOW.isoformat(timespec="seconds"))

    def test_missing_record_does_not_fake_new_observation(self):
        prior=item("a")
        prior["lastObservedAt"]="2026-11-07T09:00:00+00:00"
        result=update_feeds.merge_observations({}, {prior["id"]:prior}, NOW, [])
        self.assertEqual(result[0]["lastObservedAt"],"2026-11-07T09:00:00+00:00")

    def test_retention_horizon(self):
        stale=item("a",days=151)
        result=update_feeds.merge_observations({}, {stale["id"]:stale}, NOW, [])
        self.assertEqual(result,[])

    def test_new_records_deduplicated(self):
        prior=item("a")
        current=dict(prior)
        result=update_feeds.merge_observations(
            {current["id"]:current},{prior["id"]:prior},NOW,[])
        self.assertEqual(len(result),1)

    def test_prior_snapshot_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"regulatory_snapshot.json"
            path.write_text("invalid",encoding="utf-8")
            self.assertEqual(update_feeds.load_previous_snapshot(path),{})
            path.write_text(json.dumps({"schema":"incorrect","records":[item()]}),encoding="utf-8")
            self.assertEqual(update_feeds.load_previous_snapshot(path),{})
            path.write_text(json.dumps({"schema":"lexsignal-snapshot-v1","records":[item()]}),encoding="utf-8")
            self.assertEqual(len(update_feeds.load_previous_snapshot(path)),1)

    def test_agent_exposes_cached_state_and_errors(self):
        prior=item("a")
        prior["collectionState"]="cached"
        prior["lastObservedAt"]="2026-11-07T09:00:00+00:00"
        snapshot={"schema":"lexsignal-snapshot-v1",
                  "generatedAt":"2026-11-09T18:00:00+00:00",
                  "records":[prior],
                  "sources":[{"authority":"ESMA","status":"error","matched":0,
                              "cachedRecordCount":1,"observedRecordCount":0}]}
        docs=build_documents(snapshot)
        one=docs["updates.json"]["items"][0]
        self.assertEqual(one["collectionState"],"cached")
        self.assertEqual(one["lastObservedAt"],"2026-11-07T09:00:00+00:00")
        self.assertEqual(one["reviewStatus"],"unreviewed")
        self.assertEqual(docs["status.json"]["failedSourceCount"],1)
        self.assertEqual(docs["status.json"]["cachedRecordCount"],1)

if __name__=="__main__":
    unittest.main()
