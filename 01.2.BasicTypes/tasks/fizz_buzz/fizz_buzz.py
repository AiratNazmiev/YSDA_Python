def get_fizz_buzz(n: int) -> list[int | str]:
   """
   If value divided by 3 - "Fizz",
      value divided by 5 - "Buzz",
      value divided by 15 - "FizzBuzz",
   else - value.
   :param n: size of sequence
   :return: list of values.
   """
   result = []
   for num in range(1, n + 1):
      if num % 15 == 0:
         result.append(num)
         continue
      if num % 5 == 0:
         result.append(num)
         continue
      if num % 3 == 0:
         result.append(num)
         continue
      result.append(num)

   return result
