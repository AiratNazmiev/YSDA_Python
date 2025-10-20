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
        if wrapper._depth == 0:
            wrapper.calls = 1
        else:
            wrapper.calls += 1
        wrapper._depth += 1
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        wrapper.last_time_taken = (end_time - start_time).total_seconds()
        wrapper._depth -= 1
        return result

    wrapper.calls = 0
    wrapper.last_time_taken = 0.
    wrapper._depth = 0

    return wrapper
