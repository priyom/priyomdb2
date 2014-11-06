# encoding=utf8
from __future__ import absolute_import, print_function, unicode_literals

import random
import re
import operator
import unittest

from . import transmission, format
from .format_templates import monolyth, mkformat, redundant_monolyth

FN = format.FormatNode
FS = format.FormatStructure
FSC = format.FormatSimpleContent
CN = transmission.ContentNode

class FormatStructureNode(unittest.TestCase):
    def test_defaults(self):
        node = FS()
        self.assertIsNone(node.joiner_const)
        self.assertIsNone(node.joiner_regex)
        self.assertIsNone(node.save_to)
        self.assertEqual(1, node.nmin)
        self.assertEqual(1, node.nmax)

    def test_regex_no_repeat_no_joiner(self):
        node = FS(FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1))
        self.assertEqual(
            r"[\d\w?'-]",
            node.get_outer_regex())

    def test_regex_no_repeat_joiner(self):
        # this should not change a thing without repeat
        node = FS(
            FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1),
            joiner_regex="foo",
            joiner="bar"
        )
        self.assertEqual(
            r"[\d\w?'-]",
            node.get_outer_regex())

    def test_regex_repeat_no_joiner(self):
        node = FS(
            FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1),
            nmin=0,
            nmax=None
        )
        self.assertEqual(
            r"(?:[\d\w?'-])*",
            node.get_outer_regex()
        )

    def test_regex_repeat_joiner(self):
        node = FS(
            FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1),
            nmin=1,
            nmax=None,
            joiner="foo"
        )
        self.assertEqual(
            r"(?:[\d\w?'-]foo)*[\d\w?'-]",
            node.get_outer_regex()
        )

class FormatNode(unittest.TestCase):
    def test_parse_no_repeat_no_joiner(self):
        node = FS(
            FSC(FSC.KIND_ALPHANUMERIC),
            save_to="foo"
        )

        self.assertSequenceEqual(
            [(0, node, "test")],
            list(node.parse("test"))
        )

    def test_parse_repeat_joiner(self):
        node = FS(
            FSC(FSC.KIND_ALPHANUMERIC),
            joiner=" ",
            joiner_regex=r"\s*",
            save_to="foo",
            nmin=1,
            nmax=None,
        )

        self.assertEqual(
            r"(?:[\d\w?'-]+\s*)*[\d\w?'-]+",
            node.get_outer_regex())

        self.assertSequenceEqual(
            [
                (0, node, "test"),
                (1, node, "123"),
                (2, node, "foobar")
            ],
            list(node.parse("test 123 foobar"))
        )

    def test_complex_tree(self):
        root, datanode, (call, codeword, numbers) = monolyth()
        self.assertSequenceEqual(
            [
                (0, call, "12 123"),
                (0, codeword, "HONKING"),
                (0, numbers, "20 07 03 50"),
                (1, codeword, "ANTELOPE"),
                (1, numbers, "20 07 03 50")
            ],
            list(root.parse(
                "12 123 HONKING 20 07 03 50 ANTELOPE 20 07 03 50"
            ))
        )

    def test_redundant_complex_tree(self):
        root, datanode, (call, codeword, numbers) = redundant_monolyth()
        self.assertSequenceEqual(
            [
                (0, call, "12 123"),
                (0, codeword, "пустые"),
                (0, numbers, "20 07 03 49"),
                (1, codeword, "стены"),
                (1, numbers, "20 07 03 49")
            ],
            list(root.parse(
                "12 123 пустые 20 07 03 49 стены 20 07 03 49"
            ))
        )

    def test_parser_failure(self):
        root, datanode, (call, codeword, numbers) = monolyth()
        self.assertRaises(ValueError, list, root.parse("12 123"))
        self.assertRaises(ValueError, list, root.parse("12 123 FOO 12 34 56"))
        self.assertRaises(ValueError, list, root.parse("12 123 FOO 12 34 56 XX"))


    def test_unparse(self):
        root, _, _ = monolyth()
        text = "12 123 HONKING 20 07 03 50 ANTELOPE 20 07 03 50"
        self.assertEqual(
            text,
            root.unparse(list(root.parse(text)))
        )


class Format(unittest.TestCase):
    def test_parse(self):
        root, _, (call, codeword, numbers) = monolyth()
        fmt = mkformat(root)
        self.assertSequenceEqual(
            [
                CN(0, 0, call, "12 123"),
                CN(1, 0, codeword, "HONKING"),
                CN(2, 0, numbers, "20 07 03 50"),
                CN(3, 1, codeword, "ANTELOPE"),
                CN(4, 1, numbers, "20 07 03 50")
            ],
            list(fmt.parse("12 123 HONKING 20 07 03 50 ANTELOPE 20 07 03 50"))
        )

    def test_exact_match(self):
        root, _, (call, codeword, numbers) = monolyth()
        fmt = mkformat(root)
        with self.assertRaises(ValueError):
            list(fmt.parse(
                "foo 12 123 HONKING 20 07 03 50 ANTELOPE 20 07 03 50"
            ))

    def test_unparse(self):
        root, _, (call, codeword, numbers) = monolyth()
        fmt = mkformat(root)
        text = "12 123 HONKING 20 07 03 50 ANTELOPE 20 07 03 50"
        self.assertEqual(
            text,
            fmt.unparse(list(fmt.parse(text)))
        )

class TestGeneration(unittest.TestCase):
    system_random = random.SystemRandom()

    def test_parsability(self):
        root, *_ = monolyth()
        rng = random.Random()
        seed = self.system_random.getrandbits(32)
        rng.seed(seed)
        # this test checks with a certain probability that parsability works
        for i in range(32):
            randstr = root.generate(rng)
            try:
                list(root.parse(randstr))
            except ValueError:
                raise AssertionError(
                    "Generated invalid string: {!r} (initial seed = {})".format(
                        randstr, seed))
