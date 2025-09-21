def filter_list_by_list(lst_a: list[int] | range, lst_b: list[int] | range) -> list[int]:
    """
    Filter first sorted list by other sorted list
    :param lst_a: first sorted list
    :param lst_b: second sorted list
    :return: filtered sorted list
    """
    idx_a = 0
    idx_b = 0
    result = []

    while idx_a != len(lst_a) and idx_b != len(lst_b):
        if lst_a[idx_a] > lst_b[idx_b]:
            idx_b += 1
        elif lst_a[idx_a] == lst_b[idx_b]:
            idx_a += 1
        else:
            result.append(lst_a[idx_a])
            idx_a += 1

    if idx_a != len(lst_a):
        result.extend(lst_a[idx_a:])

    return result
