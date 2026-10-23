"""RFC5646 well-formed syntax, distinct from registry membership or translation review."""
import re

GRANDFATHERED = set("en-gb-oed i-ami i-bnn i-default i-enochian i-hak i-klingon i-lux i-mingo i-navajo i-pwn i-tao i-tay i-tsu sgn-be-fr sgn-be-nl sgn-ch-de art-lojban cel-gaulish no-bok no-nyn zh-guoyu zh-hakka zh-min zh-min-nan zh-xiang".split())
NORMAL = re.compile(r"(?:[a-z]{2,3}(?:-[a-z]{3}){0,3}|[a-z]{4}|[a-z]{5,8})(?:-[a-z]{4})?(?:-(?:[a-z]{2}|[0-9]{3}))?((?:-(?:[a-z0-9]{5,8}|[0-9][a-z0-9]{3}))*)((?:-[0-9a-wy-z](?:-[a-z0-9]{2,8})+)*)(?:-x(?:-[a-z0-9]{1,8})+)?")


def valid_tag(value):
    tag = value.lower()
    if tag in GRANDFATHERED or re.fullmatch(r"x(?:-[a-z0-9]{1,8})+", tag): return True
    match = NORMAL.fullmatch(tag)
    if not match: return False
    variants = [v for v in match[1].split("-") if v]
    singletons = [v for v in match[2].split("-") if len(v) == 1]
    return len(set(variants)) == len(variants) and len(set(singletons)) == len(singletons)
