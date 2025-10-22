from collections.abc import Callable
from collections import OrderedDict
import functools
import typing as tp


Function = tp.TypeVar("Function", bound=tp.Callable[..., tp.Any])


def cache(max_size: int) -> tp.Callable[[Function], Function]:
    """
    Returns decorator, which stores result of function
    for `max_size` most recent function arguments.
    :param max_size: max amount of unique arguments to store values for
    :return: decorator, which wraps any function passed
    """

    def _make_key(args, kwargs: dict | None = None):
        if kwargs:
            return (args, sorted((k, v) for k, v in kwargs.items()))

        return args

    def wraps(func: Function) -> Function:
        cached_results_dict: OrderedDict[tp.Any, tp.Any] = OrderedDict()

        @functools.wraps(func)
        def wrapper(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
            key = _make_key(args, kwargs)
            if key in cached_results_dict:
                cached_results_dict.move_to_end(key, last=True)
                return cached_results_dict[key]

            result = func(*args, **kwargs)
            cached_results_dict[key] = result

            if len(cached_results_dict) > max_size:
                cached_results_dict.popitem(last=False)

            return result

        return tp.cast(Function, wrapper)

    return wraps
