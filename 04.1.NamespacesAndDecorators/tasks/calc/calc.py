import sys
import math
from typing import Any

PROMPT = '>>> '


def run_calc(context: dict[str, Any] | None = None) -> None:
    """Run interactive calculator session in specified namespace"""
    context = {'__builtins__': {}} if context is None else context
    while True:
        sys.stdout.write(PROMPT)
        data = sys.stdin.readline()
        if data:
            sys.stdout.write(f"{str(eval(data, context))}\n")
        else:
            break

    sys.stdout.write('\n')


if __name__ == '__main__':
    context = {'math': math}
    run_calc(context)
