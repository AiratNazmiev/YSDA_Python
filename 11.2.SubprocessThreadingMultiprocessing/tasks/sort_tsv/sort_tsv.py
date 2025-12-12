from pathlib import Path
import subprocess


def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    lines = file_in.read_text(encoding="utf-8").splitlines()

    def key_func(line: str) -> tuple[int, str]:
        first_col, second_col = line.split("\t", 1)
        return int(second_col), first_col

    lines.sort(key=key_func)

    file_out.write_text("".join(f"{line}\n" for line in lines))


def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    cmd = ["sort", "-t", "\t", "-k2,2n", "-k1,1", str(file_in)]

    with file_out.open("w", newline="") as fout:
        subprocess.run(cmd, stdout=fout, check=True)
