import numpy as np
import numpy.typing as npt


def nonzero_product(matrix: npt.NDArray[np.int_]) -> int | None:
    """
    Compute product of nonzero diagonal elements of matrix
    If all diagonal elements are zeros, then return None
    :param matrix: array,
    :return: product value or None
    """
    diag = np.diagonal(matrix)
    nz_diag = diag[np.nonzero(diag)]
    if len(nz_diag) == 0:
        return None
    else:
        return int(np.prod(nz_diag))
