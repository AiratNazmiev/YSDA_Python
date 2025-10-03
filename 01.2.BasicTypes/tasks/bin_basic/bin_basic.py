# def find_value(nums: list[int] | range, value: int) -> bool:
#     """
#     Find value in sorted sequence
#     :param nums: sequence of integers. Could be empty
#     :param value: integer to find
#     :return: True if value exists, False otherwise
#     """
#     left = 0
#     right = len(nums)
#     while left < right:
#         mid = (left + right) // 2
#         if nums[mid] < value:
#             left = mid + 1
#         elif nums[mid] > value:
#             right = mid
#         else:
#             return True

#     return False
def find_value(nums: list[int] | range, value: int) -> bool:
    """
    Find value in sorted sequence
    :param nums: sequence of integers. Could be empty
    :param value: integer to find
    :return: True if value exists, False otherwise
    """
    left = 0
    right = len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] < value:
            left = mid + 1
        elif nums[mid] > value:
            right = mid - 1
        else:
            return True

    return False
