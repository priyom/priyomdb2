import ast

import xsltea.processor

from xsltea.namespaces import NamespaceMeta, xhtml_ns, svg_ns, xlink_ns

class SVGIcon:
    def __init__(self, elementid, x0=0, y0=0, x1=32, y1=32):
        self.elementid = elementid
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = x1

    def viewbox(self):
        return "{} {} {} {}".format(self.x0, self.y0, self.x1, self.y1)

class SVGIconProcessor(xsltea.processor.TemplateProcessor):
    class xmlns(metaclass=NamespaceMeta):
        xmlns = "https://api.priyom.org/xmlns/svgicon"

    def __init__(self, sourceurl, default_viewbox=None, **kwargs):
        super().__init__(**kwargs)

        self.elemhooks = {
            (str(self.xmlns), "embed"): [self.handle_embed],
        }
        self.attrhooks = {}

        self._sourceurl = sourceurl
        self._default_viewbox = default_viewbox

    @classmethod
    def create_svgicon(cls, template, sourceurl, iconid, viewbox, sourceline,
                       varname="svgicon"):
        body = template.ast_makeelement_and_setup(
            svg_ns.svg,
            sourceline,
            attrdict=ast.Dict(
                [
                    ast.Str(
                        "class",
                        lineno=sourceline,
                        col_offset=0),
                    ast.Str(
                        "viewBox",
                        lineno=sourceline,
                        col_offset=0),
                ],
                [
                    ast.Str(
                        "icon",
                        lineno=sourceline,
                        col_offset=0),
                    ast.Str(
                        viewbox,
                        lineno=sourceline,
                        col_offset=0),
                ],
                lineno=sourceline,
                col_offset=0),
            nsdict=ast.Dict(
                [
                    ast.Name(
                        "None",
                        ast.Load(),
                        lineno=sourceline,
                        col_offset=0),
                    ast.Str(
                        "xlink",
                        lineno=sourceline,
                        col_offset=0),
                ],
                [
                    ast.Str(
                        str(svg_ns),
                        lineno=sourceline,
                        col_offset=0),
                    ast.Str(
                        str(xlink_ns),
                        lineno=sourceline,
                        col_offset=0),
                ],
                lineno=sourceline,
                col_offset=0),
            varname=varname)

        body.extend([
            ast.Expr(
                ast.Call(
                    ast.Attribute(
                        ast.Name(
                            "etree",
                            ast.Load(),
                            lineno=sourceline,
                            col_offset=0),
                        "SubElement",
                        ast.Load(),
                        lineno=sourceline,
                        col_offset=0),
                    [
                        ast.Name(
                            varname,
                            ast.Load(),
                            lineno=sourceline,
                            col_offset=0),
                        ast.Str(
                            svg_ns.use,
                            lineno=sourceline,
                            col_offset=0),
                        ast.Dict(
                            [
                                ast.Str(
                                    xlink_ns.href,
                                    lineno=sourceline,
                                    col_offset=0),
                            ],
                            [
                                template.ast_href(
                                    ast.Str(
                                        sourceurl+"#"+iconid,
                                        lineno=sourceline,
                                        col_offset=0),
                                    sourceline),
                            ],
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
        ])

        return body

    def handle_embed(self, template, elem, context, offset):
        sourceline = elem.sourceline or 0

        attrib = elem.attrib

        try:
            if self._default_viewbox is not None:
                viewbox = elem.get("viewBox", self._default_viewbox)
            else:
                viewbox = attrib["viewBox"]
            idref = attrib["idref"]
        except KeyError as err:
            raise template.compilation_error(
                "Missing mandatory attribute @{!s} on svgicon:embed".format(
                    err),
                context,
                sourceline)

        elemcode = self.create_svgicon(
            template,
            self._sourceurl,
            idref,
            viewbox,
            sourceline,
            varname="elem")

        if "class" in attrib:
            elemcode.append(
                template.ast_set_elem_attr(
                    "class",
                    attrib["class"],
                    sourceline))

        elemcode.append(
            template.ast_yield("elem", sourceline))

        elemcode.extend(template.preserve_tail_code(elem, context))

        return [], elemcode, []
