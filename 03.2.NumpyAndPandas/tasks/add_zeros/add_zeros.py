import numpy as np
import numpy.typing as npt


def add_zeros(x: npt.NDArray[np.int_]) -> npt.NDArray[np.int_]:
    """
    Add zeros between values of given array
    :param x: array,
    :return: array with zeros inserted
    """
    #return np.stack((x, np.zeros_like(x))).flatten("F")[:-1]
    return np.insert(x, np.arange(1, x.shape[0]), values=0.)
