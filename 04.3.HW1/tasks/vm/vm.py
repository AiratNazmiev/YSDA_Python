"""
Simplified VM code which works for some cases.
You need extend/rewrite code to pass all cases.
"""

import builtins
import dis
import types
import typing as tp


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

    def make_function_op(self, arg: int) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-MAKE_FUNCTION
        """
        code = self.pop()  # the code associated with the function (at TOS1)

        # TODO: use arg to parse function defaults

        def f(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
            # TODO: parse input arguments using code attributes such as co_argcount

            parsed_args: dict[str, tp.Any] = {}
            f_locals = dict(self.locals)
            f_locals.update(parsed_args)

            frame = Frame(code, self.builtins, self.globals, f_locals)  # Run code in prepared environment
            return frame.run()

        self.push(f)

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

class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> None:
        """
        :param code_obj: code for interpreting
        """
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()['__builtins__'], globals_context, globals_context)
        return frame.run()
