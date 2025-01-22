import sys
from .pylite import main

if len(sys.argv) < 2:
    db = ":memory:"
else:
    db = sys.argv[1]

main(db)
