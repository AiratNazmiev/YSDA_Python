from pathlib import Path
import subprocess
import os


def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    text = file_in.read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line != ""]

    def key_func(line: str) -> tuple[int, str]:
        first_col, second_col = line.split("\t", 1)
        return int(second_col), first_col

    rows.sort(key=key_func)

    file_out.write_text("".join(f"{row}\n" for row in rows))


def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    cmd = ["sort", "-t", "\t", "-k2,2n", "-k1,1"]

    env = dict(os.environ)
    env["LC_ALL"] = "C"

    with file_in.open("rb") as fin, file_out.open("wb") as fout:
        subprocess.run(cmd, stdin=fin, stdout=fout, stderr=subprocess.PIPE, check=True, env=env)
