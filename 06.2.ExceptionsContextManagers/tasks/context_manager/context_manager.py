from contextlib import contextmanager
from typing import Iterator, TextIO, Type
import sys
import traceback


@contextmanager
def supresser(*types_: Type[BaseException]) -> Iterator[None]:
    try:
        yield None
    except Exception as exc:
        type_exc, value_exc, trace_exc = sys.exc_info()
        if type_exc not in types_:
            raise exc


@contextmanager
def retyper(type_from: Type[BaseException], type_to: Type[BaseException]) -> Iterator[None]:
    try:
        yield None
    except Exception as exc:
        type_exc, value_exc, trace_exc = sys.exc_info()
        if type_from == type_exc:
            if value_exc is not None:
                raise type_to(*value_exc.args)
            else:
                raise type_to
        else:
            raise exc


@contextmanager
def dumper(stream: TextIO | None = None) -> Iterator[None]:
    try:
        yield None
    except Exception:
        type_exc, value_exc, trace_exc = sys.exc_info()
        if stream is None:
            sys.stderr.write(traceback.format_exception_only(type_exc, value_exc)[0])
        else:
            stream.write(traceback.format_exception_only(type_exc, value_exc)[0])
        raise
