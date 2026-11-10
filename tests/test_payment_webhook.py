"""Offline M10 payment webhook gate tests: no Stripe account or network."""
import hashlib
import hmac
import json
import sqlite3
import unittest
from backend.payment_webhook import (
    WebhookRejected, verify_test_webhook, record_verified_test_event
)

SECRET="whsec_illustrative_test_only"
NOW=1794312000
BASE={"object":"event","id":"evt_demo1234","type":"checkout.session.completed",
      "created":NOW,"livemode":False,"data":{"object":{"id":"cs_test_demo"}}}


def signed(event=None, timestamp=NOW, secret=SECRET):
    body=json.dumps(BASE if event is None else event,separators=(",",":"),sort_keys=True).encode()
    digest=hmac.new(secret.encode(),str(timestamp).encode()+b"."+body,hashlib.sha256).hexdigest()
    return body,"t="+str(timestamp)+",v1="+digest


class WebhookTests(unittest.TestCase):
    def test_valid_snapshot_event_and_idempotent_ledger(self):
        body,header=signed()
        event=verify_test_webhook(body,header,SECRET,now=NOW)
        self.assertEqual(event.event_id,"evt_demo1234")
        self.assertEqual(event.event_type,"checkout.session.completed")
        db=sqlite3.connect(":memory:")
        db.execute("CREATE TABLE payment_events(provider TEXT NOT NULL,event_id TEXT NOT NULL,received_at TEXT DEFAULT CURRENT_TIMESTAMP,processed_at TEXT,PRIMARY KEY(provider,event_id))")
        self.assertTrue(record_verified_test_event(db,event))
        self.assertFalse(record_verified_test_event(db,event))
        self.assertEqual(db.execute("SELECT count(*) FROM payment_events").fetchone()[0],1)
        self.assertEqual(db.execute("SELECT provider FROM payment_events").fetchone()[0],"stripe_test")

    def test_reject_tampering_wrong_secret_or_time_skew(self):
        body,header=signed()
        bad_cases=[
            (body+b" ",header,SECRET,NOW),
            (body,header,"whsec_wrongsecret",NOW),
            (body,header,SECRET,NOW+301),
            (body,header,SECRET,NOW-301),
            (body,header.replace("v1=","v0="),SECRET,NOW),
            (body,"t=x,v1=nothex",SECRET,NOW),
            (body,"t="+str(NOW)+",t="+str(NOW)+",v1=bad",SECRET,NOW),
            (b"",header,SECRET,NOW),
            ("not-bytes",header,SECRET,NOW),
        ]
        for i,(data,sig,secret,now) in enumerate(bad_cases):
            with self.subTest(i=i),self.assertRaises(WebhookRejected):
                verify_test_webhook(data,sig,secret,now=now)

    def test_reject_validly_signed_live_events_and_invalid_ids(self):
        for changed in [
            {"livemode":True},
            {"livemode":"false"},
            {"livemode":None},
            {"id":"other_1234"},
            {"id":""},
            {"object":"checkout.session"},
            {"type":"hello world"},
            {"created":True},
            {"created":"now"},
        ]:
            with self.subTest(changed=changed),self.assertRaises(WebhookRejected):
                body,header=signed({**BASE,**changed})
                verify_test_webhook(body,header,SECRET,now=NOW)

    def test_accept_clock_tolerance_boundary_and_multiple_signatures(self):
        body,header=signed()
        self.assertEqual(verify_test_webhook(body,header,SECRET,now=NOW+300).event_id,"evt_demo1234")
        self.assertEqual(verify_test_webhook(body,header+",v1="+"0"*64,SECRET,now=NOW).event_id,"evt_demo1234")
        with self.assertRaises(WebhookRejected):
            verify_test_webhook(body,header,SECRET,now=NOW,tolerance=3600)

    def test_reject_30_hostile_signed_payloads(self):
        for i in range(30):
            with self.subTest(i=i), self.assertRaises(WebhookRejected):
                altered=dict(BASE)
                if i%5==0:
                    altered["id"]="not_evt_"+str(i)
                elif i%5==1:
                    altered["type"]="invalid space "+str(i)
                elif i%5==2:
                    altered["livemode"]=True
                elif i%5==3:
                    altered["object"]="other"
                else:
                    altered["created"]=-i-1
                body,header=signed(altered)
                verify_test_webhook(body,header,SECRET,now=NOW)

if __name__ == "__main__":
    unittest.main()
