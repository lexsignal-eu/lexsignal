import unittest
import update_feeds

class TriageTests(unittest.TestCase):
    def test_enforcement(self):
        self.assertEqual(update_feeds.classify_signal("Central Bank takes enforcement action against Coinbase Ireland","","Central Bank of Ireland"),("high","enforcement"))
    def test_firm_warning(self):
        self.assertEqual(update_feeds.classify_signal("Bank Issues Warning on Unauthorised Firm","","Central Bank of Ireland"),("monitor","firm warning"))
    def test_speech(self):
        self.assertEqual(update_feeds.classify_signal("Opening remarks from Governor","","Central Bank of Ireland"),("background","speech"))
    def test_coin(self):
        self.assertEqual(update_feeds.classify_signal("Central Bank launches U2 commemorative coin","","Central Bank of Ireland"),("background","press/news"))
    def test_guidance(self):
        self.assertEqual(update_feeds.classify_signal("EDPB adopts final GDPR guidelines","","EDPB"),("high","guidance"))
    def test_esma_date(self):
        self.assertEqual(update_feeds.extract_esma_date("EU seeks nominations 09 November 2026 ESMA tokenisation"),"2026-11-09")
        self.assertEqual(update_feeds.extract_esma_date("Latest newsletter 29 October 2026"),"2026-10-29")
        self.assertIsNone(update_feeds.extract_esma_date("Latest newsletter without a date"))
    def test_news(self):
        self.assertEqual(update_feeds.classify_signal("EDPB helps kids stay safe online","","EDPB"),("background","general news"))

if __name__=="__main__":
    unittest.main()
