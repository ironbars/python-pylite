import sys

from pylite.pylite import main

if __name__ == "__main__":
    if len(sys.argv) < 2:
        db = ":memory:"
    else:
        db = sys.argv[1]

    main(db)
