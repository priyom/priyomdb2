import re
import unicodedata

import babel

import pytz

import teapot.html
import teapot.html.fields
import teapot.forms

from xsltea.namespaces import xhtml_ns

import priyom.model

import lxml.etree as etree

def _extract_tz_groups(tz_list):
    groups = {}
    for tz in tz_list:
        try:
            prefix, item = tz.split("/", 1)
        except ValueError:
            continue
        groups.setdefault(prefix, list()).append(tz)

    groups = [
        (key, {pytz.timezone(tzname) for tzname in tznames})
        for key, tznames in groups.items()
    ]
    groups.sort(key=lambda x: x[0] if x[0] != "Etc" else "ZZZZZZZZZ")

    return groups

class ObjectRefField(teapot.forms.CustomField,
                     teapot.html.fields.HTMLField):
    def __init__(self, class_, *,
                 allow_none=True,
                 provide_options=False,
                 **kwargs):
        super().__init__(**kwargs)
        self._class = class_
        self.allow_none = allow_none
        self.provide_options = provide_options

    def get_options(self, instance, context):
        if self.provide_options:
            return (
                (str(obj.id), str(obj))
                for obj in context.request.dbsession.query(self._class)
            )
        else:
            return []

    def get_default(self, instance):
        return None

    def input_validate(self, request, value):
        if not value:
            value = None
        else:
            try:
                value = request.dbsession.query(self._class).get(int(value))
            except ValueError as err:
                yield ValueError("Is not a valid object reference")
                value = None

        if value is None and not self.allow_none:
            yield ValueError("Is a null object")

        return value

    def to_field_value(self, instance, value):
        obj = self.__get__(instance, type(instance))
        if obj is None:
            return str(0)
        return str(obj.id)

    @property
    def field_type(self):
        return "select"

class FrequencyField(teapot.forms.StaticDefaultField,
                     teapot.html.fields.HTMLField):
    FREQUENCY_RE = re.compile(
        r"^([0-9]+(\.[0-9]*)?|[0-9]*\.[0-9]+)\s*(([a-z]?)Hz)?$",
        re.I)

    def __init__(self, *, default=0, **kwargs):
        super().__init__(default=default, **kwargs)

    @property
    def field_type(self):
        return "text"

    def input_validate(self, request, value):
        try:
            value, _, unit, prefix = self.FREQUENCY_RE.match(value).groups()
        except AttributeError:
            yield ValueError("Not a valid frequency. Specify like this: "
                             "10.4 MHz or 1000 Hz or 123.4 kHz")

        try:
            factor = {
                None: 1,
                "k": 1000,
                "m": 1000000,
                "g": 1000000000,
                "t": 1000000000000
            }[prefix.lower() if prefix else None]
        except KeyError:
            yield ValueError("Unknown unit prefix")

        return round(float(value) * factor)

    def to_field_value(self, instance, view_type):
        value = int(self.__get__(instance, type(instance)))

        prefixes = ["k", "M", "G", "T"]

        for exp, prefix in reversed(list(enumerate(prefixes))):
            factor = 10**((exp+1)*3)
            new_value = value // factor
            if new_value * factor == value:
                use_prefix = prefix
                use_value = new_value
                break
        else:
            use_prefix = ""
            use_value = value

        return "{} {}Hz".format(use_value, use_prefix)

class LoginNameField(teapot.html.TextField):
    @staticmethod
    def opaque_error():
        """
        Return an exception which has a mesasge which is opaque with respect to
        the reason why a login name is not valid.
        """

        return ValueError("Login name is malformed, contains invalid "
                          "characters or is already taken")


    def input_validate(self, request, value):
        if not value:
            raise self.opaque_error()

        try:
            prepped = priyom.model.saslprep.saslprep(
                value,
                allow_unassigned=False)
        except ValueError:
            raise self.opaque_error() from None

        if len(prepped) > priyom.model.User.loginname.type.length:
            raise self.opaque_error()

        return value
        yield None

class PasswordVerifyField(teapot.html.fields.PasswordField):
    """
    A field type which can be used for password inputs where a users password
    is validated (as opposed to being set), e.g. in login forms.

    The password is only loosely validated and processed (with SASLprep,
    allowing unassigned characters) before being stored in the field. It may be
    empty.
    """

    def input_validate(self, request, value):
        try:
            value = priyom.model.saslprep.saslprep(
                value,
                allow_unassigned=True)
        except ValueError:
            raise ValueError("Password is malformed or contains invalid"
                             " characters") from None

        return value
        yield None

class PasswordSetField(teapot.html.PasswordField):
    """
    A field type which can be used for password inputs where a users password is
    set (as opposed to being validated), e.g. in sign-up forms.

    The password is validated more strictly and strength criteria are
    applied. SASLprep is run with unassigned characters being prohibited.
    """

    required_unicode_major_classes = {
        "L", "N", "S"
    }
    minimum_password_length = 8
    tradeoff_per_missing_class = 4

    def input_validate(self, request, value):
        try:
            value = priyom.model.saslprep.saslprep(
                value,
                allow_unassigned=False)
        except ValueError:
            yield ValueError("Password is malformed or contains invalid"
                             " characters")

        classes = frozenset(
            unicodedata.category(c)[0]
            for c in value)

        tradeoff = (len(self.required_unicode_major_classes - classes)
                    * self.tradeoff_per_missing_class)

        if len(value) < tradeoff + self.minimum_password_length:
            yield ValueError("Password violates the strength criteria")

        return value

class PasswordConfirmField(teapot.html.PasswordField):
    def __init__(self, primary_field, **kwargs):
        super().__init__(**kwargs)
        self.primary_field = primary_field

    def input_validate(self, request, value):
        value = yield from self.primary_field.input_validate(request, value)
        return value

    def postvalidate(self, instance, request):
        super().postvalidate(instance, request)
        my_value = self.__get__(instance, type(instance))
        primary_value = self.primary_field.__get__(instance, type(instance))
        if my_value != primary_value:
            teapot.forms.ValidationError(
                ValueError("Passwords do not match"),
                self,
                instance).register()

class EmailField(teapot.html.TextField):
    def input_validate(self, request, value):
        if "@" not in value:
            yield ValueError("Email address does not contain @")

        if len(value) > priyom.model.User.email.type.length:
            yield ValueError("Email is too long")

        return value


class TimezoneField(teapot.forms.StaticDefaultField,
                    teapot.html.fields.HTMLField):
    TZ_GROUPS = _extract_tz_groups(pytz.common_timezones)

    def __init__(self, *, default="Etc/UTC", **kwargs):
        super().__init__(default=default, **kwargs)

    def get_html_options(self, instance, context, elem):
        current_value = self.__get__(instance, type(instance))
        for group, tzs in self.TZ_GROUPS:
            optgroup = etree.SubElement(
                elem,
                xhtml_ns.optgroup)
            optgroup.set("label", context.i18n("tzinfo.region:"+group))

            tz_processed = [
                (tz.zone, context.i18n.get_timezone_name(tz.zone, 'full'))
                for tz in tzs
            ]
            tz_processed.sort(key=lambda x: x[1])

            for key, text in tz_processed:
                option = etree.SubElement(
                    optgroup,
                    xhtml_ns.option)
                if key == current_value:
                    option.set("selected", "selected")
                option.set("value", key)
                option.text = text

        optgroup = etree.SubElement(
            elem,
            xhtml_ns.optgroup)
        optgroup.set("label", context.i18n("tzinfo.region:Etc"))
        etczones = ["Etc/UTC"] + [
            "Etc/GMT" + ("{:+d}".format(offset) if offset != 0 else "")
            for offset in range(-14, 13)
        ]
        for key in etczones:
            text = key.split("/", 1)[1]
            option = etree.SubElement(
                optgroup,
                xhtml_ns.option)
            if key == current_value:
                option.set("selected", "selected")
            option.set("value", key)
            option.text = text


    def input_validate(self, request, value):
        if value not in pytz.all_timezones_set:
            yield ValueError("Not a known time zone")
        return value

class LocaleField(teapot.forms.StaticDefaultField,
                  teapot.html.fields.HTMLField):
    VALID_LOCALES = set(babel.localedata.locale_identifiers())

    def __init__(self, *, default="en_GB", **kwargs):
        super().__init__(default=default, **kwargs)

    def get_html_options(self, instance, context, elem):
        current_value = self.__get__(instance, type(instance)).lower()
        textdb = context.i18n.textdb
        for locale in textdb:
            localestr = teapot.accept.format_locale((locale[0], locale[1].upper()))
            option = etree.SubElement(
                elem,
                xhtml_ns.option)
            if localestr.lower() == current_value:
                option.set("selected", "selected")
            option.set("value", localestr)
            localeobj = babel.Locale(*localestr.split("_"))
            option.text = localeobj.get_display_name()

    def input_validate(self, request, value):
        if value not in self.VALID_LOCALES:
            yield ValueError("Not a known locale")
        return value

class GroupsField(teapot.forms.StaticDefaultField,
                  teapot.html.fields.HTMLField):
    def __init__(self, *, default=[], **kwargs):
        super().__init__(default=default, **kwargs)

    @property
    def field_type(self):
        return "select", "multiple"

    def _extract_value(self, values):
        return set(values),

    def get_html_options(self, instance, context, elem):
        current_values = self.__get__(instance, type(instance))
        options = context.request.dbsession.query(
            priyom.model.Group.id,
            priyom.model.Group.name
        ).order_by(
            priyom.model.Group.name.asc()
        )

        for value, name in options:
            selected = value in current_values
            option = etree.SubElement(
                elem,
                xhtml_ns.option)
            if selected:
                option.set("selected", "selected")
            option.set("value", str(value))
            option.text = context.i18n(name, ctxt="group")

    def input_validate(self, request, values):
        valid_groups = set(id
                           for id,
                           in request.dbsession.query(
                               priyom.model.Group.id))

        converted_values = set()
        has_error = False
        for invalue in values:
            try:
                invalue = int(invalue)
            except ValueError as err:
                has_error = True
                continue

            if invalue in valid_groups:
                converted_values.add(invalue)

        if has_error:
            yield ValueError("Invalid group id")

        return converted_values
