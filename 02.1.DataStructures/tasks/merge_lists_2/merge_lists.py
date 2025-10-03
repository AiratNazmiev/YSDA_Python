import typing as tp
import heapq

MAX_VALUE = 2**63 - 1

def merge(seq: tp.Sequence[tp.Sequence[int]]) -> list[int]:
    """
    :param seq: sequence of sorted sequences
    :return: merged sorted list
    """
    total_len = sum(len(s) for s in seq)
    min_heap: list[tuple[int, int, int]] = \
        [(s[0], seq_idx, 0) for seq_idx, s in enumerate(seq) if len(s) > 0]
    heapq.heapify(min_heap)
    result: list[int] = []

    for _ in range(total_len):
        curr_min, curr_seq_idx, curr_idx = heapq.heappop(min_heap)
        result.append(curr_min)
        if curr_idx + 1 < len(seq[curr_seq_idx]):
            heapq.heappush(min_heap, (seq[curr_seq_idx][curr_idx + 1], curr_seq_idx, curr_idx + 1))

    return result
