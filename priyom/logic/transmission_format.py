"""
This file deals with the logic needed to manipulate transmission formats. This
includes a serialization suitable to render an HTML table and to perform easy
manipulations without having to care about the peculiarities of a tree
structure.
"""
import collections
import functools
import itertools
import weakref

import priyom.model

import teapot.forms
import teapot.html

class FormatNodeRows(teapot.forms.CustomRows):
    def instanciate_row(self, rows, request, subdata):
        type_identity = subdata["type_"][0]
        try:
            rowcls = {
                priyom.model.FormatStructure.IDENTITY: FormatStructureRow,
                priyom.model.FormatSimpleContent.IDENTITY: FormatSimpleContentRow
            }[type_identity]
        except KeyError:
            raise ValueError("Invald row type: {}", type_identity)
        rows.append(
            rowcls(
                request=request,
                post_data=subdata,
                parent=rows))

class FormatNodeRow(teapot.forms.Row):
    type_ = teapot.html.TextField()

    @classmethod
    def instance_from_object(cls, obj):
        instance = cls()
        instance._init_from_db(obj)
        return instance

    def _init_from_db(self, obj):
        self.type_ = obj.type_

class MinMaxMixin(teapot.forms.Row):
    nmin = teapot.html.IntField(default=1, min=0, max=None,
                                allow_none=False)
    nmax = teapot.html.IntField(default=1, min=0, max=None,
                                allow_none=True)

    def _init_from_db(self, obj):
        super()._init_from_db(obj)
        self.nmin = obj.nmin
        self.nmax = obj.nmax

    def postvalidate(self, request):
        super().postvalidate(request)
        if self.nmax < self.nmin:
            teapot.forms.ValidationError(
                ValueError("nmax must be larger than or equal to nmin"),
                FormatNodeRow.nmax,
                self).register()

class FormatStructureRow(MinMaxMixin, FormatNodeRow):
    joiner_regex = teapot.html.TextField()
    joiner_const = teapot.html.TextField()
    save_to = teapot.html.TextField()
    children = FormatNodeRows()

    def _init_from_db(self, obj):
        rowcls_map = {
            priyom.model.FormatStructure: FormatStructureRow,
            priyom.model.FormatSimpleContent: FormatSimpleContentRow
        }

        super()._init_from_db(obj)
        self.joiner_regex = obj.joiner_regex
        self.joiner_const = obj.joiner_const
        self.save_to = obj.save_to
        for obj_child in obj.children:
            self.children.append(
                rowcls_map[type(obj_child)].instance_from_object(obj_child)
            )


class FormatSimpleContentRow(MinMaxMixin, FormatNodeRow):
    kind = teapot.html.EnumField(
        options=list(priyom.model.FormatSimpleContent.KINDS),
        default=priyom.model.FormatSimpleContent.KIND_ALPHABET_CHARACTER
    )

    def _init_from_db(self, obj):
        super()._init_from_db(obj)
        self.kind = obj.kind


class FormatForm(FormatStructureRow):
    display_name = teapot.html.TextField()
    description = teapot.html.TextField()

    def _init_from_db(self, obj):
        super()._init_from_db(obj.root_node)
        self.display_name = obj.display_name
        self.description = obj.description
