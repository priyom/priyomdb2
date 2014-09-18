import re
import unicodedata

import teapot.html
import teapot.html.fields
import teapot.forms

import priyom.model

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

    def get_options(self, instance, request):
        if self.provide_options:
            return (
                (str(obj.id), str(obj))
                for obj in request.dbsession.query(self._class)
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
        value = self.__get__(instance, type(instance))

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
