import unittest

from . import saslprep

class TestSASLprep(unittest.TestCase):
    def test_map_to_nothing_rfcx(self):
        self.assertEqual(
            "IX",
            saslprep.saslprep("I\u00ADX"),
            "SASLprep requirement: map SOFT HYPHEN to nothing")

    def test_identity_rfcx(self):
        self.assertEqual(
            "user",
            saslprep.saslprep("user"),
            "SASLprep requirement: identity transform")

    def test_case_preservation_rfcx(self):
        self.assertEqual(
            "USER",
            saslprep.saslprep("USER"),
            "SASLprep requirement: preserve case")

    def test_nfkc_rfcx(self):
        self.assertEqual(
            "a",
            saslprep.saslprep("\u00AA"),
            "SASLprep requirement: NFKC")
        self.assertEqual(
            "IX",
            saslprep.saslprep("\u2168"),
            "SASLprep requirement: NFKC")

    def test_prohibited_character_rfcx(self):
        with self.assertRaises(
                ValueError,
                msg="SASLprep requirement: prohibited character (C.2.1)") as err:
            saslprep.saslprep("\u0007")

        with self.assertRaises(
                ValueError,
                msg="SASLprep requirement: prohibited character (C.8)") as err:
            saslprep.saslprep("\u200E")

    def test_bidirectional_check_rfcx(self):
        with self.assertRaises(
                ValueError,
                msg="SASLprep requirement: bidirectional check") as err:
            saslprep.saslprep("\u0627\u0031")

    def test_unassigned(self):
        with self.assertRaises(
                ValueError,
                msg="SASLprep requirement: unassigned") as err:
            saslprep.saslprep("\u0221", allow_unassigned=False)

        self.assertEqual(
            "\u0221",
            saslprep.saslprep("\u0221", allow_unassigned=True))
