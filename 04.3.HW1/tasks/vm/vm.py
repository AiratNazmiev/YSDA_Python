"""
Simplified VM code which works for some cases.
You need extend/rewrite code to pass all cases.
"""

import builtins
import dis
import types
import typing as tp
import operator


class Frame:
    """
    Frame header in cpython with description
        https://github.com/python/cpython/blob/3.13/Include/internal/pycore_frame.h

    Text description of frame parameters
        https://docs.python.org/3/library/inspect.html?highlight=frame#types-and-members
    """
    def __init__(self,
                 frame_code: types.CodeType,
                 frame_builtins: dict[str, tp.Any],
                 frame_globals: dict[str, tp.Any],
                 frame_locals: dict[str, tp.Any]) -> None:
        self.code = frame_code
        self.builtins = frame_builtins
        self.globals = frame_globals
        self.locals = frame_locals
        self.data_stack: tp.Any = []
        self.return_value = None

    def top(self) -> tp.Any:
        return self.data_stack[-1]

    def pop(self) -> tp.Any:
        return self.data_stack.pop()

    def push(self, *values: tp.Any) -> None:
        self.data_stack.extend(values)

    def popn(self, n: int) -> tp.Any:
        """
        Pop a number of values from the value stack.
        A list of n values is returned, the deepest value first.
        """
        if n > 0:
            returned = self.data_stack[-n:]
            self.data_stack[-n:] = []
            return returned
        else:
            return []

    def run(self) -> tp.Any:
        for instruction in dis.get_instructions(self.code):
            getattr(self, instruction.opname.lower() + "_op")(instruction.argval)
        return self.return_value

    def resume_op(self, arg: int) -> tp.Any:
        pass

    def push_null_op(self, arg: int) -> tp.Any:
        self.push(None)

    def precall_op(self, arg: int) -> tp.Any:
        pass

    def binary_op_op(self, op: int) -> None:
        a, b = self.popn(2)
        bo = {
            8: operator.pow,
            21: lambda x, y: x**y,

            5: operator.mul,
            18: operator.mul,

            2: operator.floordiv,
            15: operator.floordiv,

            11: operator.truediv,
            24: operator.truediv,

            6: operator.mod,
            19: operator.mod,

            0: operator.add,
            13: operator.add,

            10: operator.sub,
            23: operator.sub,

            'SUBSCR': operator.getitem,

            3: operator.lshift,
            16: operator.lshift,

            9: operator.rshift,
            22: operator.rshift,

            1: operator.and_,
            14: operator.and_,

            12: operator.xor,
            25: operator.xor,

            7: operator.or_,
            20: operator.or_,
        }

        if op not in bo:
            raise NameError

        res = bo[op](a, b)
        self.push(res)

    def call_op(self, arg: int) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-CALL
        """
        arguments = self.popn(arg)
        self.pop()  # TODO: use self arg for method calls
        f = self.pop()
        self.push(f(*arguments))

    def load_name_op(self, arg: str) -> None:
        """
        Partial realization

        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-LOAD_NAME
        """
        if arg in self.locals:
            self.push(self.locals[arg])
        elif arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError(f"Name {arg} is not defined")


    def load_global_op(self, arg: str) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-LOAD_GLOBAL
        """
        # TODO: parse all scopes
        self.push(self.builtins[arg])
        self.push(None)

    def load_const_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-LOAD_CONST
        """
        self.push(arg)

    def return_value_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-RETURN_VALUE
        """
        self.return_value = self.pop()

    def return_const_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-RETURN_VALUE
        """
        self.return_value = arg

    def pop_top_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-POP_TOP
        """
        self.pop()

    # def make_function_op(self, arg: int) -> None:
    #     """
    #     Operation description:
    #         https://docs.python.org/release/3.13.7/library/dis.html#opcode-MAKE_FUNCTION
    #     """
    #     code = self.pop()  # the code associated with the function (at TOS1)

    #     # TODO: use arg to parse function defaults

    #     def f(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
    #         # TODO: parse input arguments using code attributes such as co_argcount

    #         parsed_args: dict[str, tp.Any] = {}
    #         f_locals = dict(self.locals)
    #         f_locals.update(parsed_args)

    #         frame = Frame(code, self.builtins, self.globals, f_locals)  # Run code in prepared environment
    #         return frame.run()

    #     self.push(f)

    def store_name_op(self, arg: str) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-STORE_NAME
        """
        const = self.pop()
        self.locals[arg] = const

    # def build_list_op(self, count: int) -> None:
    #     elts = self.popn(count)
    #     self.push(elts)

    # def list_extend_op(self, i: int) -> None:
    #     tos = self.pop()
    #     tos1 = self.pop()
    #     if len(tos1) == 0:
    #         list.extend(tos1, tos)
    #     else:
    #         list.extend(tos1, tos)
    #     self.push(tos1)

    # def build_tuple_op(self, size: int) -> None:
    #     buf = []
    #     for i in range(size):
    #         tos = self.pop()
    #         buf.append(tos)
    #     self.push(tuple(buf))

    # def build_slice_op(self, argc: int) -> None:
    #     if argc == 2:
    #         tos = self.pop()
    #         tos1 = self.pop()
    #         self.push(slice(tos1, tos))
    #     if argc == 3:
    #         tos = self.pop()
    #         tos1 = self.pop()
    #         tos2 = self.pop()
    #         self.push(slice(tos2, tos1, tos))

    # def binary_subscr_op(self, arg: tp.Any) -> None:
    #     tos = self.pop()
    #     tos1 = self.pop()
    #     self.push(tos1[tos])

    # def compare_op_op(self, op: str) -> None:
    #     a, b = self.popn(2)
    #     co = {
    #         "<": lambda x, y: x < y,
    #         "<=": lambda x, y: x <= y,
    #         "==": lambda x, y: x == y,
    #         "!=": lambda x, y: x != y,
    #         ">": lambda x, y: x > y,
    #         ">=": lambda x, y: x >= y,
    #     }
    #     if op not in co:
    #         raise NameError
    #     self.push(co[op](a, b))

# def bind_args(func: types.FunctionType, defaults: tp.Any, *args: tp.Any, **kwargs: tp.Any) -> dict[str, tp.Any]:

#     CO_VARARGS = 4
#     CO_VARKEYWORDS = 8

#     ERR_TOO_MANY_POS_ARGS = 'Too many positional arguments'
#     ERR_TOO_MANY_KW_ARGS = 'Too many keyword arguments'
#     ERR_MULT_VALUES_FOR_ARG = 'Multiple values for arguments'
#     ERR_MISSING_POS_ARGS = 'Missing positional arguments'
#     ERR_MISSING_KWONLY_ARGS = 'Missing keyword-only arguments'
#     ERR_POSONLY_PASSED_AS_KW = 'Positional-only argument passed as keyword argument'

#     code = func.__code__

#     if 'args' in kwargs.keys() or 'kwargs' in kwargs.keys():
#         args = kwargs['args']
#         kwargs = kwargs['kwargs']

#     if not args:
#         args = None   # type: ignore
#     if not kwargs:
#         kwargs = None   # type: ignore

#     if defaults:
#         defaults_ = defaults.copy()
#         defaults = None
#         kwdefaults = None
#         if defaults_:
#             if len(defaults_) == 1:
#                 defaults = defaults_[0]
#             if len(defaults_) == 2:
#                 defaults = defaults_[0]
#                 kwdefaults = defaults_[1]
#     else:
#         defaults = None
#         kwdefaults = None
#     argcount = code.co_argcount
#     varnames = code.co_varnames
#     kwonlyargcount = code.co_kwonlyargcount
#     posonlyargcount = code.co_posonlyargcount
#     flags = code.co_flags
#     flag_varargs = bool(CO_VARARGS & flags)
#     flag_varkeywords = bool(CO_VARKEYWORDS & flags)

#     # arguments: signature and input
#     args_kwargs_count = int(flag_varargs) + int(flag_varkeywords)
#     signature_args_count = argcount + args_kwargs_count + kwonlyargcount

#     # only function's arguments and args/kwargs names
#     varnames_ = varnames[:signature_args_count]
#     args_name, kwargs_name = None, None
#     if flag_varargs and flag_varkeywords:
#         args_name = varnames_[-2]
#         kwargs_name = varnames_[-1]
#     elif flag_varargs and not flag_varkeywords:
#         args_name = varnames_[-1]
#     elif not flag_varargs and flag_varkeywords:
#         kwargs_name = varnames_[-1]

#     # sentinel instead of None
#     NONE: tp.Any = object()

#     # binding template with flags
#     res: tp.Any = {var: {'value': NONE,
#                     'seen': False,
#                     'pos_only': False,
#                     'kw_only': False}
#                 for var in varnames_}

#     # mark pos only (always at the beginning)
#     for i in range(posonlyargcount):
#         res[varnames_[i]]['pos_only'] = True

#     # mark kw only (last args without *args and **kwargs, they are always last in co_varnames)
#     args_list = list(res.keys())
#     if kwonlyargcount > 0:
#         if args_kwargs_count > 0:
#             kw_only = args_list[:-args_kwargs_count][-kwonlyargcount:]
#         else:
#             kw_only = args_list[-kwonlyargcount:]
#         assert len(kw_only) == kwonlyargcount
#         for kw in kw_only:
#             res[kw]['kw_only'] = True

#     # go through res and fill in pos args
#     args_ = list(args) if args is not None else None  # for mutability
#     pos = None
#     pos_slots = len(varnames_) - (kwonlyargcount + args_kwargs_count)
#     for k, v in res.items():
#         pos = args_.pop(0) if args_ else NONE
#         if pos is not NONE:
#             if flag_varargs and (pos_slots <= 0):
#                 if res[args_name]['value'] is not NONE:
#                     res[args_name]['value'] += [pos]
#                 else:
#                     res[args_name]['value'] = [pos]
#                 res[args_name]['seen'] = True
#             elif v['pos_only'] or (not v['kw_only']):
#                 v['value'] = pos
#                 v['seen'] = True
#             elif v['kw_only']:
#                 raise TypeError(ERR_TOO_MANY_POS_ARGS)
#         pos_slots -= 1

#     # in case of only *args and popped first pos
#     if (len(res) == 1) and flag_varargs and (pos_slots >= 0):
#         args_ = [pos] + args_

#     # if there's left some poses, raise
#     if (not flag_varargs) and len(args_) > 0:
#         raise TypeError(ERR_TOO_MANY_POS_ARGS)

#     # go through kw args and put them into res
#     if kwargs:
#         for k, v in kwargs.items():
#             if (k not in res) and (not flag_varkeywords):
#                 raise TypeError(ERR_TOO_MANY_KW_ARGS)
#             elif (k in res) and res[k]['pos_only']:
#                 if not flag_varkeywords:
#                     raise TypeError(ERR_POSONLY_PASSED_AS_KW)
#             elif (k in res) and res[k]['seen']:
#                 raise TypeError(ERR_MULT_VALUES_FOR_ARG)
#             elif k in res:
#                 res[k]['value'] = v
#                 res[k]['seen'] = True
#             elif k not in res:
#                 if res[kwargs_name]['value'] is not NONE:
#                     res[kwargs_name]['value'].update({k: v})
#                 else:
#                     res[kwargs_name]['value'] = {k: v}
#                 res[kwargs_name]['seen'] = True

#     # go through defaults - args (stand before *args, **kwargs and kw_only)
#     if defaults is not None:
#         if (strip := kwonlyargcount + args_kwargs_count) > 0:
#             args_before_stars_and_kw = args_list[:-strip]
#         else:
#             args_before_stars_and_kw = args_list.copy()
#         for i in range(len(defaults)):
#             k = args_before_stars_and_kw[-i-1]
#             if not res[k]['seen']:
#                 res[k]['value'] = defaults[-i-1]
#                 res[k]['seen'] = True

#     # go through defaults - kwargs
#     if kwdefaults is not None:
#         for k, v in kwdefaults.items():
#             if not res[k]['seen']:
#                 res[k]['value'] = v
#                 res[k]['seen'] = True

#     # pack rest of args and kwargs to *args
#     if flag_varargs:
#         if not res[args_name]['seen']:
#             if args_ and args_[0] is not NONE:
#                 res[args_name]['value'] = tuple(args_)
#             else:
#                 res[args_name]['value'] = tuple()
#             res[args_name]['seen'] = True
#         else:
#             res[args_name]['value'] += args_
#             res[args_name]['value'] = tuple(res[args_name]['value'])

#     # pack rest of kwargs to **kwargs
#     if flag_varkeywords and kwargs is not None:
#         extra_kwargs = set(kwargs.keys()) - set(res.keys())
#         pos_only_args = [k for k, v in res.items() if v['pos_only']]
#         if kw_pos := set(kwargs.keys()).intersection(set(pos_only_args)):
#             extra_kwargs = extra_kwargs.union(kw_pos)
#         extra_kwargs_dict = {k: kwargs[k] for k in extra_kwargs}
#         if extra_kwargs_dict:
#             res[kwargs_name]['value'] = extra_kwargs_dict
#         else:
#             res[kwargs_name]['value'] = dict()
#         res[kwargs_name]['seen'] = True

#     # check missing arguments
#     for k, v in res.items():
#         if (not v['seen']) and (k not in ['args', 'kwargs']):
#             if v['pos_only'] or (not v['kw_only']):
#                 raise TypeError(ERR_MISSING_POS_ARGS)
#             else:
#                 raise TypeError(ERR_MISSING_KWONLY_ARGS)

#     result = {k: v['value'] for k, v in res.items()}
#     return result

class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> None:
        """
        :param code_obj: code for interpreting
        """
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()['__builtins__'], globals_context, globals_context)
        return frame.run()
