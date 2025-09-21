def merge_iterative(lst_a: list[int], lst_b: list[int]) -> list[int]:
    """
    Merge two sorted lists in one sorted list
    :param lst_a: first sorted list
    :param lst_b: second sorted list
    :return: merged sorted list
    """
    idx_a = 0
    idx_b = 0
    result = []
    while idx_a != len(lst_a) and idx_b != len(lst_b):
        if lst_a[idx_a] < lst_b[idx_b]:
            result.append(lst_a[idx_a])
            idx_a += 1
        else:
            result.append(lst_b[idx_b])
            idx_b += 1

    if idx_a == len(lst_a):
        result.extend(lst_b[idx_b:])
    else:
        result.extend(lst_a[idx_a:])

    return result


def merge_sorted(lst_a: list[int], lst_b: list[int]) -> list[int]:
    """
    Merge two sorted lists in one sorted list using `sorted`
    :param lst_a: first sorted list
    :param lst_b: second sorted list
    :return: merged sorted list
    """
    return sorted(lst_a + lst_b)
