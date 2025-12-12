from pathlib import Path
import os
import subprocess


def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    file_in_path = Path(file_in)
    file_out_path = Path(file_out)

    with file_in_path.open("r", encoding="utf-8", newline="") as f_in:
        lines = f_in.readlines()

    def sort_key(line: str) -> tuple[int, str]:
        first, second = line.rstrip("\n").split("\t", 1)
        return int(second), first

    lines.sort(key=sort_key)

    with file_out_path.open("w", encoding="utf-8", newline="") as f_out:
        f_out.writelines(lines)

def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    file_in_path = Path(file_in)
    file_out_path = Path(file_out)

    cmd = [
        "sort",
        "-t",
        "\t",
        "-k2,2n",
        "-k1,1",
        str(file_in_path),
    ]

    env = os.environ.copy()
    env.setdefault("LC_ALL", "C")

    with file_out_path.open("w", encoding="utf-8", newline="") as f_out:
        subprocess.run(cmd, check=True, stdout=f_out, env=env)
