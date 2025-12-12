from pathlib import Path
import subprocess
import os


def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    lines = map(lambda x: x.split(), file_in.read_text(encoding="utf-8").splitlines())
    lines_sorted = sorted(
        lines,
        key=lambda x: (int(x[1]), x[0])
    )

    with open(file_out, 'w') as f:
        f.write(''.join([f"{row[0]}\t{row[1]}\n" for row in lines_sorted]) + '\n')


def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    cmd = ["sort", "-t", "\t", "-k2,2n", "-k1,1", str(file_in)]

    with file_out.open("w", encoding="utf-8", newline="") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
