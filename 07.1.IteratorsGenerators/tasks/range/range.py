from collections.abc import Iterable, Iterator, Sized


class RangeIterator(Iterator[int]):
    """The iterator class for Range"""

    def __init__(self, range_: 'Range') -> None:
        self._range = range_
        self._current = range_.start

    def __iter__(self) -> 'RangeIterator':
        return self

    def __next__(self) -> int:
        step = self._range.step
        stop = self._range.stop
        current = self._current

        if step > 0:
            if current >= stop:
                raise StopIteration
        else:
            if current <= stop:
                raise StopIteration

        self._current += step
        return current


class Range(Sized, Iterable[int]):
    """The range-like type, which represents an immutable sequence of numbers"""

    def __init__(self, *args: int) -> None:
        """
        :param args: either it's a single `stop` argument
            or sequence of `start, stop[, step]` arguments.
        If the `step` argument is omitted, it defaults to 1.
        If the `start` argument is omitted, it defaults to 0.
        If `step` is zero, ValueError is raised.
        """
        num_args = len(args)

        if num_args == 1:
            start = 0
            stop = args[0]
            step = 1
        elif num_args == 2:
            start, stop = args
            step = 1
        elif num_args == 3:
            start, stop, step = args
        else:
            raise TypeError(
                f"Range expected at least 1 argument, at most 3, got {num_args}"
            )

        if step == 0:
            raise ValueError("step must not be zero")

        self.start = start
        self.stop = stop
        self.step = step

    def __iter__(self) -> 'RangeIterator':
        return RangeIterator(self)

    def __repr__(self) -> str:
        if self.step == 1:
            return f"range({self.start}, {self.stop})"
        else:
            return f"range({self.start}, {self.stop}, {self.step})"

    # def __str__(self) -> str:
    #     return repr(self)

    def __contains__(self, key: int) -> bool:
        if len(self) == 0:
            return False

        if self.step > 0:
            if key < self.start or key >= self.stop:
                return False
        else:
            if key > self.start or key <= self.stop:
                return False

        return (key - self.start) % self.step == 0

    def __getitem__(self, key: int) -> int:
        length = len(self)

        if key < 0:
            key += length

        if key < 0 or key >= length:
            raise IndexError("Range index out of range")

        return self.start + key * self.step

    def __len__(self) -> int:
        if self.step > 0:
            if self.start >= self.stop:
                return 0
            # ceil((stop - start) / step)
            return (self.stop - self.start + self.step - 1) // self.step
        else:
            if self.start <= self.stop:
                return 0
            step_abs = -self.step
            # ceil((start - stop) / |step|)
            return (self.start - self.stop + step_abs - 1) // step_abs
