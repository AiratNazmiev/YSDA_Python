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

        self.instructions: list[dis.Instruction] = list(dis.get_instructions(self.code))
        self.pc: int = 0
        self.next_pc: int = 0

    def top(self) -> tp.Any:
        return self.data_stack[-1]

    def topn(self, n: int) -> tp.Any:
        return self.data_stack[-n]

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

    # def run(self) -> tp.Any:
    #     for instruction in dis.get_instructions(self.code):
    #         getattr(self, instruction.opname.lower() + "_op")(instruction.argval)
    #     return self.return_value

    def run(self) -> tp.Any:
        while self.pc < len(self.instructions):
            inst = self.instructions[self.pc]
            self.next_pc = self.pc + 1  # fall-through by default

            # For 3.13, jumps use *relative deltas*. Many other ops want resolved argval.
            opname = inst.opname
            is_jump = opname.startswith("JUMP") or opname.startswith("POP_JUMP") or opname == "FOR_ITER"
            arg = inst.arg if is_jump else inst.argval

            getattr(self, opname.lower() + "_op")(arg)
            self.pc = self.next_pc

        return self.return_value

    def nop_op(self, arg: tp.Any) -> None:
        pass

    def resume_op(self, arg: int) -> tp.Any:
        pass

    def push_null_op(self, arg: int) -> tp.Any:
        self.push(None)

    def precall_op(self, arg: int) -> tp.Any:
        pass

    def load_build_class_op(self, arg: int) -> None:
        self.push(builtins.__build_class__)

    def pop_top_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-POP_TOP
        """
        self.pop()

    def end_for_op(self, arg: tp.Any) -> None:
        self.pop_top_op(arg)

    def copy_op(self, i: int) -> None:
        assert i > 0
        self.push(self.data_stack[i])

    def swap_op(self, i: int) -> None:
        self.data_stack[-i], self.data_stack[-1] = self.data_stack[-1], self.data_stack[-i]

    ####################
    # Unary operations #
    ####################

    def unary_positive_op(self, arg: tp.Any) -> None:
        self.push(operator.pos(self.pop()))

    def unary_negative_op(self, arg: tp.Any) -> None:
        self.push(operator.neg(self.pop()))

    def unary_not_op(self, arg: tp.Any) -> None:
        self.push(operator.not_(self.pop()))

    def unary_invert_op(self, arg: tp.Any) -> None:
        self.push(operator.invert(self.pop()))

    def get_iter_op(self, argc: tp.Any) -> None:
        self.push(iter(self.pop()))

    # def get_yield_from_iter_op(self, arg: tp.Any) -> None:
    #     ...

    def to_bool_op(self, arg: tp.Any) -> None:
        self.push(bool(self.pop()))

    ##################################
    # Binary and in-place operations #
    ##################################

    def binary_op_op(self, arg: int) -> None:
        """
        https://github.com/python/cpython/blob/main/Include/opcode.h
        """
        lhs, rhs = self.popn(2)
        ops = {
            0: operator.add,
            1: operator.and_,
            2: operator.floordiv,
            3: operator.lshift,
            4: operator.matmul,
            5: operator.mul,
            6: operator.mod,
            7: operator.or_,
            8: operator.pow,
            9: operator.rshift,
            10: operator.sub,
            11: operator.truediv,
            12: operator.xor
        }
        for n in range(13, 26):
            ops[n] = ops[n-13]

        if (op := ops.get(arg)) is None:
            raise NameError

        res = op(lhs, rhs)
        self.push(res)

    def binary_subscr_op(self, arg: int) -> None:
        container, key = self.popn(2)
        self.push(container[key])

    def store_subscr_op(self, arg: int) -> None:
        value, container, key = self.popn(3)
        container[key] = value

    def delete_subscr_op(self, arg: int):
        container, key = self.popn(2)
        del container[key]

    def binary_slice_op(self, arg: int) -> None:
        container, start, end = self.popn(3)
        self.push(container[start:end])

    def store_slice_op(self, arg: int) -> None:
        values, container, start, end = self.popn(4)
        container[start:end] = values

    ######################
    # Coroutine opcodes #
    ######################
    # TODO

    def call_op(self, argc: int) -> None:
        args = self.popn(argc)
        self_or_null = self.pop()
        func = self.pop()

        if self_or_null is not None:
            bound_self = getattr(func, "__self__", None)
            if bound_self is not None:
                result = func(*args)
            else:
                result = func(self_or_null, *args)
        else:
            result = func(*args)

        self.push(result)

    def call_kw_op(self, argc: int) -> None:
        names = self.pop()
        if not isinstance(names, tuple) or not all(isinstance(k, str) for k in names):
            raise TypeError("CALL_KW expects a tuple of keyword names on TOS")

        nkw = len(names)
        nargs = argc - nkw
        if nargs < 0:
            raise ValueError("CALL_KW: argc smaller than number of keyword names")

        kw_values = self.popn(nkw)
        pos_args = self.popn(nargs)

        self_or_null = self.pop()
        func = self.pop()

        kwargs = {k: v for k, v in zip(names, kw_values)}

        if self_or_null is not None:
            bound_self = getattr(func, "__self__", None)
            if bound_self is not None:
                result = func(*pos_args, **kwargs)
            else:
                result = func(self_or_null, *pos_args, **kwargs)
        else:
            result = func(*pos_args, **kwargs)

        self.push(result)

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


    # def load_global_op(self, arg: str) -> None:
    #     """
    #     Operation description:
    #         https://docs.python.org/release/3.13.7/library/dis.html#opcode-LOAD_GLOBAL
    #     """
    #     # TODO: parse all scopes
    #     self.push(self.builtins[arg])
    #     self.push(None)
    def load_global_op(self, arg: str) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.11.5/library/dis.html#opcode-LOAD_GLOBAL
        """
        if arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError

    def load_fast_op(self, var_num: str) -> None:
        self.push(self.locals[var_num])

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

    def make_function_op(self, arg: int) -> None:
        code = self.pop()

        sig_func = types.FunctionType(code, self.globals, code.co_name)

        def f(*call_args: tp.Any, **call_kwargs: tp.Any) -> tp.Any:
            bound_locals = bind_args(sig_func, *call_args, **call_kwargs)

            callee_locals = dict(self.locals)
            callee_locals.update(bound_locals)

            frame = Frame(code, self.builtins, self.globals, callee_locals)
            return frame.run()

        self.push(f)

    def store_name_op(self, arg: str) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-STORE_NAME
        """
        const = self.pop()
        self.locals[arg] = const

    def build_list_op(self, count: int) -> None:
        elts = self.popn(count)
        self.push(elts)

    def list_extend_op(self, i: int) -> None:
        tos = self.pop()
        tos1 = self.pop()
        if len(tos1) == 0:
            list.extend(tos1, tos)
        else:
            list.extend(tos1, tos)
        self.push(tos1)

    def build_tuple_op(self, size: int) -> None:
        buf = []
        for i in range(size):
            tos = self.pop()
            buf.append(tos)
        self.push(tuple(buf))

    def build_slice_op(self, argc: int) -> None:
        if argc == 2:
            start, stop = self.popn(2)
            self.push(slice(start, stop))
        if argc == 3:
            start, stop, step = self.popn(3)
            self.push(slice(start, stop, step))

    def compare_op_op(self, op: str) -> None:
        lhs, rhs = self.popn(2)
        ops = {
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
        }
        if (comp := ops.get(op)) is None:
            raise NameError
        self.push(comp(lhs, rhs))

    def contains_op_op(self, invert: int) -> None:
        lhs, rhs = self.popn(2)
        self.push(bool((lhs in rhs) ^ invert))

    def is_op_op(self, invert: int) -> None:
        lhs, rhs = self.popn(2)
        self.push(bool((lhs is rhs) ^ invert))

    ###########
    # Imports #
    ###########

    # def import_name_op(self, namei: str) -> None:
    #     level, fromlist = self.popn(2)
    #     self.push(
    #         __import__(namei, self.globals, self.locals, fromlist, level)
    #     )

    #########
    # Jumps #
    #########
    def _jump_forward(self, delta: int) -> None:
        # Move to instruction after current, plus delta
        self.next_pc = self.pc + 1 + int(delta)

    def _jump_backward(self, delta: int) -> None:
        # Move to instruction after current, minus delta
        self.next_pc = self.pc + 1 - int(delta)

    def pop_jump_if_true_op(self, delta: int) -> None:
        v = self.pop()
        if not isinstance(v, bool):
            raise TypeError("POP_JUMP_IF_TRUE requires exact bool (Py 3.13)")
        if v:
            self._jump_forward(delta)

    def pop_jump_if_false_op(self, delta: int) -> None:
        v = self.pop()
        if not isinstance(v, bool):
            raise TypeError("POP_JUMP_IF_FALSE requires exact bool (Py 3.13)")
        if not v:
            self._jump_forward(delta)

    def pop_jump_if_none_op(self, delta: int) -> None:
        if self.pop() is None:
            self._jump_forward(delta)

    def pop_jump_if_not_none_op(self, delta: int) -> None:
        if self.pop() is not None:
            self._jump_forward(delta)

    def jump_forward_op(self, delta: int) -> None:
        self._jump_forward(delta)

    def jump_backward_op(self, delta: int) -> None:
        self._jump_backward(delta)

    def jump_backward_no_interrupt_op(self, delta: int) -> None:
        self._jump_backward(delta)

class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> None:
        """
        :param code_obj: code for interpreting
        """
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()['__builtins__'], globals_context, globals_context)
        return frame.run()

def bind_args(func: types.FunctionType, *args: tp.Any, **kwargs: tp.Any) -> dict[str, tp.Any]:
    """Bind values from `args` and `kwargs` to corresponding arguments of `func`

    :param func: function to be inspected
    :param args: positional arguments to be bound
    :param kwargs: keyword arguments to be bound
    :return: `dict[argument_name] = argument_value` if binding was successful,
             raise TypeError with one of `ERR_*` error descriptions otherwise
    """
    CO_VARARGS = 4
    CO_VARKEYWORDS = 8

    ERR_TOO_MANY_POS_ARGS = 'Too many positional arguments'
    ERR_TOO_MANY_KW_ARGS = 'Too many keyword arguments'
    ERR_MULT_VALUES_FOR_ARG = 'Multiple values for arguments'
    ERR_MISSING_POS_ARGS = 'Missing positional arguments'
    ERR_MISSING_KWONLY_ARGS = 'Missing keyword-only arguments'
    ERR_POSONLY_PASSED_AS_KW = 'Positional-only argument passed as keyword argument'

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
    pos_default_map: dict[str, tp.Any] = {}
    if pos_defaults:
        for name, default in zip(all_pos_names[-len(pos_defaults):], pos_defaults):
            pos_default_map[name] = default

    bound: dict[str, tp.Any] = {}
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
