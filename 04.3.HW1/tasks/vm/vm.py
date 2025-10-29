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
        self.data_stack: list[tp.Any] = []
        self.return_value = None

        self.instructions: list[dis.Instruction] = list(dis.get_instructions(self.code))
        self._off2idx: dict[int, int] = {inst.offset: i for i, inst in enumerate(self.instructions)}
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

    def popn(self, n: int) -> list[tp.Any]:
        if n > 0:
            returned = self.data_stack[-n:]
            self.data_stack[-n:] = []
            return returned
        return []

    def run(self) -> tp.Any:
        RAW_ARG_OPS = {
            "LOAD_GLOBAL", "LOAD_ATTR",
            "LOAD_FAST_LOAD_FAST", "STORE_FAST_STORE_FAST", "STORE_FAST_LOAD_FAST",
            "SET_FUNCTION_ATTRIBUTE",
        }

        while self.pc < len(self.instructions):
            inst = self.instructions[self.pc]
            self.next_pc = self.pc + 1

            opname = inst.opname
            if opname in RAW_ARG_OPS:
                arg = inst.arg
            else:
                arg = inst.argval

            getattr(self, opname.lower() + "_op")(arg)
            self.pc = self.next_pc

        return self.return_value

    # ---------- simple/misc ops ----------
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
        self.pop()

    def end_for_op(self, arg: tp.Any) -> None:
        self.pop()

    def copy_op(self, i: int) -> None:
        assert i > 0
        self.push(self.data_stack[-i])

    def swap_op(self, i: int) -> None:
        self.data_stack[-i], self.data_stack[-1] = self.data_stack[-1], self.data_stack[-i]

    # ---------- unary ops ----------
    def unary_positive_op(self, arg: tp.Any) -> None:
        self.push(operator.pos(self.pop()))

    def unary_negative_op(self, arg: tp.Any) -> None:
        self.push(operator.neg(self.pop()))

    def unary_not_op(self, arg: tp.Any) -> None:
        self.push(operator.not_(self.pop()))

    def unary_invert_op(self, arg: tp.Any) -> None:
        self.push(operator.invert(self.pop()))

    def get_iter_op(self, arg: tp.Any) -> None:
        self.push(iter(self.pop()))

    def to_bool_op(self, arg: tp.Any) -> None:
        self.push(bool(self.pop()))

    # ---------- binary ops ----------
    def binary_op_op(self, arg: int) -> None:
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
        op = ops.get(arg % 13)
        if op is None:
            raise NameError
        self.push(op(lhs, rhs))

    def binary_subscr_op(self, arg: int) -> None:
        container, key = self.popn(2)
        self.push(container[key])

    def store_subscr_op(self, arg: int) -> None:
        value, container, key = self.popn(3)
        container[key] = value

    def delete_subscr_op(self, arg: int) -> None:
        container, key = self.popn(2)
        del container[key]

    def binary_slice_op(self, arg: int) -> None:
        container, start, end = self.popn(3)
        self.push(container[start:end])

    def store_slice_op(self, arg: int) -> None:
        values, container, start, end = self.popn(4)
        container[start:end] = values

    # ---------- CALL ----------
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

    # ---------- names / globals / fast locals ----------
    def load_name_op(self, arg: str) -> None:
        if arg in self.locals:
            self.push(self.locals[arg])
        elif arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError(f"Name {arg} is not defined")

    def load_global_op(self, namei: int) -> None:
        idx = namei >> 1
        push_null = (namei & 1) != 0
        try:
            name = self.code.co_names[idx]
        except IndexError:
            raise RuntimeError(f"LOAD_GLOBAL: bad co_names index {idx}")
        if name in self.globals:
            val = self.globals[name]
        elif name in self.builtins:
            val = self.builtins[name]
        else:
            raise NameError(f"name {name} is not defined")
        self.push(val)
        if push_null:
            self.push(None)

    def load_fast_op(self, var_name: str) -> None:
        self.push(self.locals[var_name])

    def load_fast_load_fast_op(self, var_nums: int) -> None:
        idx1 = (var_nums >> 4)
        idx2 = (var_nums & 0x0F)
        name1 = self.code.co_varnames[idx1]
        name2 = self.code.co_varnames[idx2]
        self.push(self.locals[name1])
        self.push(self.locals[name2])

    def load_fast_check_op(self, var_name: str) -> None:
        value = self.locals.get(var_name)
        if value is None:
            raise UnboundLocalError
        self.push(value)

    def load_fast_and_clear_op(self, var_name: str) -> None:
        value = self.locals.pop(var_name, None)
        self.push(value)

    def store_fast_op(self, var_name: str) -> None:
        self.locals[var_name] = self.pop()

    def store_fast_store_fast_op(self, var_nums: int) -> None:
        idx1 = (var_nums >> 4)
        idx2 = (var_nums & 0x0F)

        name1 = self.code.co_varnames[idx1]
        name2 = self.code.co_varnames[idx2]

        v1 = self.data_stack[-1]
        v2 = self.data_stack[-2]

        self.locals[name2] = v2
        self.locals[name1] = v1

    def store_fast_load_fast_op(self, var_nums: int) -> None:
        self.locals[self.code.co_varnames[var_nums >> 4]] = self.pop()
        self.push(self.locals[self.code.co_varnames[var_nums & 0x0F]])

    # ---------- const / return ----------
    def load_const_op(self, arg: tp.Any) -> None:
        self.push(arg)

    def return_value_op(self, arg: tp.Any) -> None:
        self.return_value = self.pop()

    def return_const_op(self, arg: tp.Any) -> None:
        self.return_value = arg

    def setup_annotations_op(self, arg: tp.Any) -> None:
        if "__annotations__" not in self.locals:
            self.locals["__annotations__"] = {}

    # ---------- MAKE_FUNCTION + attributes ----------
    def make_function_op(self, arg: int) -> None:
        code = self.pop()

        class FTProxy:
            def __init__(self, co: types.CodeType):
                self.__code__ = co
                self.__defaults__ = None
                self.__kwdefaults__ = None
                self.__annotations__ = {}

        sig_proxy = FTProxy(code)

        def f(*call_args: tp.Any, **call_kwargs: tp.Any) -> tp.Any:
            sig = sig_proxy
            bound_locals = bind_args(sig, *call_args, **call_kwargs)
            callee_locals = dict(self.locals)
            callee_locals.update(bound_locals)
            frame = Frame(code, self.builtins, self.globals, callee_locals)
            return frame.run()

        self.push(f)

    def set_function_attribute_op(self, flag: int) -> None:
        func = self.pop()
        value = self.pop()

        target = func
        if flag == 0x01:
            target.__defaults__ = None if value is None else tuple(value)
        elif flag == 0x02:
            target.__kwdefaults__ = None if value is None else dict(value)
        elif flag == 0x04:
            target.__annotations__ = value
        elif flag == 0x08:
            pass
        self.push(func)

    def call_function_ex_op(self, flags: int) -> None:
        if flags == 1:
            kwargs = self.pop()
            posargs = self.pop()
            function = self.pop()
            if bool(posargs):
                self.push(function(*posargs, **kwargs))
            else:
                self.push(function(**kwargs))
        else:
            posargs = self.pop()
            function = self.pop()
            self.push(function(*posargs))

    def store_name_op(self, name: str) -> None:
        self.locals[name] = self.pop()

    # ---------- builders ----------
    def build_tuple_op(self, count: int) -> None:
        self.push(tuple(self.popn(count)))

    def build_list_op(self, count: int) -> None:
        self.push(list(self.popn(count)))

    def build_set_op(self, count: int) -> None:
        self.push(set(self.popn(count)))

    def build_map_op(self, count: int) -> None:
        vals = self.popn(2 * count)
        m = {vals[2 * i]: vals[2 * i + 1] for i in range(count)}
        self.push(m)

    def build_const_key_map_op(self, count: int) -> None:
        keys = self.pop()
        values = self.popn(count)
        m = {keys[i]: values[i] for i in range(count)}
        self.push(m)

    def build_string_op(self, count: int) -> None:
        self.push("".join(self.popn(count)))

    # ---------- list/set/dict updates ----------
    def list_append_op(self, i: int) -> None:
        v = self.pop()
        self.data_stack[-i].append(v)

    def list_extend_op(self, i: int):
        lst = self.pop()
        list.extend(self.data_stack[-i], lst)

    def set_add_op(self, i: int) -> None:
        v = self.pop()
        self.data_stack[-i].add(v)

    def map_add_op(self, i: int) -> None:
        value = self.pop()
        key = self.pop()
        self.data_stack[-i][key] = value

    def set_update_op(self, i: int) -> None:
        s = self.pop()
        self.data_stack[-i].update(s)

    def dict_update_op(self, i: int) -> None:
        m = self.pop()
        self.data_stack[-i].update(m)

    def dict_merge_op(self, i: int) -> None:
        m = self.pop()
        self.data_stack[-i].update(m)

    # ---------- slicing ----------
    def build_slice_op(self, argc: int) -> None:
        if argc == 2:
            start, stop = self.popn(2)
            self.push(slice(start, stop))
        elif argc == 3:
            start, stop, step = self.popn(3)
            self.push(slice(start, stop, step))

    def extended_arg_op(self, arg: tp.Any) -> None:
        pass

    # ---------- formatting ----------
    def convert_value_op(self, oparg: int) -> None:
        v = self.pop()
        if oparg == 0:
            self.push(v)
        elif oparg == 1:
            self.push(str(v))
        elif oparg == 2:
            self.push(repr(v))
        elif oparg == 3:
            self.push(ascii(v))
        else:
            self.push(v)

    def format_simple_op(self, arg: tp.Any) -> None:
        v = self.pop()
        self.push(v.__format__(""))

    def format_with_spec_op(self, arg: tp.Any) -> None:
        spec = self.pop()
        v = self.pop()
        self.push(v.__format__(spec))

    # ---------- comparisons ----------
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
        comp = ops.get(op)
        if comp is None:
            raise NameError
        self.push(comp(lhs, rhs))

    def contains_op_op(self, invert: int) -> None:
        lhs, rhs = self.popn(2)
        self.push(bool((lhs in rhs) ^ invert))

    def is_op_op(self, invert: int) -> None:
        lhs, rhs = self.popn(2)
        self.push(bool((lhs is rhs) ^ invert))

    # ---------- deletes / attrs / globals ----------
    def delete_name_op(self, namei: str) -> None:
        del self.locals[namei]

    def unpack_sequence_op(self, count: int):
        seq = self.pop()
        self.push(*seq[-1: -count - 1: -1])

    def delete_global_op(self, namei: str) -> None:
        del self.globals[namei]

    def delete_fast_op(self, namei: str) -> None:
        del self.locals[namei]

    def load_attr_op(self, namei: int) -> None:
        obj = self.pop()
        name = self.code.co_names[namei >> 1]
        attr = getattr(obj, name)
        if (namei & 1) == 0:
            self.push(attr)
        else:
            self.push(attr, None)

    def store_attr_op(self, name: str) -> None:
        val, obj = self.popn(2)
        setattr(obj, name, val)

    def delete_attr_op(self, name: str) -> None:
        obj = self.pop()
        delattr(obj, name)

    def store_global_op(self, namei: str) -> None:
        self.globals[namei] = self.pop()

    # ---------- jumps (offset-based) ----------
    def _jump_to_offset(self, target_offset: int) -> None:
        try:
            self.next_pc = self._off2idx[target_offset]
        except KeyError:
            raise RuntimeError(f"Bad jump target offset: {target_offset}")

    def jump_forward_op(self, target_offset: int) -> None:
        self._jump_to_offset(target_offset)

    def jump_backward_op(self, target_offset: int) -> None:
        self._jump_to_offset(target_offset)

    def jump_backward_no_interrupt_op(self, target_offset: int) -> None:
        self._jump_to_offset(target_offset)

    def pop_jump_if_true_op(self, target_offset: int) -> None:
        v = self.pop()
        if not isinstance(v, bool):
            raise TypeError("POP_JUMP_IF_TRUE requires exact bool")
        if v:
            self._jump_to_offset(target_offset)

    def pop_jump_if_false_op(self, target_offset: int) -> None:
        v = self.pop()
        if not isinstance(v, bool):
            raise TypeError("POP_JUMP_IF_FALSE requires exact bool")
        if not v:
            self._jump_to_offset(target_offset)

    def pop_jump_if_none_op(self, target_offset: int) -> None:
        if self.pop() is None:
            self._jump_to_offset(target_offset)

    def pop_jump_if_not_none_op(self, target_offset: int) -> None:
        if self.pop() is not None:
            self._jump_to_offset(target_offset)

    def for_iter_op(self, target_offset: int) -> None:
        it = self.top()
        try:
            value = next(it)
        except StopIteration:
            self.push(None)  # ?
            self._jump_to_offset(target_offset)
        else:
            self.push(value)  # stack: ..., iter, value

    def import_name_op(self, namei: str) -> None:
        level, fromlist = self.popn(2)
        self.push(__import__(namei, self.globals, self.locals, fromlist, level))

    def import_star_op(self, arg: tp.Any) -> None:
        mod = self.pop()
        for attr in dir(mod):
            if attr[0] != '_':
                self.locals[attr] = getattr(mod, attr)

    def import_from_op(self, namei: str) -> None:
        mod = self.top()
        self.push(getattr(mod, namei))

    def load_assertion_error_op(self, arg: tp.Any) -> None:
        self.push(AssertionError)


class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> tp.Any:
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()['__builtins__'], globals_context, globals_context)
        return frame.run()


def bind_args(func, *args: tp.Any, **kwargs: tp.Any) -> dict[str, tp.Any]:
    """
    Your provided binder, unchanged except type loosened (we only read __code__,
    __defaults__, __kwdefaults__).
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

    pos_defaults = getattr(func, "__defaults__", None) or ()
    kw_defaults = getattr(func, "__kwdefaults__", None) or {}

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
