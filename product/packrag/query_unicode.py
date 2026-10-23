"""Frozen Unicode 15 NFKC and default lowercase for query/alias parity."""
import json
from bisect import bisect_right
from pathlib import Path

_DATA = json.loads((Path(__file__).resolve().parents[1] / "config/query-unicode15.json").read_text())
VERSION = _DATA["unicode_version"]
_DECOMP = {int(k): v for k, v in _DATA["decomposition"].items()}
_CCC = {int(k): v for k, v in _DATA["combining"].items()}
_LOWER = {int(k): v for k, v in _DATA["lower"].items()}
_COMPOSE = {int(k): v for k, v in _DATA["composition"].items()}
_RANGES = {name: [x for pair in _DATA[name] for x in pair] for name in ("word", "whitespace", "cased", "case_ignorable")}


def has_property(point, name):
    bounds = _RANGES[name]
    index = bisect_right(bounds, point)
    return index % 2 == 1 or (index > 0 and bounds[index - 1] == point)


def is_word(point):
    return has_property(point, "word")


def word_terms(text):
    terms, current = set(), []
    for char in text:
        if is_word(ord(char)):
            current.append(char)
        elif current:
            terms.add(''.join(current)); current.clear()
    if current:
        terms.add(''.join(current))
    return sorted(terms)


def contains_alias(text, alias):
    if not alias:
        return False
    start = 0
    while (index := text.find(alias, start)) >= 0:
        end = index + len(alias)
        if (index == 0 or not is_word(ord(text[index - 1]))) and (end == len(text) or not is_word(ord(text[end]))):
            return True
        start = index + 1
    return False


def nfkc(text):
    points = []
    for char in text:
        point = ord(char)
        if 0xAC00 <= point <= 0xD7A3:
            index = point - 0xAC00
            expanded = [0x1100 + index // 588, 0x1161 + index % 588 // 28]
            if index % 28:
                expanded.append(0x11A7 + index % 28)
        else:
            expanded = [ord(c) for c in _DECOMP.get(point, char)]
        points.extend(expanded)
    # Stable sorting each combining run also handles leading non-starters.
    ordered, marks = [], []
    for point in points:
        if _CCC.get(point, 0) == 0:
            ordered.extend(sorted(marks, key=lambda p: _CCC[p])); marks.clear()
            ordered.append(point)
        else:
            marks.append(point)
    ordered.extend(sorted(marks, key=lambda p: _CCC[p]))
    result, starter_index, starter, last_ccc = [], -1, -1, 0
    for point in ordered:
        ccc = _CCC.get(point, 0)
        composite = None
        if starter_index >= 0 and (last_ccc < ccc or last_ccc == 0):
            if 0x1100 <= starter <= 0x1112 and 0x1161 <= point <= 0x1175:
                composite = 0xAC00 + (starter - 0x1100) * 588 + (point - 0x1161) * 28
            elif 0xAC00 <= starter <= 0xD7A3 and (starter - 0xAC00) % 28 == 0 and 0x11A8 <= point <= 0x11C2:
                composite = starter + point - 0x11A7
            else:
                composite = _COMPOSE.get((starter << 21) | point)
        if composite is not None:
            result[starter_index] = starter = composite
        else:
            if ccc == 0:
                starter_index, starter = len(result), point
            result.append(point)
            last_ccc = ccc
    return ''.join(map(chr, result))


def lowercase(text):
    points = list(map(ord, text))
    result = []
    for i, point in enumerate(points):
        if point == 0x03A3:
            before, after = i - 1, i + 1
            while before >= 0 and has_property(points[before], "case_ignorable"):
                before -= 1
            while after < len(points) and has_property(points[after], "case_ignorable"):
                after += 1
            final = before >= 0 and has_property(points[before], "cased") and not (after < len(points) and has_property(points[after], "cased"))
            result.append('ς' if final else 'σ')
        else:
            result.append(_LOWER.get(point, chr(point)))
    return ''.join(result)


def normalize(text):
    lowered = lowercase(''.join(c for c in nfkc(text) if ord(c) != 0x0640 and not 0x064B <= ord(c) <= 0x065F and ord(c) != 0x0670))
    result, pending_space = [], False
    for char in lowered:
        if has_property(ord(char), "whitespace"):
            pending_space = bool(result)
        else:
            if pending_space:
                result.append(' ')
            result.append(char)
            pending_space = False
    return ''.join(result)
