import copy

class LifeGame(object):
    """
    Class for Game life
    """
    def __init__(self, data: list[list[int]]) -> None:
        self._map = copy.deepcopy(data)
        self.y_max = len(data)
        self.x_max = len(data[0])

    def _get_neighbours(self, i: int, j: int):
        neighbours = []

        for y in range(max(0, j - 1), min(self.y_max, j + 2)):
            for x in range(max(0, i - 1), min(self.x_max, i + 2)):
                if x == y:
                    continue

                neighbours.append(self._map[y][x])
        return neighbours

    def _step(self) -> None:
        prev_map = copy.deepcopy(self._map)

        for y in range(self.y_max):
            for x in range(self.x_max):
                cell = prev_map[y][x]

                if cell == 1:
                    self._map[y][x] = 1
                    continue

                fish_n = 0
                shrimp_n = 0
                for ny in range(max(0, y - 1), min(self.y_max, y + 2)):
                    for nx in range(max(0, x - 1), min(self.x_max, x + 2)):
                        if ny == y and nx == x:
                            continue
                        neighbour = prev_map[ny][nx]
                        match neighbour:
                            case 2:
                                fish_n += 1
                            case 3:
                                shrimp_n += 1

                match cell:
                    case 2:
                        self._map[y][x] = 2 if fish_n in (2, 3) else 0
                    case 3:
                        self._map[y][x] = 3 if shrimp_n in (2, 3) else 0
                    case 0:
                        if fish_n == 3:
                            self._map[y][x] = 2
                        elif shrimp_n == 3:
                            self._map[y][x] = 3
                        else:
                            self._map[y][x] = 0
                    case _:
                        self._map[y][x] = 0


    def get_next_generation(self) -> list[list[int]]:
        self._step()
        return self._map
