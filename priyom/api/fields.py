import re

import teapot.forms

import priyom.model

class ObjectRefField(teapot.forms.CustomField):
    def __init__(self, class_, *, allow_none=True, **kwargs):
        super().__init__(**kwargs)
        self._class = class_
        self._allow_none = allow_none

    def get_default(self, instance):
        return None

    def input_validate(self, request, value):
        if not value:
            value = None
        else:
            try:
                value = request.dbsession.get(self._class, int(value))
            except ValueError as err:
                raise ValueError("Must be a valid object reference") from None

        if value is None and not self._allow_none:
            raise ValueError("Must not be empty")

        return value

    def to_field_value(self, instance, value):
        obj = self.__get__(instance, type(instance))
        return obj.id


class FrequencyField(teapot.forms.StaticDefaultField):
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
