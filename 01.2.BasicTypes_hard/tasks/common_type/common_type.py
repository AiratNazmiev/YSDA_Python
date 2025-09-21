def get_common_type(type1: type, type2: type) -> type:
    """
    Calculate common type according to rule, that it must have the most adequate interpretation after conversion.
    Look in tests for adequacy calibration.
    :param type1: one of [bool, int, float, complex, list, range, tuple, str] types
    :param type2: one of [bool, int, float, complex, list, range, tuple, str] types
    :return: the most concrete common type, which can be used to convert both input values
    """
    if type1 is type2:
        return type1 if type1 is not range else tuple

    if str in (type1, type2):
        return str

    numeric = (bool, int, float, complex)
    container = (list, tuple, range)

    if type1 in numeric and type2 in numeric:
        return numeric[max(numeric.index(type1), numeric.index(type2))]

    if type1 in container and type2 in container:
        if list in (type1, type2):
            return list

        # if any of containers is tuple or both are range
        return tuple

    # if any of types is container
    if (type1 in container) ^ (type2 in container):
        return str

    return object  # it's not accessible
