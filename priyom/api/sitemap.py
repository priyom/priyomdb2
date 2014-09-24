import ast
import collections
import collections.abc

import lxml.etree as etree
import lxml.builder

import xsltea.processor
import xsltea.exec

from xsltea.namespaces import NamespaceMeta, xhtml_ns, xlink_ns, svg_ns

from . import svgicon

class Node(list):
    @classmethod
    def subnode(cls, parent, *args, **kwargs):
        node = cls(*args, **kwargs)
        parent.append(node)
        return node

    def __init__(self,
                 routable=None, label=None, svgicon=None,
                 aliased_routables=set(),
                 visible_predicate=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.primary_routable = routable
        self._aliased_routables = frozenset(set(aliased_routables) | {routable})
        self._child_routables = set()
        self.label = label
        self.parent = None
        self.svgicon = svgicon
        self._children = []
        self._invalidated_routables = True
        self._visible_predicate = visible_predicate

    @property
    def child_routables(self):
        if self._invalidated_routables:
            self._update_child_routables()
        return self._child_routables

    @property
    def matching_routables(self):
        return self._aliased_routables

    def is_visible(self, request):
        if self._visible_predicate:
            return self._visible_predicate(request)
        return True

    def _update_child_routables(self):
        self._child_routables = set()
        for child in self:
            self._child_routables |= (child.matching_routables |
                                      child.child_routables)
        self._child_routables = frozenset(self._child_routables)

    def __delitem__(self, index):
        del self._children[index]
        self._invalidated_routables = True

    def __setitem__(self, index, obj):
        if isinstance(index, slice):
            obj = list(obj)
        super().__setitem__(index, obj)
        if isinstance(index, slice):
            for item in obj:
                item.parent = self
        else:
            obj.parent = self
        self._invalidated_routables = True

    def append(self, obj):
        super().append(obj)
        obj.parent = self
        if not self._invalidated_routables:
            self._child_routables |= obj.matching_routables

    def insert(self, index, obj):
        super().insert(index, obj)
        obj.parent = self
        if not self._invalidated_routables:
            self._child_routables |= obj.matching_routables

    def pop(self, index=-1):
        obj = super().pop(index)
        self._invalidated_routables = True
        return obj

    def new(self, *args, **kwargs):
        return self.subnode(self, *args, **kwargs)

    def __repr__(self):
        return "<sitemap node: routable={!r}, len(children)={}, label={!r}>".format(
            self.routable,
            len(self),
            self.label)

class SitemapProcessor(xsltea.processor.TemplateProcessor):
    class xmlns(metaclass=NamespaceMeta):
        xmlns = "https://xmlns.zombofant.net/xsltea/sitemap"

    def __init__(self, name, sitemap, sprites_source=None, **kwargs):
        super().__init__(**kwargs)
        self._sitemap = sitemap
        self._name = name
        self._sprites_source = sprites_source
        self.attrhooks = {}
        self.elemhooks = {
            (str(self.xmlns), "insert"): [self.handle_sitemap]
        }

        self._outputfmts = {
            "xhtml": self._xhtml_sitemap
        }

    def _xhtml_nodefun(self, E, context, parent_node, parent_ul):
        request = context.request
        for node in parent_node:
            if not node.is_visible(request):
                continue

            child_active = request.current_routable in node.child_routables
            active = request.current_routable in node.matching_routables

            label_el = E(
                xhtml_ns.strong if active else xhtml_ns.a,
                node.label
            )
            if not active:
                label_el.set("href", context.href(node.primary_routable))

            li = E(xhtml_ns.li, label_el)
            classes = []
            if child_active:
                classes.append("sm-child-active")
            if active:
                classes.append("sm-active")
            if classes:
                li.set("class", " ".join(classes))

            if node.svgicon and self._sprites_source:
                icon = context.makeelement(svg_ns.svg, {}, {
                    None: str(svg_ns),
                    "xlink": str(xlink_ns)
                })
                icon.set("class", "icon")
                icon.set("viewBox", node.svgicon.viewbox())
                etree.SubElement(
                    icon,
                    svg_ns.use,
                    {
                        xlink_ns.href: "{}#{}".format(
                            self._sprites_source,
                            node.svgicon.elementid)
                    })
                icon.tail = label_el.text
                label_el.append(icon)
                label_el.text = None

            parent_ul.append(li)

    def _xhtml_rootfun(self, context):
        E = lxml.builder.ElementMaker(makeelement=context.makeelement)

        yield E(xhtml_ns.h3, E(xhtml_ns.span, self._sitemap.label))
        ul = E(xhtml_ns.ul)
        self._xhtml_nodefun(E, context, self._sitemap, ul)

        yield ul

    def _xhtml_node(self, type_, template, elem, node, offset):
        sourceline = elem.sourceline or 0

        elemcode = [
            ast.Expr(
                ast.YieldFrom(
                    template.ast_store_and_call(
                        self._xhtml_rootfun,
                        [
                            "context"
                        ],
                        sourceline=sourceline).value,
                    lineno=sourceline,
                    col_offset=0),
                lineno=sourceline,
                col_offset=0)
        ]

        return [], elemcode, []

    def _xhtml_sitemap(self, template, elem, context, offset):
        precode, elemcode, postcode = self._xhtml_node("h3", template, elem, self._sitemap, offset)
        return precode, elemcode, postcode

    def handle_sitemap(self, template, elem, context, offset):
        try:
            name = elem.attrib["name"]
            outputfmt = elem.attrib.get("format", "xml")
        except KeyError as err:
            raise ValueError(
                "missing required attribute on tea:sitemap: @tea:{}".format(
                    str(err).split("}", 1)[1]))

        if name != self._name:
            return False

        try:
            fmt_handler = self._outputfmts[outputfmt]
        except KeyError as err:
            raise ValueError("Unknown tea:sitemap output format: {}".format(
                err))

        return fmt_handler(template, elem, context, offset)
