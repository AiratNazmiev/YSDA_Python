import time
import contextlib
import types
import typing as tp


class TimeoutException(Exception):
    pass

class SoftTimeoutException(TimeoutException):
    pass

class HardTimeoutException(TimeoutException):
    pass


class TimeCatcher:
    def __init__(
            self,
            soft_timeout: int | float | None = None,
            hard_timeout: int | float | None = None
        ) -> None:
        if not isinstance(soft_timeout, (int, float, type(None))) or \
           not isinstance(hard_timeout, (int, float, type(None))):
            raise AssertionError("Both soft_timeout and hard_timeout must be int, float or None")

        if hard_timeout is not None:
            if soft_timeout is not None:
                if not (hard_timeout >= soft_timeout > 0):
                    raise AssertionError("It must be hard_timeout >= soft_timeout > 0")
            elif hard_timeout <= 0:
                raise AssertionError("It must be hard_timeout > 0")
        elif soft_timeout is not None and soft_timeout < 0:
            raise AssertionError("It must be soft_timeout > 0")

        self.soft_timeout = soft_timeout
        self.hard_timeout = hard_timeout
        self.t: float | None = None

    def __enter__(
            self
        ) -> tp.Self:
        self.enter_time = time.perf_counter()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: types.TracebackType | None
        ) -> bool | None:
        self.exit_time = time.perf_counter()
        self.t = self.exit_time - self.enter_time
        if self.hard_timeout is not None and self.t > self.hard_timeout:
            raise HardTimeoutException
        elif self.soft_timeout is not None and self.t > self.soft_timeout:
            raise SoftTimeoutException

    def _curr_time(self):
        if self.t is None:
            return time.perf_counter() - self.enter_time
        else:
            return self.t

    def __float__(self):
        return float(self._curr_time())

    def __int__(self):
        return int(self._curr_time())

    def __str__(self):
        return f"Time consumed: {self._curr_time():.4f}"
