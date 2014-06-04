import ast
import functools
import gettext
import os

import babel
import babel.dates

import teapot.accept

import xsltea.template
import xsltea.processor
import xsltea.exec

from xsltea.namespaces import NamespaceMeta

class Catalog:
    def __init__(self, locale, sourcefile):
        super().__init__()
        self.translations = gettext.GNUTranslations(sourcefile)
        self.localestr = "_".join(locale)

    def __call__(self, key):
        return self._(key)

    def _(self, key):
        result = self.translations.gettext(key)
        return result

    def n(self, singular, plural, n):
        return self.translations.ngettext(singular, plural, n)

    def date(self, dt):
        return babel.dates.format_date(dt, locale=self.localestr)

    def datetime(self, dt):
        return babel.dates.format_datetime(dt, locale=self.localestr)

    def time(self, dt):
        return babel.dates.format_time(dt, locale=self.localestr)

    def timedelta(self, deltat):
        return babel.dates.format_timedelta(deltat, locale=self.localestr)

class TextDB:
    def __init__(self, fallback_locale="en"):
        super().__init__()
        self._locales = {}
        self._fallback_locale = teapot.accept.parse_locale(fallback_locale)

    def catalog_for_locale(self, locale):
        try:
            return self.get_catalog(locale)
        except KeyError:
            try:
                return self.get_catalog((locale[0], None))
            except KeyError:
                pass

            try:
                return self.get_catalog(self._fallback_locale)
            except KeyError:
                pass

            raise

    def catalog_by_preference(self, preference_list):
        best_locale = preference_list.best_match(
            [
                teapot.accept.LanguagePreference(
                    lang, 1.0,
                    parameters={"sub": variant} if variant else {})
                for lang, variant in self._locales.keys()
            ])

        if not best_locale:
            best_locale = self._fallback_locale
        else:
            best_locale = best_locale.value, best_locale.parameters.get("sub")
        return self.get_catalog(best_locale)

    def get_catalog(self, locale):
        return self._locales[locale]

    def load_all(self, base_path):
        fallback_locale = os.path.join(
            base_path,
            "_".join(self._fallback_locale)+".mo")

        with open(fallback_locale, "rb") as f:
            self.load_catalog(self._fallback_locale, f)

        for filename in os.listdir(base_path):
            if not filename.endswith(".mo"):
                continue
            locale, _ = os.path.splitext(filename)
            locale = teapot.accept.parse_locale(locale)
            if locale == self._fallback_locale:
                continue
            with open(os.path.join(base_path, filename), "rb") as f:
                self.load_catalog(locale, f)

    def load_catalog(self, for_locale, sourcefile):
        for_locale = teapot.accept.parse_locale(for_locale)

        if for_locale in self._locales:
            raise ValueError("Locale {} already loaded".format(
                "_".join(for_locale)))

        catalog = Catalog(for_locale, sourcefile)
        self._locales[for_locale] = catalog


class L10NProcessor(xsltea.processor.TemplateProcessor):
    class xmlns(metaclass=NamespaceMeta):
        xmlns = "https://xmlns.zombofant.net/xsltea/l10n"

    def __init__(self, textdb,
                 safety_level=xsltea.safe.SafetyLevel.conservative,
                 varname="l10n",
                 **kwargs):
        super().__init__(**kwargs)

        self.attrhooks = {
            (str(self.xmlns), "text"): [self.handle_attr],
        }
        self.elemhooks = {
            (str(self.xmlns), "_"): [self.handle_elem],
            (str(self.xmlns), "date"): [
                functools.partial(
                    self.handle_elem_type,
                    "date")],
            (str(self.xmlns), "datetime"): [
                functools.partial(
                    self.handle_elem_type,
                    "datetime")],
            (str(self.xmlns), "time"): [
                functools.partial(
                    self.handle_elem_type,
                    "time")],
            (str(self.xmlns), "timedelta"): [
                functools.partial(
                    self.handle_elem_type,
                    "timedelta")],
        }
        self.globalhooks = [self.provide_vars]

        self._textdb = textdb
        self._varname = varname
        self._safety_level = safety_level

    def _access_var(self, template, ctx, sourceline):
        return template.ast_get_from_object(
            self._varname,
            "context",
            sourceline,
            ctx=ctx)

    def _lookup_type(self, template, key, type_, sourceline, attrs={}):
        lookup_key = template.ast_or_str(key, sourceline)

        attrs_dict = ast.Dict([], [], lineno=sourceline, col_offset=0)
        for key, value in attrs.items():
            attrs_dict.keys.append(
                ast.Str(
                    key,
                    lineno=sourceline,
                    col_offset=0))
            attrs_dict.values.append(value)

        lookup_result = ast.Call(
            ast.Attribute(
                self._access_var(template, ast.Load(), sourceline),
                type_,
                ast.Load(),
                lineno=sourceline,
                col_offset=0),
            [
                lookup_key
            ],
            [],
            None,
            None,
            lineno=sourceline,
            col_offset=0)

        if not attrs:
            return lookup_result

        return ast.Call(
            ast.Attribute(
                lookup_result,
                "format",
                ast.Load(),
                lineno=sourceline,
                col_offset=0),
            [],
            [],
            None,
            attrs_dict,
            lineno=sourceline,
            col_offset=0)

    def handle_attr(self, template, elem, key, value, context):
        sourceline = elem.sourceline or 0

        keycode = ast.Str(
            key,
            lineno=sourceline,
            col_offset=0)

        valuecode = self._lookup_type(template, value, "_", sourceline)

        return [], [], keycode, valuecode, []

    def handle_elem(self, template, elem, context, offset):
        sourceline = elem.sourceline or 0

        attrs = {}
        for key, value in elem.attrib.items():
            ns, name = xsltea.template.split_tag(key)
            if ns == str(xsltea.exec.ExecProcessor.xmlns):
                expr = compile(value,
                               context.filename,
                               "eval",
                               ast.PyCF_ONLY_AST).body
                self._safety_level.check_safety(expr)
                attrs[name] = expr
            elif ns is None:
                attrs[name] = ast.Str(
                    value,
                    lineno=sourceline,
                    col_offset=0)
            else:
                raise template.compilation_error(
                    "Unexpected attribute on l10n:text: {} "
                    "(in namespace {})".format(
                        name, ns),
                    context,
                    sourceline)

        elemcode = [
            template.ast_yield(
                self._lookup_type(template, elem.text, "_", sourceline, attrs),
                sourceline)
        ]
        elemcode.extend(template.preserve_tail_code(elem, context))

        return [], elemcode, []

    def handle_elem_type(self, type_, template, elem, context, offset):
        sourceline = elem.sourceline or 0

        key_code = compile(
            elem.text,
            context.filename,
            "eval",
            ast.PyCF_ONLY_AST).body
        self._safety_level.check_safety(key_code)

        elemcode = template.preserve_tail_code(elem, context)
        elemcode.insert(
            0,
            template.ast_yield(
                self._lookup_type(template, key_code, type_, sourceline),
                sourceline)
        )

        return [], elemcode, []

    def provide_vars(self, template, tree, context):
        textdb_key = template.store(self._textdb)
        precode = [
            ast.Assign(
                [
                    ast.Attribute(
                        ast.Name(
                            "context",
                            ast.Load(),
                            lineno=0,
                            col_offset=0),
                        self._varname,
                        ast.Store(),
                        lineno=0,
                        col_offset=0),
                ],
                ast.Call(
                    ast.Attribute(
                        template.ast_get_stored(
                            textdb_key,
                            0),
                        "catalog_by_preference",
                        ast.Load(),
                        lineno=0,
                        col_offset=0),
                    [
                        ast.Attribute(
                            template.ast_get_request(0),
                            "accept_language",
                            ast.Load(),
                            lineno=0,
                            col_offset=0)
                    ],
                    [],
                    None,
                    None,
                    lineno=0,
                    col_offset=0),
                lineno=0,
                col_offset=0)
        ]

        return precode, []
