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
