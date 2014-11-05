import abc
import re
import sys

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, validates, Session

from .base import Base, TopLevel

GENERATION_CHAR_UPPER_BOUND = 12
GENERATION_GROUP_UPPER_BOUND = 3

def gen_char_amount(nmin, nmax, rng):
    if nmax is None:
        nmax = GENERATION_CHAR_UPPER_BOUND
    return rng.randint(nmin, max(nmin, min(nmax, GENERATION_CHAR_UPPER_BOUND)))

def gen_group_amount(nmin, nmax, rng):
    if nmax is None:
        nmax = GENERATION_GROUP_UPPER_BOUND
    return rng.randint(nmin, max(nmin, min(nmax, GENERATION_GROUP_UPPER_BOUND)))

def gen_alphanumerics(nmin, nmax, rng):
    amount = gen_char_amount(nmin, nmax, rng)
    for i in range(amount):
        value = rng.randint(0, (26+10)-1)
        if value < 10:
            yield chr(ord('0')+value)
        else:
            yield chr(ord('A')+value-10)

def gen_alphabet_characters(nmin, nmax, rng):
    amount = gen_char_amount(nmin, nmax, rng)
    for i in range(amount):
        value = rng.randint(0, 26-1)
        yield chr(ord('A')+value)

def gen_digits(nmin, nmax, rng):
    amount = gen_char_amount(nmin, nmax, rng)
    for i in range(amount):
        value = rng.randint(0, 9)
        yield chr(ord('0')+value)

def gen_nonspaces(nmin, nmax, rng):
    amount = gen_char_amount(nmin, nmax, rng)
    for i in range(amount):
        char = " "
        while char.isspace():
            char = chr(rng.randint(32, 127))
        yield char

def gen_spaces(nmin, nmax, rng):
    if nmax is None:
        nmax = nmin
    amount = gen_char_amount(nmin, max(nmin, min(nmax, 1)), rng)
    return " "*amount

def make_regex_range(nmin, nmax):
    if nmax is None:
        if nmin == 1:
            return "+"
        elif nmin == 0:
            return "*"
    elif nmax == 1:
        if nmin == 0:
            return "?"
        elif nmin == 1:
            return ""
    elif nmin == nmax:
        return "{{{n}}}".format(n=nmin)

    return "{{{nmin},{nmax}}}".format(
        nmin=nmin,
        nmax=nmax if nmax is not None else ""
    )

def regex_range(regex_to_range, nmin, nmax, omit_grouping=False):
    nmin = max(nmin, 0)
    if nmax is not None:
        nmax = max(nmax, 0)

    if nmin == nmax == 0:
        return ""
    elif nmin == nmax == 1:
        return regex_to_range

    if not omit_grouping:
        regex_to_range = "(?:" + regex_to_range + ")"

    return regex_to_range + make_regex_range(nmin, nmax)

class FormatNode(Base):
    TAG_PLAIN = "plain"
    TAG_FLATTENABLE = "flattenable"
    TAG_RSN = "rsn"

    __tablename__ = "format_node"

    id = Column(Integer, primary_key=True)
    type_ = Column(Unicode(4))
    order = Column(Integer, nullable=False)

    parent_id = Column(Integer,
                       ForeignKey(
                           "format_node.id",
                           ondelete="CASCADE",
                           name="format_node_fk_format_node_id"),
                       nullable=True)
    parent = relationship(
        "FormatNode",
        backref=backref("children",
                        order_by=order),
        remote_side=[id])

    __table_args__ = (
        # UniqueConstraint("parent_id", "order"),
        Base.__table_args__
    )

    __mapper_args__ = {
        "polymorphic_identity": "node",
        "polymorphic_on": type_,
        "with_polymorphic": "*"
    }

    def __init__(self, *, order=None, parent=None):
        super().__init__()
        if parent is not None and order is None and parent.children:
            order = parent.children[-1].order + 1
        self.parent = parent
        self.order = order or 0

    @abc.abstractmethod
    def get_outer_regex(self):
        """
        Return a string resembling the minimum regex required to validate and
        parse this format node.
        """

    def _to_parser_expression_parts(self):
        """
        Return an iterable of strings which can be joined together to a parser
        expression, resembling this node and all of its children.

        If anything cannot be represented in a parser expression, a
        :class:`ValueError` is raised
        """
        raise ValueError("{!r} does not support conversion to a parser"
                         " expression".format(
                             self))

    def to_parser_expression(self):
        return "".join(self._to_parser_expression_parts())


    def parse(self, text):
        raise NotImplementedError("Cannot parse this node standalone.")

    def unparse(self, data):
        """
        Unparse a list of parser statements.

        This is the same kind of list as returned by :meth:`parse`.
        """
        raise NotImplementedError("Cannot unparse this node standalone.")

    def generate(self, rng):
        """
        Generate a random string which can be parsed by this format tree.
        """
        raise NotImplementedError("Cannot generate a string for this node.")

class FormatStructure(FormatNode):
    IDENTITY = "srct"

    __tablename__ = "format_structure_node"

    id = Column(Integer,
                ForeignKey(FormatNode.id,
                           ondelete="CASCADE",
                           name="format_structure_fk_format_node_id"),
                primary_key=True)
    joiner_regex = Column(Unicode(255), nullable=True)
    joiner_const = Column(Unicode(255), nullable=True)
    save_to = Column(Unicode(255), nullable=True)
    nmin = Column(Integer, nullable=False)
    nmax = Column(Integer, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": IDENTITY,
        "inherit_condition": id == FormatNode.id,
    }

    def __init__(self, *children,
                 joiner=None, joiner_regex=None,
                 save_to=None,
                 nmin=1, nmax=1, **kwargs):
        super().__init__(**kwargs)
        self.joiner_const = joiner
        self.joiner_regex = joiner_regex or joiner
        self.save_to = save_to
        self.nmin = nmin
        self.nmax = nmax
        self.children.extend(children)

    def __repr__(self):
        return ("<FormatStructure order={} #children={} nmin={} nmax={} "
                "save_to={!r} joiner={!r}/{!r}>".format(
                    self.order,
                    len(self.children),
                    self.nmin,
                    self.nmax,
                    self.save_to,
                    self.joiner_const,
                    self.joiner_regex))

    def _to_parser_expression_parts(self):
        if     (not self.joiner_const and self.save_to and
                not (self.nmin == self.nmax == 1)):
            raise ValueError("{!r} cannot be expressed as parser expression, due"
                             " to combination of group-mode and save_to".format(
                                 self))

        if ((self.joiner_regex and self.joiner_regex != r"\s+") or
            (self.joiner_const and self.joiner_const != " ") or
            (bool(self.joiner_regex) ^ bool(self.joiner_const))):
            raise ValueError("{!r} cannot be expressed as parser expression"
                             ", due to joiner setup.".format(
                                 self))

        if self.joiner_const or self.save_to:
            # so this is a group
            yield "("

        for child in self.children:
            yield from child._to_parser_expression_parts()

        if self.joiner_const or self.save_to:
            yield ")"
            if self.save_to:
                if not self.save_to.isidentifier():
                    raise ValueError("{!r} cannot be expressed as parser"
                                     "expression, due to save_to value".format(
                                         self))
                yield '[->"{}"]'.format(self.save_to)
        yield make_regex_range(self.nmin, self.nmax)


    def _get_compound_outer_child_regex(self):
        return "".join(child.get_outer_regex()
                       for child in self.children)

    def _get_compound_inner_child_regex(self):
        return "".join(
            r"(?P<c{idx}>{regex})".format(
                idx=i,
                regex=child.get_outer_regex())
            for i, child in enumerate(self.children))

    def get_outer_regex(self):
        children_regex = self._get_compound_outer_child_regex()

        if self.nmin == 1 and self.nmax == 1:
            regex = children_regex
        elif not self.joiner_regex:
            # the simple case. we just emit the correct constraint
            regex = regex_range(children_regex,
                                self.nmin,
                                self.nmax)
        else:
            # this is the complex case. we have to take into account joiners
            regex = (regex_range(children_regex + self.joiner_regex,
                                 self.nmin-1,
                                 (self.nmax-1)
                                 if self.nmax is not None
                                 else None) +
                     children_regex)

        return regex

    def _rewrite_child_number(self, statement_generator, number):
        for _, destination, text in statement_generator:
            yield number, destination, text

    def _parse_match(self, match, number):
        # if we are a saving node, we have to emit save statements
        # otherwise, we delegate parsing to the child nodes

        match_text = match.string[match.start():match.end()]

        if self.save_to:
            yield (number, self, match_text)
            return

        if not self.nmin == self.nmax == 1:
            def child_statements(child, group):
                return self._rewrite_child_number(child.parse(group), number)
        else:
            def child_statements(child, group):
                return child.parse(group)

        # as a non-saving node, we have to figure out whether we are the common
        # parent which needs to take ownership of the statements emitted from
        # the children.
        groupdict = match.groupdict()
        for i, child in enumerate(self.children):
            group = groupdict["c"+str(i)]
            yield from child_statements(child, group)

    def parse(self, text):
        compound_inner_re = self._get_compound_inner_child_regex()
        if self.nmin == self.nmax == 1:
            # special case: require a single full match here
            match = re.compile("^"+compound_inner_re+"$").match(text)
            if match is None:
                raise ValueError("Match of a subpattern failed")
            yield from self._parse_match(match, 0)
        else:
            regex = re.compile(compound_inner_re)
            count = 0
            for i, match in enumerate(regex.finditer(text)):
                count += 1
                yield from self._parse_match(match, i)
            if self.nmin > count:
                raise ValueError("Too few repetitions of subpattern detected")
            if self.nmax is not None and self.nmax < count:
                raise ValueError("Too many repetitions of subpattern detected")

    def unparse(self, data, child_number=0):
        items = []
        if self.save_to:
            # expect data addressed to me
            # make sure we don’t consume more than the maximum amount of items
            # (we are not strict about the minimum though)
            while (self.nmax is None or len(items) < self.nmax) and data:
                number, addressee, text = data[0]
                if addressee is not self or child_number != number:
                    break
                data.pop(0)
                items.append(text)
        else:
            # delegate to children
            while (self.nmax is None or len(items) < self.nmax) and data:
                items.append("".join(child.unparse(data, child_number=len(items))
                                     for child in self.children))

        # recompose
        return (self.joiner_const or "").join(items)

    def generate(self, rng):
        amount = gen_group_amount(self.nmin, self.nmax, rng)
        parts = []
        for i in range(amount):
            child_parts = []
            for child in self.children:
                child_parts.append(child.generate(rng))
            parts.append("".join(child_parts))
        return (self.joiner_const or "").join(parts)

    def __eq__(self, other):
        if type(other) != type(self):
            return NotImplemented
        return (self.joiner_regex == other.joiner_regex and
                self.joiner_const == other.joiner_const and
                self.save_to == other.save_to and
                self.nmin == other.nmin and
                self.nmax == other.nmax and
                len(self.children) == len(other.children) and
                all(my_child == other_child
                    for my_child, other_child in zip(self.children,
                                                     other.children)
                ))

    def __ne__(self, other):
        return not (self == other)

class FormatSimpleContent(FormatNode):
    IDENTITY = "sicn"

    KIND_ALPHABET_CHARACTER = "alphabet_character"
    KIND_DIGIT = "digit"
    KIND_ALPHANUMERIC = "alphanumeric"
    KIND_NONSPACE = "nonspace"
    KIND_SPACE = "space"

    KINDS = {
        KIND_ALPHANUMERIC: (r"[\d\w?]", "X", gen_alphanumerics),
        KIND_ALPHABET_CHARACTER: (r"[\w?]", "A", gen_alphabet_characters),
        KIND_DIGIT: (r"[\d?]", "#", gen_digits),
        KIND_NONSPACE: (r"\S", "?", gen_nonspaces),
        KIND_SPACE: (r"\s", " ", gen_spaces),
    }

    __tablename__ = "format_simple_content_node"

    __mapper_args__ = {
        "polymorphic_identity": IDENTITY
    }

    id = Column(Integer,
                ForeignKey(FormatNode.id,
                           ondelete="CASCADE",
                           name="format_structure_node_fk_format_node_id"),
                primary_key=True)
    kind = Column(
        Enum(
            *KINDS,
            name="simple_content_kind"
        ),
        nullable=False)
    nmin = Column(Integer, nullable=False)
    nmax = Column(Integer, nullable=True)

    def __init__(self, kind, *, nmin=1, nmax=None, **kwargs):
        super().__init__(**kwargs)
        if kind not in self.KINDS:
            raise ValueError("Invalid simple content type: {!r}".format(kind))
        self.kind = kind
        self.nmin = nmin
        self.nmax = nmax

    def __repr__(self):
        return ("<FormatSimpleContentNode order={} kind={} "
                "nmin={} nmax={}>".format(
                    self.order,
                    self.kind,
                    self.nmin,
                    self.nmax))

    def _to_parser_expression_parts(self):
        chr = self.KINDS[self.kind][1]

        if self.kind == self.KIND_SPACE:
            if self.nmin != 1 or self.nmax is not None:
                raise ValueError("{!r} cannot be represented as parser"
                                 " expression, due to range".format(self))

            yield chr
        elif self.nmin == self.nmax and self.nmax <= 3:
            yield chr*self.nmax
        else:
            yield chr
            yield make_regex_range(self.nmin, self.nmax)

    def get_outer_regex(self):
        return regex_range(
            self.KINDS[self.kind][0],
            self.nmin,
            self.nmax,
            omit_grouping=True)

    def parse(self, text):
        regex = re.compile("^"+self.get_outer_regex()+"$")
        if not regex.match(text):
            raise ValueError("Match failed at {} with {!r}".format(
                self, text))

        return []

    def unparse(self, data, child_number=0):
        return self.KINDS[self.kind][1] * self.nmin

    def generate(self, rng):
        return "".join(self.KINDS[self.kind][2](self.nmin, self.nmax, rng))

    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented
        return (self.kind == other.kind and
                self.nmin == other.nmin and
                self.nmax == other.nmax)

    def __ne__(self, other):
        return not (self == other)


class Format(TopLevel):
    __tablename__ = "formats"

    id = Column(Integer, primary_key=True)
    display_name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText, nullable=False)

    root_node_id = Column(Integer,
                          ForeignKey(
                              FormatStructure.id,
                              ondelete="RESTRICT",
                              name="formats_fk_format_structure_node_id"),
                          nullable=False)

    root_node = relationship(FormatStructure)

    def __init__(self, display_name, root_node, description=""):
        super().__init__()
        self.display_name = display_name
        self.root_node = root_node
        self.description = description

    def from_format_string(self, format_string):
        from .format_parser import parse_string
        fmt = parse_string(format_string)

    def parse(self, text):
        from .transmission import ContentNode
        for i, row in enumerate(self.root_node.parse(text)):
            (child_number, format_node, text) = row
            yield ContentNode(
                order=i,
                child_number=child_number,
                format_node=format_node,
                segment=text)

    def unparse(self, content_nodes):
        return self.root_node.unparse([
            (node.child_number, node.format_node, node.segment)
            for node in content_nodes])

    def get_has_users(self):
        from .transmission import StructuredContents

        session = Session.object_session(self)
        if not session:
            return False
        if self.id is None:
            return False
        return session.query(StructuredContents.id).filter(
            StructuredContents.format_id == self.id
        ).count() > 0

def dump_format_tree(node, indent="", indent_per_level=4, file=sys.stdout):
    print(indent + repr(node), file=file)
    if hasattr(node, "children"):
        new_indent = indent + " "*indent_per_level
        for child in node.children:
            dump_format_tree(child,
                             indent=new_indent,
                             indent_per_level=indent_per_level,
                             file=file)
