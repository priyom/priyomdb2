import unittest

from . import format_parser, transmission, format_templates

FSC = transmission.FormatSimpleContent
FS = transmission.FormatStructure

class ParserTester(unittest.TestCase):
    def assertParserTreeEqual(self, t1, t2):
        try:
            self.assertEqual(t1, t2)
        except AssertionError:
            print()
            transmission.dump_format_tree(t1)
            transmission.dump_format_tree(t2)
            raise

class TestParser(ParserTester):
    def test_simple_content_digit(self):
        self.assertParserTreeEqual(
            FSC(FSC.KIND_DIGIT, nmin=1, nmax=1),
            format_parser.parse_string("#").children[0]
        )

    def test_simple_content_alphabet_character(self):
        self.assertParserTreeEqual(
            FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=1, nmax=1),
            format_parser.parse_string("A").children[0]
        )

    def test_simple_content_alphanumeric(self):
        self.assertParserTreeEqual(
            FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1),
            format_parser.parse_string("X").children[0]
        )

    def test_simple_content_nonspace(self):
        self.assertParserTreeEqual(
            FSC(FSC.KIND_NONSPACE, nmin=1, nmax=1),
            format_parser.parse_string("?").children[0]
        )

    def test_simple_content_space(self):
        # special case: space always expands to {1,} repeat
        self.assertParserTreeEqual(
            FSC(FSC.KIND_SPACE, nmin=1, nmax=None),
            format_parser.parse_string(" ").children[0]
        )

    def test_simple_content_repeated(self):
        self.assertParserTreeEqual(
            FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=3, nmax=3),
            format_parser.parse_string("AAA").children[0]
        )
        self.assertParserTreeEqual(
            FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=3, nmax=3),
            format_parser.parse_string("A{3}").children[0]
        )

    def test_simple_content_mixed(self):
        self.assertParserTreeEqual(
            FS(
                FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=1, nmax=1),
                FSC(FSC.KIND_NONSPACE, nmin=1, nmax=1),
                FSC(FSC.KIND_DIGIT, nmin=1, nmax=1),
                nmin=1,
                nmax=1,
            ),
            format_parser.parse_string("A?#").children[0]
        )

    def test_root(self):
        self.assertParserTreeEqual(
            FS(nmin=1, nmax=1),
            format_parser.parse_string("")
        )

    def test_group(self):
        self.assertParserTreeEqual(
            FS(
                FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1),
                joiner_regex=r"\s+",
                joiner=" ",
                nmin=1,
                nmax=None
            ),
            format_parser.parse_string("(X)+").children[0]
        )

    def test_multiple_simple_content_with_range(self):
        self.assertParserTreeEqual(
            FS(
                FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=2, nmax=2),
                nmin=1,
                nmax=None,
            ),
            format_parser.parse_string("AA+").children[0]
        )

    def test_complex(self):
        t1 = format_templates.monolyth()[0]
        t2 = format_parser.parse_string("""(## ###)[->"call"]+ ((A+)[->"codeword"] ((##){4})[->"numbers"])+""")
        self.assertParserTreeEqual(t1, t2)

class TestUnparser(unittest.TestCase):
    def test_simple_content_digit(self):
        self.assertEqual(
            "#",
            FS(FSC(FSC.KIND_DIGIT, nmin=1, nmax=1), nmin=1, nmax=1).to_parser_expression()
        )

    def test_simple_content_alphabet_character(self):
        self.assertEqual(
            "A",
            FS(FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=1, nmax=1), nmin=1, nmax=1).to_parser_expression()
        )

    def test_simple_content_alphanumeric(self):
        self.assertEqual(
            "X",
            FS(FSC(FSC.KIND_ALPHANUMERIC, nmin=1, nmax=1), nmin=1, nmax=1).to_parser_expression()
        )

    def test_simple_content_nonspace(self):
        self.assertEqual(
            "?",
            FS(FSC(FSC.KIND_NONSPACE, nmin=1, nmax=1), nmin=1, nmax=1).to_parser_expression()
        )

    def test_simple_content_space(self):
        self.assertEqual(
            " ",
            FS(FSC(FSC.KIND_SPACE, nmin=1, nmax=None), nmin=1, nmax=1).to_parser_expression()
        )

    def test_simple_content_repeated(self):
        self.assertEqual(
            "AA",
            FS(FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=2, nmax=2), nmin=1, nmax=1).to_parser_expression()
        )
        self.assertEqual(
            "AAA",
            FS(FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=3, nmax=3), nmin=1, nmax=1).to_parser_expression()
        )
        self.assertEqual(
            "A{4}",
            FS(FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=4, nmax=4), nmin=1, nmax=1).to_parser_expression()
        )

    def test_complex(self):
        t = format_templates.monolyth()[0]
        self.assertEqual(
            """(## ###)[->"call"]+ ((A+)[->"codeword"] ((##){4})[->"numbers"])+""",
            t.to_parser_expression()
        )
