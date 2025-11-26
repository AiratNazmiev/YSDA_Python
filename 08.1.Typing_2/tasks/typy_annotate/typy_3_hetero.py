from typing import TypeVar, Tuple
from collections.abc import Sized, Sequence

TStrLike = TypeVar("TStrLike", bound=str)


def f(a: Tuple[Sized, TStrLike, Sequence[str]]) -> TStrLike:
    return a[1]


TEST_SAMPLES = """
# SUCCESS
f(("a", "b", "c"))

# SUCCESS
f(("a", "b", ["c", "d", "e"]))

# ERROR
f(("a", "b", "c", "d"))

# SUCCESS
class A(str):
    pass

a: A
a = f(("a", A(), A()))

# SUCCESS
f((["a", "b"], "c", "d"))

# SUCCESS
class A:
    def __len__(self) -> int:
        return 1

f((A(), "c", "d"))

# ERROR
class A:
    def __len__(self) -> int:
        return 1

f((A(), "c", {"d", "e"}))
"""
