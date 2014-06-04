"""
SASLprep
########

This module implements the SASLprep (`RFC 4013`_) stringprep profile. It
provides functions to run strings through the stringprep profile and return the
result.

.. autofunction:: prep

.. _RFC 3454: https://tools.ietf.org/html/rfc4013
.. _RFC 4013: https://tools.ietf.org/html/rfc4013

"""

import stringprep
import unicodedata

def is_RandALCat(c):
    return unicodedata.bidirectional(c) in ("R", "AL")

def is_LCat(c):
    return unicodedata.bidirectional(c) == "L"

def check_against_tables(chars, tables):
    """
    Perform a check against the table predicates in *tables*. *tables* must be a
    reusable iterable containing characteristic functions of character sets,
    that is, functions which return :data:`True` if the character is in the
    table.

    The function returns the first character occuring in any of the tables or
    :data:`None` if no character matches.
    """

    for c in chars:
        if any(in_table(c) for in_table in tables):
            return c

    return None

def do_mapping(chars):
    """
    Perform the stringprep mapping step of SASLprep. Operates in-place on a list
    of unicode characters provided in *chars*.
    """
    i = 0
    while i < len(chars):
        c = chars[i]
        if stringprep.in_table_c12(c):
            chars[i] = "\u0020"
        elif stringprep.in_table_b1(c):
            del chars[i]
            continue
        i += 1

def do_normalization(chars):
    """
    Perform the stringprep normalization step of SASLprep. Operates in-place on
    a list of unicode characters provided in *chars*.
    """
    chars[:] = list(unicodedata.normalize("NFKC", "".join(chars)))

def check_prohibited_output(chars):
    """
    Check against prohibited output as per SASLprep. Operates on a list of
    unicode characters provided in *chars*.
    """
    bad_tables = (
        stringprep.in_table_c12,
        stringprep.in_table_c21,
        stringprep.in_table_c22,
        stringprep.in_table_c3,
        stringprep.in_table_c4,
        stringprep.in_table_c5,
        stringprep.in_table_c6,
        stringprep.in_table_c7,
        stringprep.in_table_c8,
        stringprep.in_table_c9)

    violator = check_against_tables(chars, bad_tables)
    if violator is not None:
        raise ValueError("Input contains invalid unicode codepoint: "
                         "U+{}".format(ord(violator)))

def check_bidi(chars):
    """
    Check proper bidirectionality as per SASLprep. Operates on a list of
    unicode characters provided in *chars*.
    """

    # the empty string is valid, as it cannot violate the RandALCat constraints
    if not chars:
        return

    # first_is_RorAL = unicodedata.bidirectional(chars[0]) in {"R", "AL"}
    # if first_is_RorAL:

    has_RandALCat = any(is_RandALCat(c) for c in chars)
    if not has_RandALCat:
        return

    has_LCat = any(is_LCat(c) for c in chars)
    if has_LCat:
        raise ValueError("L and R/AL characters must not occur in the same"
                         " string")

    if not is_RandALCat(chars[0]) or not is_RandALCat(chars[-1]):
        raise ValueError("R/AL string must start and end with R/AL character.")


def check_unassigned(chars):
    """
    Check that *chars* does not contain any unassigned code points as per
    SASLprep. Operates on a list of unicode code points provided in *chars*.
    """
    bad_tables = (
        stringprep.in_table_a1,)

    violator = check_against_tables(chars, bad_tables)
    if violator is not None:
        raise ValueError("Input contains unassigned code point: "
                         "U+{}".format(ord(violator)))


def saslprep(string, allow_unassigned=True):
    """
    Process the given *string* using the SASLprep profile. In the error cases
    defined in `RFC 3454`_ (stringprep), a :class:`ValueError` is raised.
    """

    chars = list(string)
    do_mapping(chars)
    do_normalization(chars)
    check_prohibited_output(chars)
    check_bidi(chars)

    if not allow_unassigned:
        check_unassigned(chars)

    return "".join(chars)
