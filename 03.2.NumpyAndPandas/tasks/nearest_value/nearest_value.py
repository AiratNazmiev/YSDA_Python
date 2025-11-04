import numpy as np
import numpy.typing as npt


def nearest_value(matrix: npt.NDArray[np.float64], value: float) -> float | None:
    """
    Find nearest value in matrix.
    If matrix is empty return None
    :param matrix: input matrix
    :param value: value to find
    :return: nearest value in matrix or None
    """
    return float(matrix.flat[np.argmin(np.abs(matrix - value))]) if matrix.size != 0 else None
