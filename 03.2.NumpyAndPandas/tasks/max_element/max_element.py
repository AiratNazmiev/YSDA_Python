import numpy as np
import numpy.typing as npt


def max_element(array: npt.NDArray[np.int_]) -> int | None:
    """
    Return max element before zero for input array.
    If appropriate elements are absent, then return None
    :param array: array,
    :return: max element value or None
    """
    if array.shape[0] < 2:
        return None

    mask = (array[:-1] == 0)

    x = array[1:][mask]

    if x.shape[0] == 0:
        return None

    return int(np.max(x))
