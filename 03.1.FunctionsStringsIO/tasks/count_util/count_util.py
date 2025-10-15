import re


def count_util(text: str, flags: str | None = None) -> dict[str, int]:
    """
    :param text: text to count entities
    :param flags: flags in command-like format - can be:
        * -m stands for counting characters
        * -l stands for counting lines
        * -L stands for getting length of the longest line
        * -w stands for counting words
    More than one flag can be passed at the same time, for example:
        * "-l -m"
        * "-lLw"
    Ommiting flags or passing empty string is equivalent to "-mlLw"
    :return: mapping from string keys to corresponding counter, where
    keys are selected according to the received flags:
        * "chars" - amount of characters
        * "lines" - amount of lines
        * "longest_line" - the longest line length
        * "words" - amount of words
    """
    flags = "-mlLw" if not flags else flags
    flags_list = [c for s in re.findall(r"-(\w+)", flags) for c in s]
    result = {}
    if 'm' in flags_list:
        result["chars"] = len(text)
    if 'l' in flags_list:
        result["lines"] = text.count('\n')
    if 'L' in flags_list:
        result["longest_line"] = max(map(len, text.split('\n')))
    if 'w' in flags_list:
        result["words"] = len(text.split())

    return result
