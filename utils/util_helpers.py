import argparse
import os
import sys

def default_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--code",
        default=os.getcwd(),
        dest="coderoot",
        help="Path to the location of the priyom package."
    )

    return parser

def setup_env(args):
    import sys
    sys.path.insert(0, args.coderoot)

    import priyom.config
