from functools import wraps
from datetime import datetime


def profiler(func):  # type: ignore
    """
    Returns profiling decorator, which counts calls of function
    and measure last function execution time.
    Results are stored as function attributes: `calls`, `last_time_taken`
    :param func: function to decorate
    :return: decorator, which wraps any function passed
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        is_outer = wrapper._depth == 0
        if is_outer:
            wrapper.calls = 0
            wrapper._start_time = datetime.now()

        wrapper._depth += 1
        wrapper.calls += 1
        result = func(*args, **kwargs)
        wrapper._depth -= 1

        if is_outer:
            end_time = datetime.now()
            wrapper.last_time_taken = (end_time - wrapper._start_time).total_seconds()

        return result

    wrapper.calls = 0
    wrapper.last_time_taken = 0.
    wrapper._depth = 0
    wrapper._start_time = 0.

    return wrapper
