"""
Forth-style operand stack for Patchboard Atlas.

Data flows through the system via the stack S.
"""


S = []

var = {}


def push(x):
    """( -- x )  Push x onto the stack."""
    S.append(x)


def pop():
    """( x -- )  Remove and return top of stack."""
    return S.pop()


def top():
    """( x -- x )  Return top of stack without removing."""
    return S[-1]


def drop():
    """( x -- )  Discard top of stack."""
    S.pop()


def clear():
    """( ... -- )  Empty the stack."""
    S.clear()
