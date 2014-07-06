import abc
import copy
import functools
import operator

import teapot.routing.selectors
import teapot.forms
import teapot.html

from datetime import datetime, timedelta

__all__ = [
    "dbview",
    "subquery"]

datetime_formats = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%MZ",
    "%Y-%m-%dT%H:%M",
]

operators = {
    "endswith": "ends with",
    "startswith": "starts with",
    "like": "is like",
    "contains": "contains",
    "notlike": "is not like",
    "notin_": "not in",
    "in_": "in",
    "__le__": "≤",
    "__lt__": "<",
    "__eq__": "=",
    "__ne__": "≠",
    "__ge__": "≥",
    "__gt__": ">"
}

order_operators = {
    "__le__", "__lt__", "__eq__", "__ne__", "__ge__", "__gt__"}

type_mapping = {
    datetime: (
        lambda **kwargs: teapot.html.DateTimeField(
            teapot.html.DateTimeMode.Full,
            "datetime",
            **kwargs),
        order_operators),
    int: (
        lambda **kwargs: teapot.html.IntField(**kwargs),
        order_operators),
    str: (
        lambda **kwargs: teapot.html.TextField(**kwargs),
        frozenset(operators) - {"notin_", "in_"}),
    bool: (
        lambda **kwargs: teapot.html.CheckboxField(**kwargs),
        {"__eq__", "__ne__"}),
}

def descriptor_for_type(name, python_type, **kwargs):
    try:
        field_constructor, operators = type_mapping[python_type]
    except KeyError:
        raise ValueError("python type {} not mapped; provide an entry in the"
                         " priyom.api.dbview.type_mapping"
                         " dict".format(python_type))

    descriptor = field_constructor(**kwargs)
    return descriptor, operators

def one_of_descriptor(fieldname,
                      valid_values,
                      error=None,
                      default=None):
    if error is None:
        error = "Not a valid value. Use one of {}".format(
            ", ".join(str(value) for value in sorted(valid_values)))

    descriptor = teapot.html.EnumField(
        options=list(valid_values),
        default=default)
    return descriptor

class dynamic_rows(teapot.forms.CustomRows):
    def __init__(self, fieldname_key, fieldclasses):
        super().__init__()
        self._fieldname_key = fieldname_key
        self._fieldclasses = fieldclasses

    def instanciate_row(self, rows, request, subdata):
        try:
            fieldname = subdata[self._fieldname_key][0]
            fieldclass = self._fieldclasses[fieldname]
        except (IndexError, KeyError):
            return None

        rows.append(fieldclass(request=request, post_data=subdata))

class RowBase(teapot.forms.Row):
    pass

class View(teapot.forms.Form):
    def __init__(self, dbsession, dbview, **kwargs):
        super().__init__(**kwargs)

        fields = []
        fieldmap = {}
        joins = [("outerjoin", obj) for obj in dbview._supplemental_objects]
        for fieldname, field, typehint in dbview._fields:
            if isinstance(field, lazy_node):
                subquery = field._evaluate(dbsession).subquery()
                field = getattr(subquery.c, fieldname)
                joins.append(("outerjoin", subquery))
            fields.append(field)
            fieldmap[fieldname] = field

        query = dbsession.query(
            dbview._primary_object,
            *fields)
        for join in joins:
            jointype = join[0]
            args = join[1:]
            query = getattr(query, jointype)(*args)

        for filterrow in getattr(self, dbview._filter_key):
            field = fieldmap[filterrow.f]
            query = query.filter(
                getattr(field, filterrow.o)(filterrow.v))

        total = query.count()
        if dbview._itemsperpage > 0:
            total_pages = (total+(dbview._itemsperpage-1)) // dbview._itemsperpage
        else:
            total_pages = 1

        query = query.order_by(
            getattr(
                fieldmap[getattr(self, dbview._orderfield_key)],
                getattr(self, dbview._orderdir_key))())

        offset = (getattr(self, dbview._pageno_key)-1)*dbview._itemsperpage
        if total < offset:
            offset = (total_pages-1)*dbview._itemsperpage
        if offset < 0:
            offset = 0
        query = query.offset(offset)

        if dbview._itemsperpage > 0:
            length = min(total - offset, dbview._itemsperpage)
            query = query.limit(dbview._itemsperpage)
            setattr(self, dbview._pageno_key, (offset // dbview._itemsperpage)+1)
        else:
            length = total

        self.dbview = dbview

        self.query = query
        self.length = length
        self.offset = offset
        self.total = total
        self.total_pages = total_pages

    def get_pageno(self):
        return getattr(self, self.dbview._pageno_key)

    def get_orderby_dir(self):
        return getattr(self, self.dbview._orderdir_key)

    def get_orderby_field(self):
        return getattr(self, self.dbview._orderfield_key)

    def __len__(self):
        return self.length

    def __iter__(self):
        if self.dbview._provide_primary_object:
            return iter(self.query)
        else:
            return (
                row[1:]
                for row in self.query)

    def at_page(self, new_pageno):
        result = copy.deepcopy(self)
        setattr(result, self.dbview._pageno_key, int(new_pageno))
        return result

    def with_orderby(self, new_fieldname=None, new_direction=None):
        if new_fieldname is None and new_direction is None:
            return self

        result = copy.deepcopy(self)
        if new_fieldname is not None:
            setattr(result, self.dbview._orderfield_key, new_fieldname)
        if new_direction is not None:
            setattr(result, self.dbview._orderdir_key, new_direction)

        return result

    def without_filters(self):
        result = copy.deepcopy(self)
        getattr(result, self.dbview._filter_key).clear()
        return result

class dbview(teapot.routing.selectors.Selector):
    FIELDNAME_KEY = "f"
    OPERATOR_KEY = "o"
    VALUE_KEY = "v"

    def create_class_for_field(self, fieldname, field, type_hint=None):
        value_descriptor, operators = descriptor_for_type(
            self.VALUE_KEY,
            type_hint or field.type.python_type)
        namespace = {
            self.FIELDNAME_KEY: one_of_descriptor(
                self.FIELDNAME_KEY,
                [fieldname],
                error="Field name must match exactly"),
            self.OPERATOR_KEY: one_of_descriptor(
                self.OPERATOR_KEY,
                operators,
                error="Operator not supported for this field",
                default="__eq__"),
            self.VALUE_KEY: value_descriptor
        }

        return teapot.forms.RowMeta(
            "Row_"+fieldname,
            (RowBase,),
            namespace)

    def __init__(self,
                 primary_object,
                 fields,
                 *,
                 destarg="view",
                 supplemental_objects=[],
                 autojoin=True,
                 pageno_key="p",
                 orderfield_key="ob",
                 orderdir_key="d",
                 filter_key="f",
                 viewname="View",
                 itemsperpage=25,
                 default_orderfield=None,
                 default_orderdir="asc",
                 provide_primary_object=False,
                 **kwargs):
        super().__init__(**kwargs)
        self._primary_object = primary_object
        if autojoin and not supplemental_objects:
            supplemental_objects = list(set(
                field.class_
                for field_name, field, type_hint in fields
                if (hasattr(field, "class_") and
                    field.class_ is not primary_object and
                    not isinstance(field.class_, lazy_node))))

        self._supplemental_objects = supplemental_objects
        self._fields = fields

        self._destarg = destarg
        self._pageno_key = pageno_key
        self._orderfield_key = orderfield_key
        self._orderdir_key = orderdir_key
        self._filter_key = filter_key

        filterable_fields = list(filter(
            lambda x: x[2] or (hasattr(x[1], "type") and
                               hasattr(x[1].type, "python_type")),
            fields))
        self._filterable_fields = filterable_fields

        field_names = frozenset(
            field_name
            for field_name, _, _ in filterable_fields)

        fieldclasses = {
            field_name: self.create_class_for_field(
                field_name, field, type_hint)
            for field_name, field, type_hint in filterable_fields}

        namespace = {
            orderfield_key: one_of_descriptor(
                orderfield_key,
                field_names,
                default=default_orderfield),
            orderdir_key: one_of_descriptor(
                orderdir_key,
                {"asc", "desc"},
                default=default_orderdir),
            pageno_key: descriptor_for_type(
                pageno_key,
                int,
                default=1)[0],
            filter_key: dynamic_rows(
                self.FIELDNAME_KEY, fieldclasses),
        }

        self.ViewForm = teapot.forms.Meta(
            viewname,
            (View,),
            namespace)

        self._itemsperpage = itemsperpage
        self._provide_primary_object = provide_primary_object
        self._fieldclasses = fieldclasses

    def select(self, request):
        dbsession = request.original_request.dbsession
        view = self.ViewForm(dbsession,
                             self,
                             request=request.original_request,
                             post_data=request.query_data)


        request.kwargs[self._destarg] = view
        return True

    def unselect(self, request):
        dbsession = request.original_request.dbsession
        try:
            view = request.kwargs.pop(self._destarg)
        except KeyError:
            view = self.ViewForm(dbsession,
                                 self)
        dest = request.query_data

        dest[self._pageno_key] = [str(getattr(view, self._pageno_key))]
        dest[self._orderfield_key] = [str(getattr(view, self._orderfield_key))]
        dest[self._orderdir_key] = [str(getattr(view, self._orderdir_key))]

        for i, row in enumerate(getattr(view, self._filter_key)):
            prefix = "{}[{}].".format(self._filter_key, i)
            dest[prefix+self.FIELDNAME_KEY] = [
                str(getattr(row, self.FIELDNAME_KEY))]
            dest[prefix+self.OPERATOR_KEY] = [
                str(getattr(row, self.OPERATOR_KEY))]
            value = getattr(row, self.VALUE_KEY)
            dest[prefix+self.VALUE_KEY] = [
                getattr(type(row), self.VALUE_KEY).to_field_value(row, "text")
            ]

    def __call__(self, callable):
        result = super().__call__(callable)
        result.dbview = self
        return result

    def new_view(self,
                 dbsession,
                 **simple_filters):
        view = self.ViewForm(dbsession, self)
        filter_rows = getattr(view, self._filter_key)
        for fieldname, value in simple_filters.items():
            try:
                cls = self._fieldclasses[fieldname]
            except KeyError:
                raise ValueError("Field `{}' is not filterable".format(
                    fieldname))

            row = cls()
            setattr(row, self.FIELDNAME_KEY, fieldname)
            setattr(row, self.OPERATOR_KEY, "__eq__")
            setattr(row, self.VALUE_KEY, value)
            filter_rows.append(row)

        return view

class lazy_node:
    def __init__(self, onlazy):
        super().__init__()
        self._onlazy = onlazy

    def _gettarget(self, on):
        if self._onlazy is not None:
            return self._onlazy._evaluate(on)
        else:
            return on

    def __getattr__(self, name):
        if name.startswith("_"):
            return self.__dict__[name]
        return lazy_operator(self, operator.attrgetter(name))

    def __call__(self, *args, **kwargs):
        return lazy_call(self, *args, **kwargs)

class lazy_call(lazy_node):
    def __init__(self, onlazy, *args, **kwargs):
        super().__init__(onlazy)
        self._args = args
        self._kwargs = kwargs

    def _evaluate(self, on):
        return self._gettarget(on)(*self._args, **self._kwargs)

class lazy_operator(lazy_node):
    def __init__(self, onlazy, operator):
        super().__init__(onlazy)
        self._operator = operator

    def _evaluate(self, on):
        return self._operator(self._gettarget(on))

def subquery(*args, **kwargs):
    """
    Support for subqueries in dbviews is implemented using this class. You can
    pass it arbitrary arguments and retrieve arbitrary members, which in turn
    will be callable. Nothing will be evaluated until the query is actually
    created (that is, at routing time).
    """

    return lazy_call(
        lazy_operator(None, operator.attrgetter("query")),
        *args,
        **kwargs)
