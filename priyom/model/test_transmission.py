# encoding=utf8
from __future__ import absolute_import, print_function, unicode_literals

import unittest
import re
import operator

from . import transmission

FN = transmission.FormatNode
FS = transmission.FormatStructure
FSC = transmission.FormatSimpleContent
CN = transmission.ContentNode

def monolyth_savables():
    codeword = FS(
        FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=1, nmax=None),
        nmin=1,
        nmax=1,
        save_to="codeword"
    )
    numbers = FS(
        FS(
            FSC(FSC.KIND_DIGIT, nmin=2, nmax=2),
            nmin=4,
            nmax=4,
            joiner=" "
        ),
        nmin=1,
        nmax=1,
        save_to="numbers"
    )

    call = FS(
        FSC(
            FSC.KIND_DIGIT,
            nmin=2,
            nmax=2),
        FSC(FSC.KIND_SPACE),
        FSC(
            FSC.KIND_DIGIT,
            nmin=3,
            nmax=3),
        joiner=" ",
        nmin=1,
        nmax=None,
        save_to="call"
    )

    return call, codeword, numbers

def monolyth():
    call, codeword, numbers = monolyth_savables()

    datanode = FS(
        codeword,
        FSC(FSC.KIND_SPACE),
        numbers,
        joiner=" ",
        nmin=1,
        nmax=None
    )

    root = FS(
        call,
        FSC(FSC.KIND_SPACE),
        datanode
    )

    return root, datanode, (call, codeword, numbers)

def redundant_monolyth():
    """
    This is a special version of a monolyth parser, which matches the same
    patterns, but contains some no-op nodes. These are there to confuse the
    algorithm and make sure it still produces the same results even if weird
    people compose parsers :)
    """
    call, codeword, numbers = monolyth_savables()

    datanode = FS(
        FS(
            codeword,
            nmin=1,
            nmax=1
        ),
        FSC(FSC.KIND_SPACE),
        FS(
            numbers,
            nmin=1,
            nmax=1
        ),
        joiner=" ",
        nmin=1,
        nmax=None
    )


    root = FS(
        call,
        FSC(FSC.KIND_SPACE),
        datanode
    )

    return root, datanode, (call, codeword, numbers)

def mkformat(root_node):
    return transmission.Format("foo", root_node)

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
            r"[\d\w?]",
            node.get_outer_regex())

    def test_regex_no_repeat_joiner(self):
        # this should not change a thing without repeat
        node = FS(
            FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1),
            joiner_regex="foo",
            joiner="bar"
        )
        self.assertEqual(
            r"[\d\w?]",
            node.get_outer_regex())

    def test_regex_repeat_no_joiner(self):
        node = FS(
            FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1),
            nmin=0,
            nmax=None
        )
        self.assertEqual(
            r"(?:[\d\w?])*",
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
            r"(?:[\d\w?]foo)*[\d\w?]",
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
            r"(?:[\d\w?]+\s*)*[\d\w?]+",
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

    def test_unparse(self):
        root, _, (call, codeword, numbers) = monolyth()
        fmt = mkformat(root)
        text = "12 123 HONKING 20 07 03 50 ANTELOPE 20 07 03 50"
        self.assertEqual(
            text,
            fmt.unparse(list(fmt.parse(text)))
        )
