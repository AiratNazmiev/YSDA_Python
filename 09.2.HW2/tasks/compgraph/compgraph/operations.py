from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from itertools import groupby
import re
import heapq
import string
import typing as tp
import math


def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))


TRow = dict[str, tp.Any]
TRowsIterable = tp.Iterable[TRow]
TRowsGenerator = tp.Generator[TRow, None, None]


# ======================================================================
# Base operations
# ======================================================================


class Operation(ABC):
    @abstractmethod
    def __call__(
        self,
        rows: TRowsIterable,
        *args: tp.Any,
        **kwargs: tp.Any,
    ) -> TRowsGenerator: ...


class AddOperation(Operation):
    """
    Compose two operations where `second` produces rows and `first` consumes them.
    AddOperation(first, second)(**kwargs) ≈ first(second(**kwargs))
    """

    def __init__(self, first: Operation, second: Operation) -> None:
        self.first = first
        self.second = second

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        rows_from_second = self.second(*args, **kwargs)
        yield from self.first(rows_from_second)


class Read(Operation):
    """
    Read lines from a file and parse them with a given parser.

    Parser can return:
      - a single row (dict)
      - a list of rows (list[dict])
    """

    def __init__(self, filename: str, parser: tp.Callable[[str], tp.Any]) -> None:
        self.filename = filename
        self.parser = parser

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        with open(self.filename) as f:
            for line in f:
                parsed = self.parser(line)
                if isinstance(parsed, list):
                    for row in parsed:
                        yield row
                else:
                    yield parsed


class ReadIterFactory(Operation):
    """
    Wrap a callable from kwargs[name] that returns an iterable of rows.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for row in kwargs[self.name]():
            yield row


# ======================================================================
# Map
# ======================================================================


class Mapper(ABC):
    """Base class for mappers (row -> 0..N rows)."""

    @abstractmethod
    def __call__(self, row: TRow) -> TRowsGenerator: ...


class Map(Operation):
    """Apply a Mapper to every row in the stream."""

    def __init__(self, mapper: Mapper) -> None:
        self.mapper = mapper

    def __call__(
        self,
        rows: TRowsIterable,
        *args: tp.Any,
        **kwargs: tp.Any,
    ) -> TRowsGenerator:
        for row in rows:
            yield from self.mapper(row)


class DummyMapper(Mapper):
    """Yield exactly the row passed."""

    def __call__(self, row: TRow) -> TRowsGenerator:
        yield row


class FilterPunctuation(Mapper):
    """Strip punctuation from a given column."""

    def __init__(self, column: str) -> None:
        self.column = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.column] = remove_punctuation(row[self.column])
        yield row


class LowerCase(Mapper):
    """Lowercase a given column."""

    def __init__(self, column: str) -> None:
        self.column = column

    @staticmethod
    def _lower_case(txt: str) -> str:
        return txt.lower()

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.column] = self._lower_case(row[self.column])
        yield row


class Split(Mapper):
    """Split one column into multiple rows by a separator.

    Tokens are produced lazily to avoid the intermediate list that ``str.split``
    would allocate. The regex-based iterator adds a tiny constant overhead for
    very short strings, but on real document payloads it keeps peak memory flat
    while matching Python's native splitting semantics.
    """

    def __init__(self, column: str, separator: str | None = None) -> None:
        """
        :param column: name of column to split
        :param separator: string to separate by (None -> any whitespace)
        """
        self.column = column
        if separator == "":
            raise ValueError("separator must not be empty")
        self._token_iter: tp.Callable[[str], tp.Iterator[str]]
        self.separator = separator
        if separator is None:
            whitespace_pattern = re.compile(r"\S+")
            self._token_iter = lambda text: (match.group(0) for match in whitespace_pattern.finditer(text))
        else:
            sep_pattern = re.compile(re.escape(separator))

            def _tokens(text: str) -> tp.Iterator[str]:
                start = 0
                for match in sep_pattern.finditer(text):
                    yield text[start : match.start()]
                    start = match.end()
                yield text[start:]

            self._token_iter = _tokens

    def __call__(self, row: TRow) -> TRowsGenerator:
        text = row[self.column]
        for value in self._token_iter(text):
            new_row = row.copy()  # copy to avoid mutating shared rows downstream
            new_row[self.column] = value
            yield new_row


class Product(Mapper):
    """Calculate product of multiple numeric columns."""

    def __init__(self, columns: tp.Sequence[str], result_column: str = "product") -> None:
        self.columns = list(columns)
        self.result_column = result_column

    def __call__(self, row: TRow) -> TRowsGenerator:
        prod = 1
        for column in self.columns:
            prod *= row[column]
        row[self.result_column] = prod
        yield row


class Filter(Mapper):
    """Keep only rows that satisfy a predicate."""

    def __init__(self, condition: tp.Callable[[TRow], bool]) -> None:
        self.condition = condition

    def __call__(self, row: TRow) -> TRowsGenerator:
        if self.condition(row):
            yield row


class Project(Mapper):
    """Keep only the given columns."""

    def __init__(self, columns: tp.Sequence[str]) -> None:
        self.columns = set(columns)

    def __call__(self, row: TRow) -> TRowsGenerator:
        yield {key: value for key, value in row.items() if key in self.columns}


class IDF(Mapper):
    """Compute IDF-like value: log(columns[0] / columns[1])."""

    def __init__(self, columns: tp.Sequence[str], result_col: str = "idf") -> None:
        self.columns = list(columns)
        self.result_col = result_col

    def __call__(self, row: TRow) -> TRowsGenerator:
        num = row[self.columns[0]]
        den = row[self.columns[1]]
        row[self.result_col] = math.log(num / den)
        yield row


class PMI(Mapper):
    """Compute PMI-like value: log(columns[0] / columns[1])."""

    def __init__(self, columns: tp.Sequence[str], result_col: str = "pmi") -> None:
        self.columns = list(columns)
        self.result_col = result_col

    def __call__(self, row: TRow) -> TRowsGenerator:
        num = row[self.columns[0]]
        den = row[self.columns[1]]
        row[self.result_col] = math.log(num / den)
        yield row


class Reveal(Mapper):
    """
    Duplicate row `times` based on a given column, then drop the column.
    """

    def __init__(self, column: str) -> None:
        self.column_to_reveal = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        times = row[self.column_to_reveal]
        del row[self.column_to_reveal]
        for _ in range(times):
            # Make copies to avoid later mutation issues downstream
            yield row.copy()


class Multiply(Mapper):
    """Scale a numeric column by a constant factor."""

    def __init__(self, column: str, factor: float) -> None:
        self.column = column
        self.factor = factor

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.column] = row[self.column] * self.factor
        yield row


class GetDuration(Mapper):
    """Compute duration (in hours) from two datetime columns."""

    def __init__(
        self,
        start_col: str,
        leave_col: str,
        res_col_name: str = "duration",
    ) -> None:
        self.start_col = start_col
        self.leave_col = leave_col
        self.res_col_name = res_col_name
        self._fmt_with_fraction = "%Y%m%dT%H%M%S.%f"
        self._fmt_without_fraction = "%Y%m%dT%H%M%S"

    def _parse_time(self, timestamp: str) -> datetime:
        if "." in timestamp:
            return datetime.strptime(timestamp, self._fmt_with_fraction)

        return datetime.strptime(timestamp, self._fmt_without_fraction)

    def __call__(self, row: TRow) -> TRowsGenerator:
        start = self._parse_time(row[self.start_col])
        leave = self._parse_time(row[self.leave_col])
        time_delta = leave - start
        row[self.res_col_name] = time_delta.total_seconds() / 3600.0
        yield row


class GetWeekdayAndHour(Mapper):
    """Extract weekday name and hour from a datetime column."""

    def __init__(
        self,
        enter_time_col: str,
        weekday_res_col: str,
        hour_res_col: str,
    ) -> None:
        self.enter_time_col = enter_time_col
        self.weekday_res_col = weekday_res_col
        self.hour_res_col = hour_res_col
        self._fmt_with_fraction = "%Y%m%dT%H%M%S.%f"
        self._fmt_without_fraction = "%Y%m%dT%H%M%S"

    def _parse_time(self, timestamp: str) -> datetime:
        if "." in timestamp:
            return datetime.strptime(timestamp, self._fmt_with_fraction)

        return datetime.strptime(timestamp, self._fmt_without_fraction)

    def __call__(self, row: TRow) -> TRowsGenerator:
        dt_obj = self._parse_time(row[self.enter_time_col])
        row[self.weekday_res_col] = dt_obj.strftime("%a")
        row[self.hour_res_col] = dt_obj.hour
        yield row


class GetHaversineDist(Mapper):
    """Compute haversine distance (km) between two (lng, lat) pairs."""

    def __init__(self, start: str, end: str, res_col_name: str = "distance") -> None:
        self.start = start
        self.end = end
        self.res_col_name = res_col_name
        self._radius_km = 6373.0

    def __call__(self, row: TRow) -> TRowsGenerator:
        lng1, lat1 = row[self.start]
        lng2, lat2 = row[self.end]

        lat1, lng1, lat2, lng2 = map(math.radians, (lat1, lng1, lat2, lng2))

        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat * 0.5) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng * 0.5) ** 2
        row[self.res_col_name] = 2 * self._radius_km * math.asin(math.sqrt(a))
        yield row


class GetAverageSpeed(Mapper):
    """Compute average speed as dist / duration."""

    def __init__(
        self,
        dist: str,
        duration: str,
        res_col_name: str = "speed",
    ) -> None:
        self.dist = dist
        self.duration = duration
        self.res_col_name = res_col_name

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.res_col_name] = row[self.dist] / row[self.duration]
        yield row


# ======================================================================
# Reduce
# ======================================================================


class Reducer(ABC):
    """Base class for reducers: grouped rows -> 0..N rows."""

    @abstractmethod
    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator: ...


class Reduce(Operation):
    """Group rows by key columns, then apply a Reducer to each group."""

    def __init__(self, reducer: Reducer, keys: tp.Sequence[str]) -> None:
        self.reducer = reducer
        self.keys = tuple(keys)

    def __call__(
        self,
        rows: TRowsIterable,
        *args: tp.Any,
        **kwargs: tp.Any,
    ) -> TRowsGenerator:
        def make_key(r: TRow) -> tuple[tp.Any, ...]:
            return tuple(r[k] for k in self.keys)

        for _, group in groupby(rows, key=make_key):
            yield from self.reducer(self.keys, group)


class FirstReducer(Reducer):
    """Yield only the first row in each group."""

    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator:
        for row in rows:
            yield row
            break


class TopN(Reducer):
    """Keep top N rows by a given column within each group."""

    def __init__(self, column: str, n: int) -> None:
        """
        :param column: column name to get top by
        :param n: number of top values to extract
        """
        self.column_max = column
        self.n = n

    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator:
        _ = group_key

        # (sort_value, tiebreaker, row_dict)
        heap: list[tuple[tp.Any, int, TRow]] = []
        idx = 0

        for row in rows:
            row_copy = row.copy()
            sort_val = row_copy[self.column_max]
            heapq.heappush(heap, (sort_val, idx, row_copy))
            idx += 1
            if len(heap) > self.n:
                heapq.heappop(heap)

        for _, _, row in heap:
            yield row


class TermFrequency(Reducer):
    """Calculate term frequency per group."""

    def __init__(self, words_column: str, result_column: str = "tf") -> None:
        self.words_column = words_column
        self.result_column = result_column

    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator:
        word_counts: dict[str, int] = defaultdict(int)
        key_values: dict[str, tp.Any] = {}
        total = 0

        for row in rows:
            if not key_values:
                key_values = {key: row[key] for key in group_key}
            word = row[self.words_column]
            word_counts[word] += 1
            total += 1

        for word, count in word_counts.items():
            result = dict(key_values)
            result[self.words_column] = word
            result[self.result_column] = count / total
            yield result


class WeightedTermFrequency(Reducer):
    """Calculate term frequency using pre-counted word occurrences per group."""

    def __init__(
        self,
        words_column: str,
        count_column: str,
        result_column: str = "tf",
    ) -> None:
        self.words_column = words_column
        self.count_column = count_column
        self.result_column = result_column

    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator:
        key_values: dict[str, tp.Any] = {}
        totals: list[tuple[str, int]] = []
        total_count = 0

        for row in rows:
            if not key_values:
                key_values = {key: row[key] for key in group_key}
            count = row[self.count_column]
            total_count += count
            totals.append((row[self.words_column], count))

        for word, count in totals:
            result = dict(key_values)
            result[self.words_column] = word
            result[self.result_column] = count / total_count
            yield result


class Count(Reducer):
    """
    Count number of rows per group and store in `column`.

    Example (group_key=('a',), column='d'):
        {'a': 1, 'b': 5}
        {'a': 1, 'b': 6}
    =>
        {'a': 1, 'd': 2}
    """

    def __init__(self, column: str) -> None:
        self.column = column

    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator:
        result: dict[str, tp.Any] = {}
        count = 0

        for row in rows:
            if not result:
                for key in group_key:
                    result[key] = row[key]
            count += 1

        result[self.column] = count
        yield result


class Sum(Reducer):
    """
    Sum a single column per group.

    Example (group_key=('a',), column='b'):
        {'a': 1, 'b': 2}
        {'a': 1, 'b': 3}
    =>
        {'a': 1, 'b': 5}
    """

    def __init__(self, column: str) -> None:
        self.column = column

    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator:
        result: dict[str, tp.Any] = {}
        total = 0

        for row in rows:
            if not result:
                for key in group_key:
                    result[key] = row[key]
            total += row[self.column]

        result[self.column] = total
        yield result


class SumColumns(Reducer):
    """Sum multiple numeric columns per group."""

    def __init__(self, columns: tp.Sequence[str]) -> None:
        self.columns = list(columns)

    def __call__(
        self,
        group_key: tuple[str, ...],
        rows: TRowsIterable,
    ) -> TRowsGenerator:
        result: dict[str, tp.Any] = {}
        totals = {column: 0 for column in self.columns}

        for row in rows:
            if not result:
                for key in group_key:
                    result[key] = row[key]
            for column in self.columns:
                totals[column] += row[column]

        result.update(totals)
        yield result


# ======================================================================
# Join side
# ======================================================================


class Joiner(ABC):
    """Base class for join strategies."""

    def __init__(self, suffix_a: str = "_1", suffix_b: str = "_2") -> None:
        self._a_suffix = suffix_a
        self._b_suffix = suffix_b

    def get_ans(
        self,
        row_a: dict[str, tp.Any],
        row_b: dict[str, tp.Any],
        keys: tp.Sequence[str],
    ) -> dict[str, tp.Any]:
        ans: dict[str, tp.Any] = {key: row_a[key] for key in keys}

        for key, value in row_a.items():
            if key in keys:
                continue
            out_key = key + self._a_suffix if key in row_b else key
            ans[out_key] = value

        for key, value in row_b.items():
            if key in keys:
                continue
            out_key = key + self._b_suffix if key in row_a else key
            ans[out_key] = value

        return ans

    @abstractmethod
    def __call__(
        self,
        keys: tp.Sequence[str],
        rows_a: TRowsIterable,
        rows_b: TRowsIterable,
    ) -> TRowsGenerator:
        ...


class Join(Operation):
    """
    Merge two sorted streams on given keys using a Joiner.
    Left stream is `rows`, right stream is `args[0]`.
    """

    def __init__(self, joiner: Joiner, keys: tp.Sequence[str]) -> None:
        self.joiner = joiner
        self.keys = tuple(keys)

    def __call__(
        self,
        rows: TRowsIterable,
        *args: tp.Any,
        **kwargs: tp.Any,
    ) -> TRowsGenerator:
        if not args:
            return

        right_rows: TRowsIterable = args[0]

        def make_key(r: TRow) -> tuple[tp.Any, ...]:
            return tuple(r[k] for k in self.keys)

        grouped_rows_a = groupby(rows, key=make_key)
        grouped_rows_b = groupby(right_rows, key=make_key)

        def next_group(
            it: tp.Iterator[tuple[tuple[tp.Any, ...], TRowsIterable]],
        ) -> tuple[tuple[tp.Any, ...] | None, TRowsIterable]:
            try:
                return next(it)
            except StopIteration:
                return None, iter(())

        key_a, group_a = next_group(grouped_rows_a)
        key_b, group_b = next_group(grouped_rows_b)

        # Merge join
        while key_a is not None and key_b is not None:
            if key_a == key_b:
                # Matching keys -> regular join
                yield from self.joiner(self.keys, group_a, group_b)
                key_a, group_a = next_group(grouped_rows_a)
                key_b, group_b = next_group(grouped_rows_b)
            elif key_a < key_b:
                # Left key is "smaller": may need left/outer join rows
                if isinstance(self.joiner, (LeftJoiner, OuterJoiner)):
                    yield from self.joiner(self.keys, group_a, [])
                key_a, group_a = next_group(grouped_rows_a)
            else:
                # Right key is "smaller": may need right/outer join rows
                if isinstance(self.joiner, (RightJoiner, OuterJoiner)):
                    yield from self.joiner(self.keys, [], group_b)
                key_b, group_b = next_group(grouped_rows_b)

        # Drain remaining left side
        if isinstance(self.joiner, (LeftJoiner, OuterJoiner)):
            while key_a is not None:
                yield from self.joiner(self.keys, group_a, [])
                key_a, group_a = next_group(grouped_rows_a)

        # Drain remaining right side
        if isinstance(self.joiner, (RightJoiner, OuterJoiner)):
            while key_b is not None:
                yield from self.joiner(self.keys, [], group_b)
                key_b, group_b = next_group(grouped_rows_b)


class InnerJoiner(Joiner):
    """Inner join strategy."""

    def __call__(
        self,
        keys: tp.Sequence[str],
        rows_a: TRowsIterable,
        rows_b: TRowsIterable,
    ) -> TRowsGenerator:
        list_rows_b = list(rows_b)
        for row_a in rows_a:
            for row_b in list_rows_b:
                yield self.get_ans(row_a, row_b, keys)


class OuterJoiner(Joiner):
    """Full outer join strategy."""

    def __call__(
        self,
        keys: tp.Sequence[str],
        rows_a: TRowsIterable,
        rows_b: TRowsIterable,
    ) -> TRowsGenerator:
        list_rows_a = list(rows_a)
        list_rows_b = list(rows_b)

        if not list_rows_a and not list_rows_b:
            return

        if not list_rows_b:
            # Only left side present
            for row_a in list_rows_a:
                yield row_a
            return

        if not list_rows_a:
            # Only right side present
            for row_b in list_rows_b:
                yield row_b
            return

        # Both sides present -> regular product join
        for row_a in list_rows_a:
            for row_b in list_rows_b:
                yield self.get_ans(row_a, row_b, keys)


class LeftJoiner(Joiner):
    """Left join strategy."""

    def __call__(
        self,
        keys: tp.Sequence[str],
        rows_a: TRowsIterable,
        rows_b: TRowsIterable,
    ) -> TRowsGenerator:
        list_rows_b = list(rows_b)
        if not list_rows_b:
            for row_a in rows_a:
                yield row_a
            return

        for row_a in rows_a:
            for row_b in list_rows_b:
                yield self.get_ans(row_a, row_b, keys)


class RightJoiner(Joiner):
    """Right join strategy."""

    def __call__(
        self,
        keys: tp.Sequence[str],
        rows_a: TRowsIterable,
        rows_b: TRowsIterable,
    ) -> TRowsGenerator:
        list_rows_a = list(rows_a)
        if not list_rows_a:
            for row_b in rows_b:
                yield row_b
            return

        for row_b in rows_b:
            for row_a in list_rows_a:
                yield self.get_ans(row_a, row_b, keys)
