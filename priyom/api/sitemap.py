import ast
import collections
import collections.abc

import lxml.etree as etree

import xsltea.processor
import xsltea.exec

from xsltea.namespaces import NamespaceMeta, xhtml_ns, xlink_ns, svg_ns

from . import svgicon

class Node(collections.abc.MutableSequence):
    @classmethod
    def subnode(cls, parent, *args, **kwargs):
        node = cls(*args, **kwargs)
        parent.append(node)
        return node

    def __init__(self, routable=None, label=None, svgicon=None, **kwargs):
        super().__init__(**kwargs)
        self.routable = routable
        self.label = label
        self.parent = None
        self.svgicon = svgicon
        self._children = []

    def _release_child(self, obj):
        obj.parent = None

    def _release_children(self, sequence):
        collections.deque(0, map(self._release_child, sequence))

    def _validate_and_acquire_child(self, obj):
        if obj.parent is not None:
            raise ValueError("{} is already bound to parent {}".format(
                obj, obj.parent))
        obj.parent = self

    def _validate_and_acquire_children(self, sequence):
        collections.deque(0, map(self._validate_and_acquire_child, sequence))

    def __delitem__(self, index):
        if isinstance(index, slice):
            self._release_children(self._children[index])
        else:
            self._release_child(self._children[index])
        try:
            del self._children[index]
        except:
            if isinstance(index, slice):
                self._validate_and_acquire_children(self._children[index])
            else:
                self._validate_and_acquire_child(self._children[index])

    def __getitem__(self, index):
        return self._children[index]

    def __iter__(self):
        return iter(self._children)

    def __len__(self):
        return len(self._children)

    def __reversed__(self):
        return iter(reversed(self._children))

    def __setitem__(self, index, obj):
        if isinstance(index, slice):
            obj = list(obj)  # we must evaluate it here once
            self._validate_and_acquire_children(obj)
        else:
            self._validate_and_acquire_child(obj)
        try:
            self._children[index] = obj
        except:
            if isinstance(index, slice):
                self._release_children(obj)
            else:
                self._release_child(obj)

    def append(self, obj):
        self._validate_and_acquire_child(obj)
        try:
            self._children.append(obj)
        except:
            self._release_child(obj)
            raise

    def insert(self, index, obj):
        self._validate_and_acquire_child(obj)
        try:
            self._children.insert(index, obj)
        except:
            self._release_child(obj)
            raise

    def reverse(self):
        self._children.reverse()

    def pop(self, index=-1):
        obj = self._children.pop(index)
        self._release_child(obj)
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
            "xml": self._xml_sitemap,
            "xhtml": self._xhtml_sitemap
        }

    def _xhtml_elemcode(self, template, elem, node):
        sourceline = elem.sourceline or 0

        body = template.ast_makeelement_and_setup(
            xhtml_ns.span,
            sourceline,
            varname="textcont")

        if node.routable:
            routable_key = template.store(node.routable)

            body.append(
                ast.If(
                    ast.Compare(
                        ast.Attribute(
                            template.ast_get_request(sourceline),
                            "current_routable",
                            ast.Load(),
                            lineno=sourceline,
                            col_offset=0),
                        [
                            ast.Eq()
                        ],
                        [
                            template.ast_get_stored(
                                routable_key,
                                sourceline)
                        ],
                        lineno=sourceline,
                        col_offset=0),
                    [
                        # set the class of the surrounding element
                        template.ast_set_elem_attr(
                            "class",
                            ast.Str(
                                "active",
                                lineno=sourceline,
                                col_offset=0),
                            sourceline),
                        # convert the text container to <strong />
                        ast.Assign(
                            [
                                ast.Attribute(
                                    ast.Name(
                                        "textcont",
                                        ast.Load(),
                                        lineno=sourceline,
                                        col_offset=0),
                                    "tag",
                                    ast.Store(),
                                    lineno=sourceline,
                                    col_offset=0),
                            ],
                            ast.Str(
                                xhtml_ns.strong,
                                lineno=sourceline,
                                col_offset=0),
                            lineno=sourceline,
                            col_offset=0),
                    ],
                    [
                        # convert the text container to <a />
                        ast.Assign(
                            [
                                ast.Attribute(
                                    ast.Name(
                                        "textcont",
                                        ast.Load(),
                                        lineno=sourceline,
                                        col_offset=0),
                                    "tag",
                                    ast.Store(),
                                    lineno=sourceline,
                                    col_offset=0),
                            ],
                            ast.Str(
                                xhtml_ns.a,
                                lineno=sourceline,
                                col_offset=0),
                            lineno=sourceline,
                            col_offset=0),
                        # set the link href
                        template.ast_set_elem_attr(
                            "href",
                            template.ast_href(
                                template.ast_get_stored(
                                    routable_key,
                                    sourceline),
                                sourceline),
                            sourceline,
                            varname="textcont"),
                    ],
                    lineno=sourceline,
                    col_offset=0))

        body.append(
            ast.Expr(
                ast.Call(
                    ast.Attribute(
                        ast.Name(
                            "elem",
                            ast.Load(),
                            lineno=sourceline,
                            col_offset=0),
                        "append",
                        ast.Load(),
                        lineno=sourceline,
                        col_offset=0),
                    [
                        ast.Name(
                            "textcont",
                            ast.Load(),
                            lineno=sourceline,
                            col_offset=0)
                    ],
                    [],
                    None,
                    None,
                    lineno=sourceline,
                    col_offset=0),
                lineno=sourceline,
                col_offset=0))

        if node.svgicon and self._sprites_source:
            body.extend(
                svgicon.SVGIconProcessor.create_svgicon(
                    template,
                    self._sprites_source,
                    node.svgicon.elementid,
                    node.svgicon.viewbox(),
                    sourceline,
                    varname="svgicon"))

            body.append(
                ast.Expr(
                    ast.Call(
                        ast.Attribute(
                            ast.Name(
                                "textcont",
                                ast.Load(),
                                lineno=sourceline,
                                col_offset=0),
                            "insert",
                            ast.Load(),
                            lineno=sourceline,
                            col_offset=0),
                        [
                            ast.Num(
                                0,
                                lineno=sourceline,
                                col_offset=0),
                            ast.Name(
                                "svgicon",
                                ast.Load(),
                                lineno=sourceline,
                                col_offset=0),
                        ],
                        [],
                        None,
                        None,
                        lineno=sourceline,
                        col_offset=0),
                    lineno=sourceline,
                    col_offset=0))

        if node.label:
            body.append(
                ast.Assign(
                    [
                        ast.Attribute(
                            ast.Name(
                                "svgicon" if node.svgicon else "textcont",
                                ast.Load(),
                                lineno=sourceline,
                                col_offset=0),
                            "tail" if node.svgicon else "text",
                            ast.Store(),
                            lineno=sourceline,
                            col_offset=0),
                    ],
                    ast.Str(
                        node.label,
                        lineno=sourceline,
                        col_offset=0),
                    lineno=sourceline,
                    col_offset=0))

        return body

    def _xhtml_childfun(self, template, elem, node, name):
        precode, elemcode, postcode = [], [], []

        for i, child in enumerate(node):
            child_precode, child_elemcode, child_postcode = \
                self._xhtml_node("li", template, elem, child, i)

            precode.extend(child_precode)
            elemcode.extend(child_elemcode)
            postcode[:0] = child_postcode

        body = precode + elemcode + postcode

        if not body:
            return []

        childfun = ast.FunctionDef(
            name,
            ast.arguments(
                [], None, None, [], None, None, [], [],
                lineno=elem.sourceline or 0,
                col_offset=0),
            body,
            [],
            None,
            lineno=elem.sourceline or 0,
            col_offset=0)

        return [childfun]

    def _xhtml_childrencode(self, template, elem, node, offset):
        sourceline = elem.sourceline or 0
        if not precode:
            return [], []

        elemcode = [
            ast.Expr(
                ast.Call(
                    ast.Name(
                        "append_children",
                        ast.Load(),
                        lineno=sourceline,
                        col_offset=0),
                    [
                        ast.Name(
                            "elem",
                            ast.Load(),
                            lineno=sourceline,
                            col_offset=0),
                        ast.Call(
                            ast.Name(
                                childfun_name,
                                ast.Load(),
                                lineno=sourceline,
                                col_offset=0),
                            [],
                            [],
                            None,
                            None,
                            lineno=sourceline,
                            col_offset=0),
                    ],
                    [],
                    None,
                    None,
                    lineno=sourceline,
                    col_offset=0),
                lineno=sourceline,
                col_offset=0),
        ]

        return precode, elemcode

    def _xhtml_node(self, type_, template, elem, node, offset):
        sourceline = elem.sourceline or 0

        precode = []

        elemcode = template.ast_makeelement_and_setup(
            getattr(xhtml_ns, type_),
            sourceline)
        elemcode.extend(self._xhtml_elemcode(template, elem, node))

        elemcode.append(
            template.ast_yield(
                "elem",
                sourceline))

        childfun_name = "children{}".format(offset)

        child_precode = self._xhtml_childfun(
            template, elem, node, childfun_name)

        if child_precode:
            elemcode.extend(
                template.ast_makeelement_and_setup(
                    xhtml_ns.ul,
                    sourceline,
                    childfun=childfun_name))

            elemcode.append(
                template.ast_yield(
                    "elem",
                    sourceline))

            precode.extend(child_precode)

        return precode, elemcode, []

    def _build_xml_sitemap(self, template, elem, node):
        if node.label:
            elem.set("label", node.label)
        if node.routable:
            routable_name = template.store(node.routable)
            elem.set(xsltea.exec.ExecProcessor.xmlns.href,
                     "href(context.storage[{!r}])".format(routable_name))
            elem.set(xsltea.exec.ExecProcessor.xmlns.active,
                     "'' if request.current_routable == context.storage[{!r}] "
                     "else None".format(routable_name))
        for child in node:
            childelem = etree.SubElement(elem, self.xmlns.entry)
            self._build_xml_sitemap(template, childelem, child)

    def _xml_sitemap(self, template, elem, context, offset):
        root = etree.Element(self.xmlns.entry)
        self._build_xml_sitemap(template, root, self._sitemap)
        return template.default_subtree(root, context, offset)

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
