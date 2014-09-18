try:
    from priyom_config import *
except ImportError:
    import sys
    print("""
You have to supply a priyom_config.py which is importable. For full details see
the docs (which currently still need to be written).

A working example is::

    from priyom.paths import *
    CODEROOT = # ...
    set_paths(paths(CODEROOT))
    database_url = # ...

where you should replace ``# ...`` with strings pointing to the respective
locations. CODEROOT must be the directory which contains the directory
``priyom`` (i.e. which contains the package).""")
    sys.exit(2)
