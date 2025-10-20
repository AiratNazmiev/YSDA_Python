import types
import dis
from collections import Counter


def count_operations(source_code: types.CodeType) -> dict[str, int]:
    """Count byte code operations in given source code.

    :param source_code: the bytecode operation names to be extracted from
    :return: operation counts
    """
    ops_cnt: Counter = Counter()
    instructions = dis.get_instructions(source_code)
    for cur_instruction in instructions:
        ops_cnt[cur_instruction.opname] += 1

        if isinstance(cur_instruction.argval, types.CodeType):
            inner_ops_cnt = count_operations(cur_instruction.argval)
            ops_cnt += inner_ops_cnt

    return ops_cnt
