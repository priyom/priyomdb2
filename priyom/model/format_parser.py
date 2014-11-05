from .format_parser_gen import Parser, Lexer

def parse_string(s):
    l = Lexer(s.encode("utf8"), string=True)
    p = Parser(l)
    return p.Parse()
