import ast
import copy
import functools

import xsltea.processor
import xsltea.safe

import lxml.etree as etree

from xsltea.namespaces import NamespaceMeta, xhtml_ns

class Context:
    named_columns = None
    pageobj_ast = None
    viewobj_ast = None

class SortableTableProcessor(xsltea.processor.TemplateProcessor):
    class xmlns(metaclass=NamespaceMeta):
        xmlns = "https://xmlns.zombofant.net/xsltea/priyom"

    def __init__(self,
                 safety_level=xsltea.SafetyLevel.conservative,
                 active_column_class=None,
                 order_indicator_class=None,
                 **kwargs):
        super().__init__(**kwargs)

        self._safety_level = safety_level

        self.active_column_class = active_column_class
        self.order_indicator_class = order_indicator_class

        self.attrhooks = {}
        self.elemhooks = {
            (str(self.xmlns), "sortable-table"): [self.handle_sortable_table]
        }

    def _col_handler(self, my_context, template, elem, context, offset):
        precode, elemcode, postcode = template.default_subtree(
            elem, context, offset)

        try:
            name = elem.attrib["name"]
        except KeyError as err:
            return precode, elemcode, postcode

        if self.active_column_class:
            classmod_ast = compile("""\
if _a.order_by[0].name == _b:
    elem.set("class", _c + elem.get("class", ""))""",
                                   context.filename,
                                   "exec",
                                   ast.PyCF_ONLY_AST)
            classmod_ast = xsltea.template.replace_ast_names(classmod_ast, {
                "_a": my_context.pageobj_ast,
                "_b": name,
                "_c": "" if self.active_column_class is None \
                         else (str(self.active_column_class) + " ")
                }).body

            elemcode[-1:-1] = classmod_ast

        return precode, elemcode, postcode

    def _th_handler(self, my_context, template, elem, context, offset):
        if offset not in my_context.named_columns:
            # not instrumented
            return template.default_subtree(elem, context, offset)

        name, _ = my_context.named_columns[offset]

        childfun_name = "children{}".format(offset)
        precode = template.compose_childrenfun(elem, context, childfun_name)
        postcode = []

        attr_precode, attr_elemcode, attrdict, attr_postcode = \
            template.compose_attrdict(elem, context)

        print(name, elem.text)

        elemcode = compile("""\
elem = makeelement(_elem_tag, attrib=_attrdict)
elem.tail = _elem_tail
elem_a = etree.SubElement(elem, _xhtml_a)
if _page.order_by[0].name == _name:
    elem_a.set(
        "href",
        href(_viewobj, page=_page.with_order_by_direction(
            "asc" if _page.order_by[1] == "desc" else "desc")))
    elem_div = etree.SubElement(
        elem_a,
        _xhtml_div,
        attrib={
            "class": _order_indicator_class
        })
    elem_div.tail = _elem_text
    elem_div.text = "▲" if _page.order_by[1] == "asc" else "▼"
else:
    elem_a.text = _elem_text
    elem_a.set(
        "href",
        href(_viewobj, page=_page.with_order_by_field(_name)))
append_children(elem_a, _childfun())
yield elem""",
                           context.filename,
                           "exec",
                           ast.PyCF_ONLY_AST)
        elemcode = xsltea.template.ReplaceAstNames({
            "_elem_tag": elem.tag,
            "_attrdict": attrdict,
            "_elem_tail": elem.tail or "",
            "_page": my_context.pageobj_ast,
            "_name": name,
            "_xhtml_div": xhtml_ns.div,
            "_order_indicator_class": ("" if self.order_indicator_class is None
                                       else str(self.order_indicator_class)),
            "_childfun": ast.Name(childfun_name,
                                  ast.Load(),
                                  lineno=elem.sourceline or 0,
                                  col_offset=0),
            "_xhtml_a": xhtml_ns.a,
            "_elem_text": elem.text or "",
            "_viewobj": my_context.viewobj_ast
        }).visit(elemcode).body

        if precode:
            elemcode[-2:-2] = attr_elemcode
        else:
            elemcode[-2:-1] = attr_elemcode

        precode.extend(attr_precode)
        postcode.extend(attr_postcode)

        return precode, elemcode, postcode

    def handle_sortable_table(self, template, elem, context, offset):
        try:
            pageobj = elem.attrib[self.xmlns.pageobj]
            viewobj = elem.attrib[self.xmlns.viewobj]
        except KeyError as err:
            raise ValueError(
                "Missing required attribute on priyom:sortable-table: "
                "@priyom:{}".format(str(err).split("}", 1)[1]))

        colgroup = elem.findall(xhtml_ns.colgroup)
        if len(colgroup) != 1:
            raise ValueError("priyom:sortable-table requires exactly one colgroup")

        cols = list(colgroup[0].iter(xhtml_ns.col))

        named_columns = {}
        for i, col in enumerate(cols):
            try:
                name = col.attrib["name"]
            except KeyError:
                continue
            named_columns[i] = name, col

        my_context = Context()
        my_context.named_columns = named_columns
        my_context.pageobj_ast = compile(pageobj,
                                         context.filename,
                                         "eval",
                                         ast.PyCF_ONLY_AST).body
        self._safety_level.check_safety(my_context.pageobj_ast)
        my_context.viewobj_ast = compile(viewobj,
                                         context.filename,
                                         "eval",
                                         ast.PyCF_ONLY_AST).body
        self._safety_level.check_safety(my_context.viewobj_ast)

        col_handler = functools.partial(
            self._col_handler,
            my_context)

        th_handler = functools.partial(
            self._th_handler,
            my_context)

        context.elemhooks.setdefault((str(xhtml_ns), "col"), []).insert(
            0, col_handler)
        context.elemhooks.setdefault((str(xhtml_ns), "th"), []).insert(
            0, th_handler)
        try:
            precode, elemcode, postcode = template.default_subtree(
                elem, context, offset)
        finally:
            del context.elemhooks[(str(xhtml_ns), "col")][0]
            del context.elemhooks[(str(xhtml_ns), "th")][0]

        elemcode[0].value.args[0] = ast.Str(
            xhtml_ns.table,
            lineno=elem.sourceline or 0,
            col_offset=0)

        return precode, elemcode, postcode
