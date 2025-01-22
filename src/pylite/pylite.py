import sys

from pylite.core import repl


def main():
    if len(sys.argv) < 2:
        db = ":memory:"
    else:
        db = sys.argv[1]

    repl(db)
