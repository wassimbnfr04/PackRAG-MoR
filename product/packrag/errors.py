from kpack_builder.core import PackError


def require(condition, message="Invalid product pack"):
    if not condition: raise PackError(message)
