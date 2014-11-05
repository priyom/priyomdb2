from .format_parser_gen import Parser, Lexer, SyntaxError

def parse_string(s):
    l = Lexer(s.encode("ascii"), string=True)
    p = Parser(l)
    return p.Parse()
