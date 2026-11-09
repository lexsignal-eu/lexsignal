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
    def test_news(self):
        self.assertEqual(update_feeds.classify_signal("EDPB helps kids stay safe online","","EDPB"),("background","general news"))

if __name__=="__main__":
    unittest.main()
