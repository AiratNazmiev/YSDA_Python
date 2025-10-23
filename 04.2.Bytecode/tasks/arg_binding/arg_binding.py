from types import FunctionType
from typing import Any
CO_VARARGS = 4
CO_VARKEYWORDS = 8

ERR_TOO_MANY_POS_ARGS = 'Too many positional arguments'
ERR_TOO_MANY_KW_ARGS = 'Too many keyword arguments'
ERR_MULT_VALUES_FOR_ARG = 'Multiple values for arguments'
ERR_MISSING_POS_ARGS = 'Missing positional arguments'
ERR_MISSING_KWONLY_ARGS = 'Missing keyword-only arguments'
ERR_POSONLY_PASSED_AS_KW = 'Positional-only argument passed as keyword argument'


def bind_args(func: FunctionType, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Bind values from `args` and `kwargs` to corresponding arguments of `func`

    :param func: function to be inspected
    :param args: positional arguments to be bound
    :param kwargs: keyword arguments to be bound
    :return: `dict[argument_name] = argument_value` if binding was successful,
             raise TypeError with one of `ERR_*` error descriptions otherwise
    """
    code = func.__code__
    flags = code.co_flags

    posonly_cnt = getattr(code, "co_posonlyargcount", 0)
    total_pos_cnt = code.co_argcount
    kwonly_cnt = code.co_kwonlyargcount

    varnames = code.co_varnames

    posonly_names = list(varnames[:posonly_cnt])
    pos_or_kw_names = list(varnames[posonly_cnt: total_pos_cnt])
    kwonly_names = list(varnames[total_pos_cnt: total_pos_cnt + kwonly_cnt])

    idx = total_pos_cnt + kwonly_cnt
    vararg_name = varnames[idx] if (flags & CO_VARARGS) else None
    if vararg_name is not None:
        idx += 1
    varkw_name = varnames[idx] if (flags & CO_VARKEYWORDS) else None


    pos_defaults = func.__defaults__ or ()
    kw_defaults = func.__kwdefaults__ or {}

    all_pos_names = posonly_names + pos_or_kw_names
    pos_default_map: dict[str, Any] = {}
    if pos_defaults:
        for name, default in zip(all_pos_names[-len(pos_defaults):], pos_defaults):
            pos_default_map[name] = default

    bound: dict[str, Any] = {}
    remaining_kwargs = dict(kwargs)

    if varkw_name is None:
        for k in list(remaining_kwargs.keys()):
            if k in posonly_names:
                raise TypeError(ERR_POSONLY_PASSED_AS_KW)

    if vararg_name is None and len(args) > total_pos_cnt:
        raise TypeError(ERR_TOO_MANY_POS_ARGS)

    n_bind_pos = min(len(args), total_pos_cnt)
    for i in range(n_bind_pos):
        bound[all_pos_names[i]] = args[i]

    extra_pos = args[n_bind_pos:]
    if vararg_name is not None:
        bound[vararg_name] = tuple(extra_pos)
    else:
        if extra_pos:
            raise TypeError(ERR_TOO_MANY_POS_ARGS)

    for name in pos_or_kw_names:
        if name in remaining_kwargs:
            if name in bound:
                raise TypeError(ERR_MULT_VALUES_FOR_ARG)
            bound[name] = remaining_kwargs.pop(name)

    if varkw_name is None:
        for k in list(remaining_kwargs.keys()):
            if k in posonly_names:
                raise TypeError(ERR_POSONLY_PASSED_AS_KW)

    for name in kwonly_names:
        if name in remaining_kwargs:
            bound[name] = remaining_kwargs.pop(name)

    for name in all_pos_names:
        if name not in bound:
            if name in pos_default_map:
                bound[name] = pos_default_map[name]
            else:
                raise TypeError(ERR_MISSING_POS_ARGS)

    for name in kwonly_names:
        if name not in bound:
            if name in kw_defaults:
                bound[name] = kw_defaults[name]
            else:
                raise TypeError(ERR_MISSING_KWONLY_ARGS)

    if remaining_kwargs:
        if varkw_name is not None:
            bound[varkw_name] = dict(remaining_kwargs)
        else:
            raise TypeError(ERR_TOO_MANY_KW_ARGS)
    else:
        if varkw_name is not None and varkw_name not in bound:
            bound[varkw_name] = {}

    if vararg_name is not None and vararg_name not in bound:
        bound[vararg_name] = ()

    return bound
