import enum


class Status(enum.Enum):
    NEW = 0
    EXTRACTED = 1
    FINISHED = 2


def extract_alphabet(
        graph: dict[str, set[str]]
        ) -> list[str]:
    """
    Extract alphabet from graph
    :param graph: graph with partial order
    :return: alphabet
    """
    alphabet: list[str] = []
    status: dict[str, Status] = {v: Status.NEW for v in graph}

    for v in graph:
        if status[v] == Status.FINISHED:
            continue

        stack: list[str] = [v]

        while stack:
            to = stack.pop()

            if status[to] == Status.NEW:
                status[to] = Status.EXTRACTED
                stack.append(to)
                for ch in graph[to]:
                    if status[ch] == Status.NEW:
                        stack.append(ch)
                    elif status[ch] == Status.EXTRACTED:
                        raise ValueError("There is a cycle in graph")
            elif status[to] == Status.EXTRACTED:
                status[to] = Status.FINISHED
                alphabet.append(to)

    alphabet.reverse()

    return alphabet


def build_graph(
        words: list[str]
        ) -> dict[str, set[str]]:
    """
    Build graph from ordered words. Graph should contain all letters from words
    :param words: ordered words
    :return: graph
    """
    graph: dict[str, set[str]] = {}

    for word in words:
        for char in word:
            if char not in graph:
                graph[char] = set()

    for w1, w2 in zip(words[:-1], words[1:]):
        for c1, c2 in zip(w1, w2):
            if c1 != c2:
                graph[c1].add(c2)
                break

    return graph


#########################
# Don't change this code
#########################

def get_alphabet(
        words: list[str]
        ) -> list[str]:
    """
    Extract alphabet from sorted words
    :param words: sorted words
    :return: alphabet
    """
    graph = build_graph(words)
    return extract_alphabet(graph)

#########################
