from typing import Protocol, TypeVar, Optional

T_co = TypeVar("T_co", covariant=True)


class Gettable(Protocol[T_co]):
    def __getitem__(self, index: int) -> T_co:
        ...

    def __len__(self) -> int:
        ...


def get(container: Gettable[T_co], index: int) -> Optional[T_co]:
    if container:
        return container[index]

    return None
