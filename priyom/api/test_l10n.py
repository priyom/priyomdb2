import unittest

import teapot.accept

import priyom.api.l10n as l10n

def simple_preflist(s):
    preflist = teapot.accept.LanguagePreferenceList()
    preflist.append_header(s)
    return preflist

class TestTextDB(unittest.TestCase):
    def test_match_preference(self):
        textdb = l10n.TextDB(fallback_locale="en")
        textdb._locales["en", None] = "en"
        textdb._locales["en", "gb"] = "en_GB"
        textdb._locales["en", "us"] = "en_us"
        textdb._locales["de", "de"] = "de_DE"

        self.assertEqual(
            textdb.catalog_by_preference(simple_preflist("de;q=1.0,en;q=0.9")),
            "de_DE")

        self.assertEqual(
            textdb.catalog_by_preference(simple_preflist("de-at;q=1.0,en;q=0.9")),
            "en")
