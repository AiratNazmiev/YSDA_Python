import sys
import math
from typing import Any

PROMPT = '>>> '


def run_calc(context: dict[str, Any] | None = None) -> None:
    """Run interactive calculator session in specified namespace"""
    context = {'__builtins__': {}} if context is None else context
    while True:
        print(PROMPT, flush=True, end='')
        data = sys.stdin.readline()
        if data:
            print(str(eval(data, context)))
        else:
            print()
            break

if __name__ == '__main__':
    context = {'math': math}
    run_calc(context)
