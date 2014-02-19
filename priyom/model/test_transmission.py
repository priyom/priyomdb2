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
        self.assertRaises(TypeError, TFN)
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

class TransmissionFormat(unittest.TestCase):
    @staticmethod
    def multikey_format():
        TF, TFN = model.TransmissionFormat, model.TransmissionFormatNode
        foo_node = TFN("foo", duplicity="+", key="foos")
        bar_node = TFN("bar", duplicity="+", key="bars")
        return TF("test",
            TFN(
                foo_node,
                bar_node,
                TFN("baz")
            )
        ), foo_node, bar_node

    @staticmethod
    def mdzhb_format():
        TF, TFN = model.TransmissionFormat, model.TransmissionFormatNode
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
        return TF("test", tree), callwrap, call, messagewrap, codeword, numbers

    def test_parse(self):
        fmt, foo_node, bar_node = self.multikey_format()
        parsed = fmt.parse("foofoobarbarbaz")
        test_list = [
            (item.order, item.format_node, item.segment)
            for item in parsed.nodes
        ]
        reference_list = [
            (0, foo_node, "foo"),
            (1, foo_node, "foo"),
            (2, bar_node, "bar"),
            (3, bar_node, "bar"),
        ]
        for item in parsed.nodes:
            self.assertIs(item.contents, parsed)
        self.assertEqual(test_list, reference_list)
        self.assertIs(parsed.format, fmt)

    def _check_children(self, nodes, reference):
        for (order, format_node, value), child in zip(reference, nodes):
            self.assertEqual(child.order, order)
            self.assertIs(child.format_node, format_node)
            if isinstance(value, str):
                self.assertEqual(value, child.segment)
            else:
                self._check_children(child.children, value)

    def test_parse_mdzhb(self):
        fmt, callwrap, call, messagewrap, codeword, numbers = self.mdzhb_format()
        parsed = fmt.parse("11 111 22 222 33 333 FOOBAR 11 11 11 11 BAZ 22 22 22 22")
        reference = [
            (0, callwrap, [
                (0, call, "11 111")
            ]),
            (1, callwrap, [
                (0, call, "22 222")
            ]),
            (2, callwrap, [
                (0, call, "33 333")
            ]),
            (3, messagewrap, [
                (0, codeword, "FOOBAR"),
                (1, numbers, "11 11 11 11")
            ]),
            (4, messagewrap, [
                (0, codeword, "BAZ"),
                (1, numbers, "22 22 22 22")
            ])
        ]
        self._check_children(
            filter(lambda x: x.parent is None, parsed.nodes),
            reference
        )

    def test_unparse(self):
        fmt, foo_node, bar_node = self.multikey_format()
        s = "foofoobarbarbaz"
        parsed = fmt.parse(s)
        self.assertEqual(parsed.unparse(), s)

    def test_unparse_mdzhb(self):
        fmt, callwrap, call, messagewrap, codeword, numbers = self.mdzhb_format()
        message = "11 111 22 222 33 333 FOOBAR 11 11 11 11 BAZ 22 22 22 22"
        parsed = fmt.parse(message)
        self.assertEqual(parsed.unparse(), message)
