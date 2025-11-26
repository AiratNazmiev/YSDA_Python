from typing import Generic, TypeVar, cast

T = TypeVar("T", int, float)


class Pair(Generic[T]):
    def __init__(self, a: T, b: T) -> None:
        self._a: T = a
        self._b: T = b

    def sum(self) -> T:
        tmp_sum = cast(int | float, self._a) + cast(int | float, self._b)
        return cast(T, tmp_sum)

    def first(self) -> T:
        return self._a

    def second(self) -> T:
        return self._b

    def __iadd__(self, pair: "Pair[T]") -> "Pair[T]":
        new_a = cast(int | float, self._a) + cast(int | float, pair._a)
        new_b = cast(int | float, self._b) + cast(int | float, pair._b)

        self._a = cast(T, new_a)
        self._b = cast(T, new_b)
        return self
