import sys
import math
from typing import Any

PROMPT = '>>> '


def run_calc(context: dict[str, Any] | None = None) -> None:
    """Run interactive calculator session in specified namespace"""


if __name__ == '__main__':
    context = {'math': math}
    run_calc(context)
