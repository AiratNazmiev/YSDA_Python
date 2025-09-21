import typing as tp


def convert_to_common_type(data: list[tp.Any]) -> list[tp.Any]:
    """
    Takes list of multiple types' elements and convert each element to common type according to given rules
    :param data: list of multiple types' elements
    :return: list with elements converted to common type
    """
    if any(type(x) in (list, tuple) for x in data):
        result = [x if x not in (None, "") else [] for x in data]
        return [[x] if type(x) not in (list, tuple) else list(x) for x in result]

    if any(type(x) is float for x in data):
        return [float(x) if x not in (None, "") else 0.0 for x in data]

    if any(type(x) is bool for x in data):
        return [bool(x) if x not in (None, "") else False for x in data]

    if any(type(x) is int for x in data):
        return [int(x) if x not in (None, "") else 0 for x in data]

    if any(type(x) is str for x in data):
        return [x if x is not None else "" for x in data]

    return [""] * len(data)
