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

__all__ = [
    "TransmissionFormatForm",
    "TransmissionFormatRow"]

class TransmissionFormatRow(teapot.forms.Row):
    @classmethod
    def initialize_from_database(cls, txnode):
        instance = cls()
        instance.order = txnode.order
        instance.duplicity = txnode.duplicity
        instance.saved = txnode.saved
        instance.count = txnode.count
        instance.content_match = txnode.content_match
        instance.key = txnode.key
        instance.join = txnode.join
        instance.comment = txnode.comment
        instance.children[:] = (
            TransmissionFormatRow.initialize_from_database(child)
            for child in txnode.children)
        return instance

    order = teapot.html.IntField()
    duplicity = teapot.html.EnumField(
        options=[
            (priyom.model.TransmissionFormatNode.DUPLICITY_ONE, "Exactly one"),
            (priyom.model.TransmissionFormatNode.DUPLICITY_ONE_OR_MORE, "One or more"),
            (priyom.model.TransmissionFormatNode.DUPLICITY_ZERO_OR_MORE, "Zero or more"),
            (priyom.model.TransmissionFormatNode.DUPLICITY_FIXED, "Fixed amount"),
        ],
        default=priyom.model.TransmissionFormatNode.DUPLICITY_ONE)

    saved = teapot.html.CheckboxField()
    count = teapot.html.IntField(min=0)
    content_match = teapot.html.TextField(default=None)
    key = teapot.html.TextField(default=None)
    join = teapot.html.CheckboxField()
    comment = teapot.html.TextField()

    def to_database_object(self):
        obj = priyom.model.TransmissionFormatNode(
            duplicity=self.duplicity,
            count=self.count,
            key=self.key,
            saved=self.saved,
            join=self.join,
            comment=self.comment)
        if self.content_match is not None:
            obj.content_match = self.content_match
        for child in self.children:
            obj.children.append(child.to_database_object())
        return obj

    children = teapot.forms.Rows(None)

class TransmissionFormatForm(TransmissionFormatRow):
    @classmethod
    def initialize_from_database(cls, txformat):
        instance = super(TransmissionFormatForm, cls).initialize_from_database(
            txformat.root_node)
        instance.display_name = txformat.display_name
        instance.description = txformat.description
        return instance

    display_name = teapot.html.TextField()
    description = teapot.html.TextField()

    def to_database_object(self, destination=None):
        tree = super().to_database_object()

        if destination is None:
            destination = priyom.model.TransmissionFormat(
                self.display_name,
                tree,
                description=self.description)
        else:
            destination.display_name = self.display_name
            destination.root_node = tree
            destination.description = self.description
        return destination
