# encoding=utf8
from __future__ import absolute_import, print_function, unicode_literals

import unittest
import re
import operator

import priyom.model as model

class TransmissionFormatNode(unittest.TestCase):
    def test_init(self):
        TFN = model.TransmissionFormatNode
        child = TFN("fnord")
        root_node = TFN(
            child
        )
        self.assertIs(root_node.children[0], child)
        self.assertEqual(child.order, 0)

    def test_tree_init(self):
        TFN = model.TransmissionFormatNode
        leaf1 = TFN("foo")
        leaf2 = TFN("bar")
        leaf3 = TFN("baz")
        node1 = TFN(leaf1, leaf2)
        node2 = TFN(leaf3)
        root = TFN(node1, node2)
        self.assertEqual(node1.order, 0)
        self.assertEqual(node2.order, 1)
        self.assertEqual(leaf1.order, 0)
        self.assertEqual(leaf2.order, 1)
        self.assertEqual(leaf3.order, 0)
        self.assertSequenceEqual(root.children, [node1, node2])
        self.assertSequenceEqual(node1.children, [leaf1, leaf2])
        self.assertSequenceEqual(node2.children, [leaf3])

    def test_faulty_init(self):
        TFN = model.TransmissionFormatNode
        self.assertRaises(TypeError, TFN, "foo", "bar")
        self.assertRaises(ValueError, TFN, "foo)")  # invalid regex

    def test_regex_leaf(self):
        TFN = model.TransmissionFormatNode
        leaf = TFN("fnord")
        self.assertEqual(leaf.build_regex(), "fnord")

    def test_regex_nested(self):
        TFN = model.TransmissionFormatNode
        tree = TFN(
            TFN(
                TFN("foo"),
                TFN("bar"),
            ),
            TFN("baz")
        )
        self.assertEqual(tree.build_regex(), "foobarbaz")

    def test_regex_nested_complex(self):
        TFN = model.TransmissionFormatNode
        tree = TFN(
            TFN(
                TFN("foo", duplicity="+"),
                TFN("bar", duplicity="{}", count=4),
            ),
            TFN("baz", duplicity="*")
        )
        self.assertEqual(tree.build_regex(), "(foo)+(bar){4}(baz)*")

    def test_regex_keyed(self):
        TFN = model.TransmissionFormatNode
        tree = TFN(
            TFN(
                TFN("foo", duplicity="+"),
                TFN("bar", duplicity="{}", count=4),
                key="foobar"
            ),
            TFN("baz", duplicity="*")
        )
        regex = tree.build_regex()
        self.assertEqual(regex, "(?P<foobar>(foo)+(bar){4})(baz)*")

        regex = re.compile(regex)
        match = regex.search("foofoobarbarbarbarbaz")
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict(), {"foobar": "foofoobarbarbarbar"})

    def test_parse(self):
        TFN = model.TransmissionFormatNode
        call = TFN("[0-9]{2}\s+[0-9]{3}", key="call")
        callwrap = TFN(
            call,
            duplicity="+",
            separator=" ",
            key="callwrap",
            saved=False
        )
        codeword = TFN("\w+", key="codeword")
        numbers = TFN("([0-9]{2} ){3}[0-9]{2}", key="numbers")
        messagewrap = TFN(
            TFN(
                codeword,
                TFN(" "),
                numbers,
            ),
            duplicity="+",
            separator=" ",
            key="messagewrap",
            saved=False
        )
        tree = TFN(
            callwrap,
            TFN(" "),
            messagewrap
        )
        self.assertEqual(
            tree.parse("11 111 22 222 33 333 FOOBAR 11 11 11 11 BAZ 22 22 22 22"),
            {
                "callwrap": (callwrap, [
                    {
                        "call": (call, ["11 111"])
                    },
                    {
                        "call": (call, ["22 222"])
                    },
                    {
                        "call": (call, ["33 333"])
                    }
                ]),
                "messagewrap": (messagewrap, [
                    {
                        "codeword": (codeword, ["FOOBAR"]),
                        "numbers": (numbers, ["11 11 11 11"])
                    },
                    {
                        "codeword": (codeword, ["BAZ"]),
                        "numbers": (numbers, ["22 22 22 22"])
                    }
                ])
            }
        )
