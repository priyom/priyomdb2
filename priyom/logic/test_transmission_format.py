import unittest

import priyom.model

from . import transmission_format

class TestTransmissionFormatEditee(unittest.TestCase):
    def test_construction_from_actual_tree(self):
        TF = priyom.model.TransmissionFormat
        TFN = priyom.model.TransmissionFormatNode

        node21 = TFN("a")
        node22 = TFN("b")
        node23 = TFN("c")

        node2 = TFN(node21, node22, node23, separator=" ")

        node11 = TFN("A")
        node12 = TFN("B")
        node13 = TFN("C")

        node1 = TFN(node11, node12, node13, separator=" ")

        node = TFN(node1, node2, separator=" ")

        fmt = TF("foo", node, "bar")

        editee = transmission_format.TransmissionFormatEditee.from_actual_format(
            fmt)

        self.assertEqual("", editee.id)
        self.assertEqual("foo", editee.display_name)
        self.assertEqual("bar", editee.description)

        node_sequence = [
            node, node1, node11, node12, node13,
                  node2, node21, node22, node23]

        # only compare attributes for which it makes sense
        attributes = [
            (attr, str if attr in {"id"} else lambda x: x)
            for attr in dir(transmission_format.TFN_tuple)
            if not attr.startswith("_") and attr not in {
                    "children",
                    "level",
                    "index"}]

        for attrname, cast in attributes:
            for i, node in enumerate(node_sequence):
                self.assertEqual(
                    cast(getattr(node, attrname)),
                    getattr(editee.byindex[i], attrname))

    def test_construction_from_postdata(self):
        postdata = [
            ("id", ""),
            ("display_name", "fnord"),
            ("description", "funk"),
            ("node[0].id", ""),
            ("node[0].duplicity", "1"),
            ("node[0].count", ""),
            ("node[0].content_match", ""),
            ("node[0].key", ""),
            ("node[0].comment", "Foo"),
            ("node[0].level", 0),
            ("node[1].id", ""),
            ("node[1].duplicity", "+"),
            ("node[1].saved", ),
            ("node[1].count", ""),
            ("node[1].content_match", "a"),
            ("node[1].key", "foo"),
            ("node[1].comment", "Bar"),
            ("node[1].level", 1)
        ]

        postdata = {
            item[0]: list(item[1:])
            for item in postdata}

        editee = transmission_format.TransmissionFormatEditee.from_postdata(
            postdata)

        self.assertEqual(
            None,
            editee.byindex[0].id)
        self.assertEqual(
            "1",
            editee.byindex[0].duplicity)
        self.assertEqual(
            None,
            editee.byindex[0].count)
        self.assertEqual(
            None,
            editee.byindex[0].content_match)
        self.assertEqual(
            None,
            editee.byindex[0].key)
        self.assertEqual(
            "Foo",
            editee.byindex[0].comment)
        self.assertEqual(
            0,
            editee.byindex[0].level)

        self.assertEqual(
            None,
            editee.byindex[1].id)
        self.assertEqual(
            "+",
            editee.byindex[1].duplicity)
        self.assertEqual(
            None,
            editee.byindex[1].count)
        self.assertEqual(
            "a",
            editee.byindex[1].content_match)
        self.assertEqual(
            "foo",
            editee.byindex[1].key)
        self.assertEqual(
            "Bar",
            editee.byindex[1].comment)
        self.assertEqual(
            1,
            editee.byindex[1].level)

    def test_multiple_root_nodes(self):
        postdata = [
            ("id", ""),
            ("display_name", "fnord"),
            ("description", "funk"),
            ("node[0].id", ""),
            ("node[0].duplicity", "1"),
            ("node[0].count", ""),
            ("node[0].content_match", ""),
            ("node[0].key", ""),
            ("node[0].comment", "Foo"),
            ("node[0].level", 0),
            ("node[1].id", ""),
            ("node[1].duplicity", "+"),
            ("node[1].saved", ),
            ("node[1].count", ""),
            ("node[1].content_match", "a"),
            ("node[1].key", "foo"),
            ("node[1].comment", "Bar"),
            ("node[1].level", "0")
        ]

        postdata = {
            item[0]: list(item[1:])
            for item in postdata}

        with self.assertRaises(ValueError):
            editee = transmission_format.TransmissionFormatEditee.from_postdata(
                postdata)

    def test_nesting_without_parents(self):
        postdata = [
            ("id", ""),
            ("display_name", "fnord"),
            ("description", "funk"),
            ("node[0].id", ""),
            ("node[0].duplicity", "1"),
            ("node[0].count", ""),
            ("node[0].content_match", ""),
            ("node[0].key", ""),
            ("node[0].comment", "Foo"),
            ("node[0].level", 0),
            ("node[1].id", ""),
            ("node[1].duplicity", "+"),
            ("node[1].saved", ),
            ("node[1].count", ""),
            ("node[1].content_match", "a"),
            ("node[1].key", "foo"),
            ("node[1].comment", "Bar"),
            ("node[1].level", "2")
        ]

        postdata = {
            item[0]: list(item[1:])
            for item in postdata}

        with self.assertRaises(ValueError):
            editee = transmission_format.TransmissionFormatEditee.from_postdata(
                postdata)

    def test_missing_attribute(self):
        postdata = [
            ("id", ""),
            ("display_name", "fnord"),
            ("description", "funk"),
            ("node[0].id", ""),
            ("node[0].duplicity", "1"),
            ("node[0].count", ""),
            ("node[0].content_match", ""),
            ("node[0].key", ""),
            ("node[0].comment", "Foo"),
            ("node[0].level", 0),
            ("node[1].id", ""),
            ("node[1].duplicity", "+"),
            ("node[1].saved", ),
            ("node[1].count", ""),
            ("node[1].content_match", "a"),
            ("node[1].key", "foo"),
            ("node[1].level", "1")
        ]

        postdata = {
            item[0]: list(item[1:])
            for item in postdata}

        editee = transmission_format.TransmissionFormatEditee.from_postdata(
            postdata)
        # the second one is dropped for incompleteness
        self.assertEqual(len(editee.byindex), 1)
