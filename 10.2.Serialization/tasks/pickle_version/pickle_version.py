import dataclasses
import pickletools


@dataclasses.dataclass
class PickleVersion:
    is_new_format: bool
    version: int


def get_pickle_version(data: bytes) -> PickleVersion:
    """
    Returns used protocol version for serialization.

    :param data: serialized object in pickle format.
    :return: protocol version.
    """
    version = next(pickletools.genops(data))[1]

    if version is None or version < 2:
        version = -1
        is_new_format = False
    else:
        version = version
        is_new_format = True

    return PickleVersion(is_new_format, version)
