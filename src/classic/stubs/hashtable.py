"""Stand-in for the `hashtable` module CLASSIC.py imports (not shared on OSF).

CLASSIC uses item get/set, .keys(), and truthiness checks such as `if chunkmatch:` after a lookup.
So a missing key must return a falsy value instead of raising. A dict with __missing__ -> None does that.
The size argument is accepted and ignored.
"""


class HashTable(dict):
    def __init__(self, size=None):
        super().__init__()

    def __missing__(self, key):
        return None
