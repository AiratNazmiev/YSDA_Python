from collections.abc import Sequence


def find_median(nums1: Sequence[int], nums2: Sequence[int]) -> float:
    """
    Find median of two sorted sequences. At least one of sequences should be not empty.
    :param nums1: sorted sequence of integers
    :param nums2: sorted sequence of integers
    :return: middle value if sum of sequences' lengths is odd
             average of two middle values if sum of sequences' lengths is even
    """
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1

    left = 0
    right = len(nums1)

    while left <= right:
        pivot_1 = (left + right) // 2
        pivot_2 = (len(nums1) + len(nums2) + 1) // 2 - pivot_1

        max_left_1 = float("-inf") if pivot_1 == 0 else nums1[pivot_1 - 1]
        min_right_1 = float("inf") if pivot_1 == len(nums1) else nums1[pivot_1]

        max_left_2 = float("-inf") if pivot_2 == 0 else nums2[pivot_2 - 1]
        min_right_2 = float("inf") if pivot_2 == len(nums2) else nums2[pivot_2]

        if max_left_1 <= min_right_2 and max_left_2 <= min_right_1:
            if (len(nums1) + len(nums2)) % 2 == 0:
                return (max(max_left_1, max_left_2) + min(min_right_1, min_right_2)) * 0.5
            else:
                return float(max(max_left_1, max_left_2))
        elif max_left_1 > min_right_2:
            right = pivot_1
        else:
            left = pivot_1 + 1
