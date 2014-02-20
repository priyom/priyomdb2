import binascii
import functools
import hashlib
import unittest

import priyom.model.user

class TestPBKDF2(unittest.TestCase):
    def _test_hmac_testvectors(self, vectors, hashfun):
        pbkdf2 = functools.partial(
            priyom.model.user.pbkdf2,
            hashfun)

        for i, ((P, S, c, dkLen), DK) in enumerate(vectors):
            my_DK = pbkdf2(P, S, c, dkLen)
            self.assertEqual(
                my_DK, DK,
                "Test vector #{} fails".format(i+1))

    def test_HMAC_SHA1_rfc6070_testvectors(self):
        vectors = [
            ((b"password", b"salt", 1, 20),
             binascii.a2b_hex(b"0c60c80f961f0e71f3a9b524af6012062fe037a6")),
            ((b"password", b"salt", 2, 20),
             binascii.a2b_hex(b"ea6c014dc72d6f8ccd1ed92ace1d41f0d8de8957")),
            ((b"password", b"salt", 4096, 20),
             binascii.a2b_hex(b"4b007901b765489abead49d926f721d065a429c1")),
            ((b"passwordPASSWORDpassword",
              b"saltSALTsaltSALTsaltSALTsaltSALTsalt",
              4096,
              25),
             binascii.a2b_hex(b"3d2eec4fe41c849b80c8d83662c0e44a8b291a964cf2f0"
                              b"7038")),
            ((b"pass\0word",
              b"sa\0lt",
              4096,
              16),
             binascii.a2b_hex(b"56fa6aa75548099dcc37d7f03425e0c3")),
        ]

        self._test_hmac_testvectors(vectors, hashlib.sha1)

    def test_HMAC_SHA256_stackoverflow_testvectors(self):
        # these testvectors are taken from
        # <http://stackoverflow.com/a/5136918/1248008>
        vectors = [
            ((b"password", b"salt", 1, 32),
             binascii.a2b_hex(b"120fb6cffcf8b32c43e7225256c4f837a86548c92ccc3"
                              b"5480805987cb70be17b")),
            ((b"password", b"salt", 2, 32),
             binascii.a2b_hex(b"ae4d0c95af6b46d32d0adff928f06dd02a303f8ef3c25"
                              b"1dfd6e2d85a95474c43")),
            ((b"password", b"salt", 4096, 32),
             binascii.a2b_hex(b"c5e478d59288c841aa530db6845c4c8d962893a001ce4"
                              b"e11a4963873aa98134a")),
            ((b"passwordPASSWORDpassword",
              b"saltSALTsaltSALTsaltSALTsaltSALTsalt",
              4096,
              40),
             binascii.a2b_hex(b"348c89dbcbd32b2f32d814b8116e84cf2b17347ebc180"
                              b"0181c4e2a1fb8dd53e1c635518c7dac47e9")),
            ((b"pass\0word",
              b"sa\0lt",
              4096,
              16),
             binascii.a2b_hex(b"89b69d0516f829893c696226650a8687")),
        ]

        self._test_hmac_testvectors(vectors, hashlib.sha256)

class TestPassword(unittest.TestCase):
    def test_construction_and_validation(self):
        p = "TestPassword"
        verifier = priyom.model.user.create_password_verifier(
            p, 32, b"salt", "sha1")

        self.assertTrue(priyom.model.user.verify_password(
            verifier, p))
        self.assertFalse(priyom.model.user.verify_password(
            verifier, "TestPasswordd"))
        self.assertFalse(priyom.model.user.verify_password(
            verifier, "TestPasswor"))
        self.assertFalse(priyom.model.user.verify_password(
            verifier, "foobarbaz"))

    def test_normalization(self):
        p1 = "a\u0308" # ä constructed through combining
        p2 = "ä"
        verifier = priyom.model.user.create_password_verifier(
            p1, 32, b"salt", "sha1")

        self.assertTrue(priyom.model.user.verify_password(
            verifier, p1))
        self.assertTrue(priyom.model.user.verify_password(
            verifier, p2))
        self.assertFalse(priyom.model.user.verify_password(
            verifier, "a"))
