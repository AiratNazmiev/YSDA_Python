# mypy: ignore-errors

import enum
import subprocess
import tempfile

import pytest
import re
import typing as tp

import inspect

import typy_1_dummy
import typy_2_homo
import typy_3_hetero
import typy_4_in
import typy_5_call


def is_not_union(value):
    print(tp.get_origin(value))
    print(tp.get_origin(value) is tp.Optional)
    return tp.get_origin(value) is not tp.Union or (len(args := tp.get_args(value)) == 2 and type(None) in args)


def check_annotations(func: tp.Callable[..., tp.Any]) -> None:
    for p, value in inspect.signature(func).parameters.items():
        assert value.annotation != inspect.Signature.empty, f"Parameter {p} does not have annotation"
        assert value.annotation != tp.Any, f"Parameter {p} has prohibited Any annotation"
        assert is_not_union(value.annotation), f"Parameter {p} has prohibited Union annotation"

    assert inspect.signature(func).return_annotation != inspect.Signature.empty, "Return does not have annotation"
    assert inspect.signature(func).return_annotation != tp.Any, "Return has prohibited Any annotation"
    assert is_not_union(inspect.signature(func).return_annotation), "Return has prohibited Union annotation"


def pyrefly_file(filepath: str) -> tuple[str, str, int]:
    # Build pyrefly command
    cmd: list[str] = ["pyrefly", "check", "--output-format", "min-text", filepath]
    print(filepath)

    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def check(module: tp.Callable[..., tp.Any], test_case: str, is_success: bool) -> None:
    test_str = f"{inspect.getsource(module)}\n{test_case}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as fp:
        fp.write(test_str)
        fp.flush()
        normal_report, error_report, exit_status = pyrefly_file(fp.name)

    result_success_status = exit_status == 0
    message_status = {
        True: "success",
        False: "error"
    }
    print(f"==========================\n\n"
          f"===Expected status: {message_status[is_success]}===\n"
          f"===Result status: {message_status[result_success_status]}===\n"
          f"===Code:===\n{test_str}\n===Report:===\n{normal_report}\n{error_report}\n")
    assert result_success_status is is_success, \
        f"Typecheck result should be {message_status[is_success]}, " \
        f"but result is {message_status[result_success_status]}"


class Status(enum.Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


@pytest.mark.parametrize("module", [typy_1_dummy, typy_2_homo, typy_3_hetero, typy_4_in, typy_5_call])
def test_typy(module: tp.Any) -> None:
    check_annotations(module.f)
    sp = re.split("# (\\w+)", module.TEST_SAMPLES)[1:]
    assert sp
    for status, test_code in zip(sp[::2], sp[1::2]):
        if Status(status) == Status.SUCCESS:
            check(module, test_code, is_success=True)
        else:
            check(module, test_code, is_success=False)
