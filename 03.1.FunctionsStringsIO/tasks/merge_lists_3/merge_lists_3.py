import heapq
import typing as tp


def merge(input_streams: tp.Sequence[tp.IO[bytes]], output_stream: tp.IO[bytes]) -> None:
    """
    Merge input_streams in output_stream
    :param input_streams: list of input streams. Contains byte-strings separated by "\n". Nonempty stream ends with "\n"
    :param output_stream: output stream. Contains byte-strings separated by "\n". Nonempty stream ends with "\n"
    :return: None
    """
    min_heap = [(int(line), seq_idx) for seq_idx, s in enumerate(input_streams) if (line := s.readline())]
    heapq.heapify(min_heap)

    while min_heap:
        curr_min, curr_seq_idx = heapq.heappop(min_heap)
        output_stream.write(f"{curr_min}\n".encode())
        next_elem = input_streams[curr_seq_idx].readline()
        if next_elem:
            heapq.heappush(min_heap, (int(next_elem), curr_seq_idx))
