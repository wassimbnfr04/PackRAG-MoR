"""Authenticated JSON resource bounds before recursive canonicalization/parsing."""
from .errors import require

MAX_JSON_DEPTH = 32

def bounded_structure(raw: bytes):
    stack = []
    quoted = escaped = False
    for value in raw:
        if quoted:
            if escaped: escaped = False
            elif value == 92: escaped = True
            elif value == 34: quoted = False
        elif value == 34: quoted = True
        elif value in (123, 91):
            stack.append(value)
            require(len(stack) <= MAX_JSON_DEPTH, "Authenticated JSON exceeds nesting limit")
        elif value in (125, 93):
            require(bool(stack) and stack.pop() == (123 if value == 125 else 91), "Unbalanced authenticated JSON")
    require(not quoted and not stack, "Unterminated authenticated JSON")
