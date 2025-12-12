import json
import typing as tp

from . import external_sort as ext_sort
from . import operations as ops


class Graph:
    """Simple computational graph with chainable operations."""

    def __init__(self) -> None:
        self.op: tp.Any = None

    @staticmethod
    def make_graph(input_stream_name: str, file: bool = False) -> "Graph":
        """Create graph reading from iterator (`run` kwarg) or JSON file."""
        if file:
            return Graph.graph_from_file(input_stream_name, json.loads)
        return Graph.graph_from_iter(input_stream_name)

    @staticmethod
    def graph_from_iter(name: str) -> "Graph":
        """Create graph that reads from an iterator passed as `name` to `run`."""
        graph = Graph()
        graph.op = ops.ReadIterFactory(name)
        return graph

    @staticmethod
    def graph_from_file(
        filename: str,
        parser: tp.Callable[[str], ops.TRow],
    ) -> "Graph":
        """Create graph that reads rows from a file using `parser`."""
        graph = Graph()
        graph.op = ops.Read(filename, parser)
        return graph

    def map(self, mapper: ops.Mapper) -> "Graph":
        """Return new graph with a map step added."""
        graph = Graph()
        graph.op = ops.AddOperation(ops.Map(mapper), self.op)
        return graph

    def reduce(self, reducer: ops.Reducer, keys: tp.Sequence[str]) -> "Graph":
        """Return new graph with a reduce step added."""
        graph = Graph()
        graph.op = ops.AddOperation(ops.Reduce(reducer, keys), self.op)
        return graph

    def sort(self, keys: tp.Sequence[str]) -> "Graph":
        """Return new graph with an external sort step added."""
        graph = Graph()
        graph.op = ops.AddOperation(ext_sort.ExternalSort(keys), self.op)
        return graph

    def join(
        self,
        joiner: ops.Joiner,
        join_graph: "Graph",
        keys: tp.Sequence[str],
    ) -> "Graph":
        """Return new graph that joins this graph with `join_graph`."""
        join_operation = ops.Join(joiner, keys)
        left_graph = self
        right_graph = join_graph

        def op(*args: tp.Any, **kwargs: tp.Any) -> ops.TRowsGenerator:
            left_rows = left_graph.run(**kwargs)
            right_rows = right_graph.run(**kwargs)
            yield from join_operation(left_rows, right_rows)

        graph = Graph()
        graph.op = op
        return graph

    def run(self, **kwargs: tp.Any) -> ops.TRowsIterable:
        """
        Execute the graph.

        Sources are passed as keyword arguments: each value should be a
        zero-argument callable returning an iterator of rows.
        """
        if self.op is None:
            raise RuntimeError("Graph has no root operation defined.")
        yield from self.op(**kwargs)
