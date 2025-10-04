import string
from collections import defaultdict
import heapq


def normalize(
        text: str
        ) -> str:
    """
    Removes punctuation and digits and convert to lower case
    :param text: text to normalize
    :return: normalized query
    """
    return text.translate({ord(c): None for c in string.digits + string.punctuation}).lower()


def get_words(
        query: str
        ) -> list[str]:
    """
    Split by words and leave only words with letters greater than 3
    :param query: query to split
    :return: filtered and split query by words
    """
    return [w for w in query.split() if len(w) > 3]


def build_index(
        banners: list[str]
        ) -> dict[str, list[int]]:
    """
    Create index from words to banners ids with preserving order and without repetitions
    :param banners: list of banners for indexation
    :return: mapping from word to banners ids
    """
    index: dict[str, list[int]] = defaultdict(list)

    for idx, banner in enumerate(banners):
        words = get_words(normalize(banner))
        words_in_banner = set()
        for w in words:
            if w not in words_in_banner:
                index[w].append(idx)
                words_in_banner.add(w)

    return dict(index)


def get_banner_indices_by_query(
        query: str,
        index: dict[str, list[int]]
        ) -> list[int]:
    """
    Extract banners indices from index, if all words from query contains in indexed banner
    :param query: query to find banners
    :param index: index to search banners
    :return: list of indices of suitable banners
    """
    words = get_words(normalize(query))
    if not words:
        return []

    word_banners: list[list[int]] = []
    for w in words:
        w_list = index.get(w)
        if not w_list:
            return []
        word_banners.append(w_list)

    num_w = len(word_banners)
    min_heap = []

    for idx, w_list in enumerate(word_banners):
        heapq.heappush(min_heap, (w_list[0], idx, 0))

    result = []
    curr_b_idx = None
    curr_w_cnt = 0

    while min_heap:
        b_idx, w_idx, idx = heapq.heappop(min_heap)

        if curr_b_idx is None or b_idx != curr_b_idx:
            if curr_b_idx is not None and curr_w_cnt == num_w:
                result.append(curr_b_idx)

            curr_b_idx = b_idx
            curr_w_cnt = 1
        else:
            curr_w_cnt += 1

        if idx + 1 < len(word_banners[w_idx]):
            heapq.heappush(min_heap, (word_banners[w_idx][idx + 1], w_idx, idx + 1))

    if curr_b_idx is not None and curr_w_cnt == num_w:
        result.append(curr_b_idx)

    return result

#########################
# Don't change this code
#########################

def get_banners(
        query: str,
        index: dict[str, list[int]],
        banners: list[str]
        ) -> list[str]:
    """
    Extract banners matched to queries
    :param query: query to match
    :param index: word-banner_ids index
    :param banners: list of banners
    :return: list of matched banners
    """
    indices = get_banner_indices_by_query(query, index)
    return [banners[i] for i in indices]

#########################
