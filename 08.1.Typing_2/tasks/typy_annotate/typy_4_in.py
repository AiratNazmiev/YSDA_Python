from typing import Optional, TypeVar, Protocol, overload, Container

T = TypeVar("T")


class ContainsAll(Protocol):
    def __contains__(self, a: object) -> bool:
        ...

@overload
def f(a: list[int], b: int) -> Optional[int]:
    ...


@overload
def f(a: set[int], b: int) -> Optional[int]:
    ...

@overload
def f(a: str, b: str) -> Optional[str]:
    ...

@overload
def f(a: ContainsAll, b: T) -> Optional[T]:
    ...

def f(a: Container[object], b: T) -> Optional[T]:
    return b if b in a else None


TEST_SAMPLES = """
# SUCCESS

a: float | None
a = f([1, 2, 3], 1)
if a is not None:
    a += 1

# SUCCESS
a: float | None
a = f({1, 2, 3}, 1)


# SUCCESS
a: str | None
a = f("abcd", "a")

# SUCCESS
class A:
    def __contains__(self, a: object) -> bool:
        return True

a: int | None
a = f(A(), 10)

b: str | None
b = f(A(), "qwerty")

# ERROR
f([1, 2, 3], "h")

# ERROR
f([1, 2, 3], 1.3)

# ERROR
f([1.4, 2, 3], 1)

# ERROR
f(["a", "b", "c"], 1)
"""
