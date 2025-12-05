import json
from pathlib import Path

import click

from compgraph.algorithms import word_count_graph


@click.command()
@click.argument("input_stream_name", nargs=1)
@click.argument("output_stream_name", nargs=1)
def word_count(input_stream_name: str, output_stream_name: str) -> None:
    """Count words in the input JSON and write results to the output JSON."""
    input_path = Path(input_stream_name).resolve()
    output_path = Path(output_stream_name).resolve()

    graph = word_count_graph(
        input_stream_name=str(input_path),
        text_column="text",
        count_column="count",
        file=True,
    )

    result = list(graph.run())

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    word_count()
