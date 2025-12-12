from pathlib import Path
import os
import subprocess


def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    rows: list[tuple[str, int]] = []
    for line in file_in.read_text(encoding="utf-8").splitlines():
        first, second = line.split("\t", 1)
        rows.append((first, int(second)))

    rows.sort(key=lambda r: (r[1], r[0]))

    with file_out.open("w", newline="") as f_out:
        for first, second in rows:
            f_out.write(f"{first}\t{second}\n")

def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    cmd = ["sort", "-t", "\t", "-k2,2n", "-k1,1"]
    with file_in.open("r") as fin, file_out.open("w") as fout:
        subprocess.run(cmd, stdin=fin, stdout=fout, stderr=subprocess.PIPE, check=True)
