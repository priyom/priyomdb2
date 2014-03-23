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

    @teapot.forms.field
    def order(self, value):
        if not value:
            return None
        return int(value)

    @order.default
    def order(self):
        return 0

    @teapot.forms.field
    def duplicity(self, value):
        if value not in priyom.model.TransmissionFormatNode.DUPLICITY_TEMPLATES:
            raise ValueError("Invalid duplicity: {!s}".format(value))
        return value

    @teapot.forms.boolfield
    def saved(self, value):
        return bool(value)

    @teapot.forms.field
    def count(self, value):
        if not value:
            return None
        value = int(value)
        if not value:
            return None
        if value < 0:
            raise ValueError("Count must be a non-negative integer")
        return value

    @teapot.forms.field
    def content_match(self, value):
        if not value:
            return None
        return str(value)

    @teapot.forms.field
    def key(self, value):
        if not value:
            return None
        return str(value)

    @teapot.forms.boolfield
    def join(self, value):
        return bool(value)

    @teapot.forms.field
    def comment(self, value):
        if not value:
            return ""
        return str(value)

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

    children = teapot.forms.rows(None)

class TransmissionFormatForm(TransmissionFormatRow):
    @classmethod
    def initialize_from_database(cls, txformat):
        instance = super(TransmissionFormatForm, cls).initialize_from_database(
            txformat.root_node)
        instance.display_name = txformat.display_name
        instance.description = txformat.description
        return instance

    @teapot.forms.field
    def display_name(self, value):
        if not value:
            raise ValueError("Must not be empty")
        return value

    @teapot.forms.field
    def description(self, value):
        if not value:
            return ""
        return value

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
