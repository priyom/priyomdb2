"""
This module contains some format templates, mainly used for testing.
"""

from . import transmission

FN = transmission.FormatNode
FS = transmission.FormatStructure
FSC = transmission.FormatSimpleContent
CN = transmission.ContentNode

def monolyth_savables():
    codeword = FS(
        FSC(FSC.KIND_ALPHABET_CHARACTER, nmin=1, nmax=None),
        nmin=1,
        nmax=1,
        save_to="codeword"
    )
    numbers = FS(
        FS(
            FSC(FSC.KIND_DIGIT, nmin=2, nmax=2),
            nmin=4,
            nmax=4,
            joiner=" "
        ),
        nmin=1,
        nmax=1,
        save_to="numbers"
    )

    call = FS(
        FSC(
            FSC.KIND_DIGIT,
            nmin=2,
            nmax=2),
        FSC(FSC.KIND_SPACE),
        FSC(
            FSC.KIND_DIGIT,
            nmin=3,
            nmax=3),
        joiner=" ",
        nmin=1,
        nmax=None,
        save_to="call"
    )

    return call, codeword, numbers

def monolyth():
    call, codeword, numbers = monolyth_savables()

    datanode = FS(
        codeword,
        FSC(FSC.KIND_SPACE),
        numbers,
        joiner=" ",
        nmin=1,
        nmax=None
    )

    root = FS(
        call,
        FSC(FSC.KIND_SPACE),
        datanode
    )

    return root, datanode, (call, codeword, numbers)

def redundant_monolyth():
    """
    This is a special version of a monolyth parser, which matches the same
    patterns, but contains some no-op nodes. These are there to confuse the
    algorithm and make sure it still produces the same results even if weird
    people compose parsers :)
    """
    call, codeword, numbers = monolyth_savables()

    datanode = FS(
        FS(
            codeword,
            nmin=1,
            nmax=1
        ),
        FSC(FSC.KIND_SPACE),
        FS(
            numbers,
            nmin=1,
            nmax=1
        ),
        joiner=" ",
        nmin=1,
        nmax=None
    )


    root = FS(
        call,
        FSC(FSC.KIND_SPACE),
        datanode
    )

    return root, datanode, (call, codeword, numbers)

def mkformat(root_node):
    return transmission.Format("foo", root_node)
