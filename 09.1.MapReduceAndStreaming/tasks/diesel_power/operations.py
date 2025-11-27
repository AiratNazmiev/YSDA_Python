from abc import abstractmethod, ABC
import typing as tp
import string
import itertools
import heapq

TRow = dict[str, tp.Any]
TRowsIterable = tp.Iterable[TRow]
TRowsGenerator = tp.Generator[TRow, None, None]


class Operation(ABC):
    @abstractmethod
    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        pass


class Read(Operation):
    def __init__(self, filename: str, parser: tp.Callable[[str], TRow]) -> None:
        self._filename = filename
        self._parser = parser

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        with open(self._filename) as f:
            for line in f:
                yield self._parser(line)


class ReadIterFactory(Operation):
    def __init__(self, name: str) -> None:
        self._name = name

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for row in kwargs[self._name]():
            yield row


# Operations


class Mapper(ABC):
    """Base class for mappers"""
    @abstractmethod
    def __call__(self, row: TRow) -> TRowsGenerator:
        """
        :param row: one table row
        """
        pass


class Map(Operation):
    def __init__(self, mapper: Mapper) -> None:
        self._mapper = mapper

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for row in rows:
            yield from self._mapper(row)


class Reducer(ABC):
    """Base class for reducers"""
    @abstractmethod
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        """
        :param rows: table rows
        """
        pass


class Reduce(Operation):
    def __init__(self, reducer: Reducer, keys: tp.Sequence[str]) -> None:
        self._reducer = reducer
        self._keys = keys

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        def key_func(row: TRow) -> tuple[tp.Any, ...]:
            return tuple(row[k] for k in self._keys)

        for _, group in itertools.groupby(rows, key_func):
            yield from self._reducer(tuple(self._keys), group)


class Joiner(ABC):
    """Base class for joiners"""
    def __init__(self, suffix_a: str = '_1', suffix_b: str = '_2') -> None:
        self._a_suffix = suffix_a
        self._b_suffix = suffix_b

    @abstractmethod
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        """
        :param keys: join keys
        :param rows_a: left table rows
        :param rows_b: right table rows
        """
        pass


class Join(Operation):
    def __init__(self, joiner: Joiner, keys: tp.Sequence[str]):
        self._keys = keys
        self._joiner = joiner

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        if not args:
            return

        rows_b: TRowsIterable = args[0]

        def key_func(row: TRow) -> tuple[tp.Any, ...]:
            return tuple(row[k] for k in self._keys)

        iter_a = itertools.groupby(rows, key_func)
        iter_b = itertools.groupby(rows_b, key_func)

        a_finished = False
        b_finished = False

        try:
            key_a_vals, group_a = next(iter_a)
        except StopIteration:
            a_finished = True
            key_a_vals = ()
            group_a = iter(())

        try:
            key_b_vals, group_b = next(iter_b)
        except StopIteration:
            b_finished = True
            key_b_vals = ()
            group_b = iter(())

        while not a_finished and not b_finished:
            if key_a_vals < key_b_vals:
                yield from self._joiner(self._keys, group_a, iter(()))
                try:
                    key_a_vals, group_a = next(iter_a)
                except StopIteration:
                    a_finished = True
                    key_a_vals = ()
                    group_a = iter(())
            elif key_b_vals < key_a_vals:
                # key only in B
                yield from self._joiner(self._keys, iter(()), group_b)
                try:
                    key_b_vals, group_b = next(iter_b)
                except StopIteration:
                    b_finished = True
                    key_b_vals = ()
                    group_b = iter(())
            else:
                # same key in both
                yield from self._joiner(self._keys, group_a, group_b)
                try:
                    key_a_vals, group_a = next(iter_a)
                except StopIteration:
                    a_finished = True
                    key_a_vals = ()
                    group_a = iter(())
                try:
                    key_b_vals, group_b = next(iter_b)
                except StopIteration:
                    b_finished = True
                    key_b_vals = ()
                    group_b = iter(())

        # leftovers in A
        while not a_finished:
            yield from self._joiner(self._keys, group_a, iter(()))
            try:
                key_a_vals, group_a = next(iter_a)
            except StopIteration:
                a_finished = True
                key_a_vals = ()
                group_a = iter(())

        # leftovers in B
        while not b_finished:
            yield from self._joiner(self._keys, iter(()), group_b)
            try:
                key_b_vals, group_b = next(iter_b)
            except StopIteration:
                b_finished = True
                key_b_vals = ()
                group_b = iter(())


# Dummy operators


class DummyMapper(Mapper):
    """Yield exactly the row passed"""
    def __call__(self, row: TRow) -> TRowsGenerator:
        yield row


class FirstReducer(Reducer):
    """Yield only first row from passed ones"""
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        for row in rows:
            yield row
            break


# Mappers


class FilterPunctuation(Mapper):
    """Left only non-punctuation symbols"""
    def __init__(self, column: str):
        """
        :param column: name of column to process
        """
        self._column = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        value = row[self._column]
        if isinstance(value, str):
            row[self._column] = value.translate(str.maketrans('', '', string.punctuation))
        yield row


class LowerCase(Mapper):
    """Replace column value with value in lower case"""
    def __init__(self, column: str):
        """
        :param column: name of column to process
        """
        self._column = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        value = row[self._column]
        if isinstance(value, str):
            row[self._column] = value.lower()
        yield row


class Split(Mapper):
    """Split row on multiple rows by separator"""
    def __init__(self, column: str, separator: str | None = None) -> None:
        """
        :param column: name of column to split
        :param separator: string to separate by
        """
        self._column = column
        self._separator = separator

    def __call__(self, row: TRow) -> TRowsGenerator:
        s = str(row[self._column])

        if self._separator is None:
            length = len(s)
            i = 0
            while i < length:
                while i < length and s[i].isspace():
                    i += 1
                if i >= length:
                    break
                j = i
                while j < length and not s[j].isspace():
                    j += 1
                token = s[i:j]
                new_row = row.copy()
                new_row[self._column] = token
                yield new_row
                i = j
            return

        sep = self._separator
        if sep == '':
            raise ValueError("empty separator")

        sep_len = len(sep)
        start = 0
        while True:
            idx = s.find(sep, start)
            if idx == -1:
                # last piece
                token = s[start:]
                new_row = row.copy()
                new_row[self._column] = token
                yield new_row
                break
            token = s[start:idx]
            new_row = row.copy()
            new_row[self._column] = token
            yield new_row
            start = idx + sep_len


class Product(Mapper):
    """Calculates product of multiple columns"""
    def __init__(self, columns: tp.Sequence[str], result_column: str = 'product') -> None:
        """
        :param columns: column names to product
        :param result_column: column name to save product in
        """
        self._columns = columns
        self._result_column = result_column

    def __call__(self, row: TRow) -> TRowsGenerator:
        prod = 1
        for col in self._columns:
            prod *= row[col]
        row[self._result_column] = prod
        yield row


class Filter(Mapper):
    """Remove records that don't satisfy some condition"""
    def __init__(self, condition: tp.Callable[[TRow], bool]) -> None:
        """
        :param condition: if condition is not true - remove record
        """
        self._condition = condition

    def __call__(self, row: TRow) -> TRowsGenerator:
        if self._condition(row):
            yield row


class Project(Mapper):
    """Leave only mentioned columns"""
    def __init__(self, columns: tp.Sequence[str]) -> None:
        """
        :param columns: names of columns
        """
        self._columns = columns

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row: TRow = {col: row[col] for col in self._columns if col in row}
        yield new_row


# Reducers


class TopN(Reducer):
    """Calculate top N by value"""
    def __init__(self, column: str, n: int) -> None:
        """
        :param column: column name to get top by
        :param n: number of top values to extract
        """
        self._column_max = column
        self._n = n

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        if self._n <= 0:
            return

        heap: list[tuple[tp.Any, int, TRow]] = []
        idx = 0
        for row in rows:
            val = row[self._column_max]
            if len(heap) < self._n:
                heapq.heappush(heap, (val, idx, row))
            else:
                if val > heap[0][0]:
                    heapq.heapreplace(heap, (val, idx, row))
            idx += 1

        for _, _, row in sorted(heap, key=lambda t: (t[0], t[1]), reverse=True):
            yield row


class TermFrequency(Reducer):
    """Calculate frequency of values in column"""
    def __init__(self, words_column: str, result_column: str = 'tf') -> None:
        """
        :param words_column: name for column with words
        :param result_column: name for result column
        """
        self._words_column = words_column
        self._result_column = result_column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        counts: dict[tp.Any, int] = {}
        total = 0
        first_row: TRow | None = None

        for row in rows:
            if first_row is None:
                first_row = row
            word = row[self._words_column]
            counts[word] = counts.get(word, 0) + 1
            total += 1

        if first_row is None or total == 0:
            return

        for word, cnt in counts.items():
            new_row: TRow = {
                self._words_column: word,
                self._result_column: cnt / total,
            }
            for key_name in group_key:
                new_row[key_name] = first_row[key_name]
            yield new_row


class Count(Reducer):
    """
    Count records by key
    Example for group_key=('a',) and column='d'
        {'a': 1, 'b': 5, 'c': 2}
        {'a': 1, 'b': 6, 'c': 1}
        =>
        {'a': 1, 'd': 2}
    """
    def __init__(self, column: str) -> None:
        """
        :param column: name for result column
        """
        self._column = column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        count_val = 0
        first_row: TRow | None = None

        for row in rows:
            if first_row is None:
                first_row = row
            count_val += 1

        if first_row is None:
            return

        new_row: TRow = {self._column: count_val}
        for key_name in group_key:
            new_row[key_name] = first_row[key_name]
        yield new_row


class Sum(Reducer):
    """
    Sum values aggregated by key
    Example for key=('a',) and column='b'
        {'a': 1, 'b': 2, 'c': 4}
        {'a': 1, 'b': 3, 'c': 5}
        =>
        {'a': 1, 'b': 5}
    """
    def __init__(self, column: str) -> None:
        """
        :param column: name for sum column
        """
        self._column = column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        total = 0
        first_row: TRow | None = None

        for row in rows:
            if first_row is None:
                first_row = row
            total += row[self._column]

        if first_row is None:
            return

        new_row: TRow = {key_name: first_row[key_name] for key_name in group_key}
        new_row[self._column] = total
        yield new_row


# Joiners


def _merge_rows(
    keys: tp.Sequence[str],
    row_a: TRow,
    row_b: TRow,
    suffix_a: str,
    suffix_b: str,
) -> TRow:
    """
    Merge two rows with possible overlapping non-key columns.
    Columns in `keys` are assumed identical in both rows.
    For other columns with the same name:
      - original name gets suffix_a for A's value
      - original name+suffix_b for B's value
    """
    result = row_a.copy()
    for key_b, val_b in row_b.items():
        if key_b not in result:
            result[key_b] = val_b
        elif key_b not in keys:
            val_a = result[key_b]
            del result[key_b]
            result[key_b + suffix_a] = val_a
            result[key_b + suffix_b] = val_b
    return result


class InnerJoiner(Joiner):
    """Join with inner strategy"""
    def __call__(self, keys: tp.Sequence[str],
                 rows_a: TRowsIterable,
                 rows_b: TRowsIterable) -> TRowsGenerator:
        rows_b_list = list(rows_b)
        if not rows_b_list:
            return
        for row_a in rows_a:
            for row_b in rows_b_list:
                yield _merge_rows(keys, row_a, row_b, self._a_suffix, self._b_suffix)


class OuterJoiner(Joiner):
    """Join with outer strategy"""
    def __call__(self, keys: tp.Sequence[str],
                 rows_a: TRowsIterable,
                 rows_b: TRowsIterable) -> TRowsGenerator:
        rows_a_list = list(rows_a)
        rows_b_list = list(rows_b)

        if rows_a_list and rows_b_list:
            for row_a in rows_a_list:
                for row_b in rows_b_list:
                    yield _merge_rows(keys, row_a, row_b, self._a_suffix, self._b_suffix)
        elif rows_a_list:
            for row_a in rows_a_list:
                yield row_a.copy()
        elif rows_b_list:
            for row_b in rows_b_list:
                yield row_b.copy()
        else:
            return


class LeftJoiner(Joiner):
    """Join with left strategy"""
    def __call__(self, keys: tp.Sequence[str],
                 rows_a: TRowsIterable,
                 rows_b: TRowsIterable) -> TRowsGenerator:
        rows_b_list = list(rows_b)

        if not rows_b_list:
            for row_a in rows_a:
                yield row_a.copy()
            return

        for row_a in rows_a:
            for row_b in rows_b_list:
                yield _merge_rows(keys, row_a, row_b, self._a_suffix, self._b_suffix)


class RightJoiner(Joiner):
    """Join with right strategy"""
    def __call__(self, keys: tp.Sequence[str],
                 rows_a: TRowsIterable,
                 rows_b: TRowsIterable) -> TRowsGenerator:
        rows_a_list = list(rows_a)

        if not rows_a_list:
            for row_b in rows_b:
                yield row_b.copy()
            return

        for row_b in rows_b:
            for row_a in rows_a_list:
                yield _merge_rows(keys, row_a, row_b, self._a_suffix, self._b_suffix)
