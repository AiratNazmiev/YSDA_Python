import typing as tp


def traverse_dictionary_immutable(
        dct: tp.Mapping[str, tp.Any],
        prefix: str = "") -> list[tuple[str, int]]:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :param prefix: prefix for key used for passing total path through recursion
    :return: list with pairs: (full key from root to leaf joined by ".", value)
    """
    result: list[tuple[str, int]] = []

    def dfs(dct, prefix):
        for k, v in dct.items():
            new_prefix = f"{prefix}.{k}" if prefix != "" else k
            if isinstance(v, tp.Mapping):
                dfs(v, prefix=new_prefix)
            else:
                result.append((new_prefix, v))

    dfs(dct, prefix)

    return result


def traverse_dictionary_mutable(
        dct: tp.Mapping[str, tp.Any],
        result: list[tuple[str, int]],
        prefix: str = "") -> None:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :param result: list with pairs: (full key from root to leaf joined by ".", value)
    :param prefix: prefix for key used for passing total path through recursion
    :return: None
    """
    for k, v in dct.items():
        new_prefix = f"{prefix}.{k}" if prefix != "" else k
        if isinstance(v, tp.Mapping):
            traverse_dictionary_mutable(v, result, new_prefix)
        else:
            result.append((new_prefix, v))



def traverse_dictionary_iterative(
        dct: tp.Mapping[str, tp.Any]
        ) -> list[tuple[str, int]]:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :return: list with pairs: (full key from root to leaf joined by ".", value)
    """
    result: list[tuple[str, int]] = []
    stack: list[tuple[tp.Mapping[str, tp.Any], str]] = [(dct, "")]

    while stack:
        cur_dct, cur_prefix = stack.pop()
        for k, v in cur_dct.items():
            new_prefix = f"{cur_prefix}.{k}" if cur_prefix != "" else k
            if isinstance(v, tp.Mapping):
                stack.append((v, new_prefix))
            else:
                result.append((new_prefix, v))

    return result
