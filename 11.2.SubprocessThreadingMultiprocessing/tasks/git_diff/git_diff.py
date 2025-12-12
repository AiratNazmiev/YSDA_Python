import subprocess
from pathlib import Path


def get_changed_dirs(git_path: Path, from_commit_hash: str, to_commit_hash: str) -> set[Path]:
    """
    Get directories which content was changed between two specified commits
    :param git_path: path to git repo directory
    :param from_commit_hash: hash of commit to do diff from
    :param to_commit_hash: hash of commit to do diff to
    :return: sequence of changed directories between specified commits
    """
    output = subprocess.run(
        ["git", "diff", from_commit_hash, to_commit_hash, "--dirstat"],
        cwd=git_path,
        capture_output=True
    )
    changed_dirs = set(map(lambda x: git_path/Path(x.strip('/')), output.stdout.decode().split()[1::2]))

    return changed_dirs
