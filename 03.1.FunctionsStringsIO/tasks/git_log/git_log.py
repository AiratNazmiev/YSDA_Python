import typing as tp


def reformat_git_log(inp: tp.IO[str], out: tp.IO[str]) -> None:
    """Reads git log from `inp` stream, reformats it and prints to `out` stream

    Expected input format: `<sha-1>\t<date>\t<author>\t<email>\t<message>`
    Output format: `<first 7 symbols of sha-1>.....<message>`
    """
    line_width = 80
    sha_prefix = 7

    for line in inp:
        line = line.rstrip('\n')
        sha, *_, msg = line.split('\t')
        prefix = sha[:sha_prefix]

        max_msg_len = line_width - sha_prefix
        if len(msg) > max_msg_len:
            msg = msg[:max_msg_len]

        dots = line_width - sha_prefix - len(msg)
        out.write(f"{prefix}{'.' * dots}{msg}\n")
