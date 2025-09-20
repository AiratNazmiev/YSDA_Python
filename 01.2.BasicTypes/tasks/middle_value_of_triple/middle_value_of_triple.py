def get_middle_value(a: int, b: int, c: int) -> int:
    """
    Takes three values and returns middle value.
    """
    if (a >= b or c >= b) and (b >= c or b >= a):
        return b
    elif (a >= c or b >= c) and (c >= b or c >= a):
        return c
    else:
        return a
