# mypy: ignore-errors

import inspect
import os
import re
import subprocess
import tempfile
import typing as tp

import typy_protocol
from typy_protocol import get


def pyrefly_file(filepath: str) -> tuple[str, str, int]:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned_content = re.sub(r'#\s*type:\s*ignore\s*', '', content)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(cleaned_content)
        temp_path = temp_file.name

    try:
        cmd: list[str] = ["pyrefly", "check", "--output-format", "min-text", temp_path]
        result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        os.unlink(temp_path)

    return result.stdout, result.stderr, result.returncode


def check_annotations(func):
    for p, value in inspect.signature(func).parameters.items():
        if p == "self":
            assert value.annotation == inspect.Signature.empty, f"Parameter {p} should not have annotation"
        else:
            assert value.annotation != inspect.Signature.empty, f"Parameter {p} does not have annotation"
            assert value.annotation != tp.Any, f"Parameter {p} has prohibited Any annotation"

    assert inspect.signature(func).return_annotation != inspect.Signature.empty, "Return does not have annotation"
    assert inspect.signature(func).return_annotation != tp.Any, "Return has prohibited Any annotation"


def check_func(module, test_case, is_success):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as fp:
        fp.write("import typing as tp")
        fp.write("\n")
        fp.write("import numbers")
        fp.write("\n")
        fp.write("import abc")
        fp.write("\n\n")
        fp.write(inspect.getsource(module))
        fp.write("\n")
        fp.write(inspect.getsource(test_case))
        fp.write("\n")
        fp.flush()

        normal_report, error_report, exit_status = pyrefly_file(fp.name)
        print(f"Report:\n{normal_report}\n{error_report}")
        result_success_status = exit_status == 0

        assert result_success_status is is_success, \
            f"Typechecker should return {is_success}, but result {result_success_status}"


def case1() -> None:
    class A:
        def __init__(self, a: str):
            self._a = a

        def __getitem__(self, item: int) -> str:
            return self._a[item]

        def __len__(self) -> int:
            return len(self._a)

    get(A("hello"), 4)


def case2() -> None:
    class A:
        def __init__(self, a: str):
            self._a = a

        def __getitem__(self, item: int) -> str:
            return self._a[item]

    get(A("hello"), 4) # type: ignore


def case3() -> None:
    class A:
        def __getitem__(self, item: int) -> bool:
            return True

        def __len__(self) -> int:
            return 0

    get(A(), 4)


def test_protocol() -> None:

    check_annotations(get)

    check_func(typy_protocol, case1, True)
    check_func(typy_protocol, case2, False)
    check_func(typy_protocol, case3, True)
