import typing as tp
# from collections import defaultdict


# def revert(dct: tp.Mapping[str, str]) -> dict[str, list[str]]:
#     """
#     :param dct: dictionary to revert in format {key: value}
#     :return: reverted dictionary {value: [key1, key2, key3]}
#     """
#     result = defaultdict(list)
#     for k, v in dct.items():
#         result[v].append(k)

#     return dict(result)
def revert(dct: tp.Mapping[str, str]) -> dict[str, list[str]]:
    """
    :param dct: dictionary to revert in format {key: value}
    :return: reverted dictionary {value: [key1, key2, key3]}
    """
    result = {}
    for k, v in dct.items():
        k_list = result.get(v)
        if k_list is not None:
            result[v].append(k)
        else:
            result[v] = [k]

    return result
