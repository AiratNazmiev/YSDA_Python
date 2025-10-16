import typing as tp
from pathlib import Path
import sys
import io


def tail(filename: Path, lines_amount: int = 10, output: tp.IO[bytes] | None = None) -> None:
    """
    :param filename: file to read lines from (the file can be very large)
    :param lines_amount: number of lines to read
    :param output: stream to write requested amount of last lines from file
                   (if nothing specified stdout will be used)
    """
    if lines_amount <= 0:
        return

    CHUNK = 2**16
    newline = ord(b'\n')

    with filename.open('rb') as f:
        f.seek(0, 2)
        size = f.tell()
        if size == 0:
            return

        f.seek(size - 1)
        last_byte = f.read(1)
        skip_last_newline = (last_byte == b'\n')

        remaining = lines_amount
        start_pos = 0
        pos = size

        buffer = bytearray(CHUNK)
        mv = memoryview(buffer)

        while pos > 0 and remaining > 0:
            read_size = CHUNK if pos >= CHUNK else pos
            pos -= read_size
            f.seek(pos)
            n = f.readinto(mv[:read_size])

            for i in range(n - 1, -1, -1):
                if mv[i] == newline:
                    if skip_last_newline:
                        skip_last_newline = False
                        continue
                    remaining -= 1
                    if remaining == 0:
                        start_pos = pos + i + 1
                        break

        if remaining > 0:
            start_pos = 0

        f.seek(start_pos)

        if output is not None:
            while True:
                n = f.readinto(mv)
                if not n:
                    break
                output.write(mv[:n])
        else:
            text_out = sys.stdout
            wrapper = io.TextIOWrapper(f, encoding='utf-8', errors='replace', newline=None)
            wrapper.seek(start_pos)
            while True:
                chunk = wrapper.read(CHUNK)
                if not chunk:
                    break
                text_out.write(chunk)
