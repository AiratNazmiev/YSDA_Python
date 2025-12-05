import json
from pathlib import Path

import click

from compgraph.algorithms import inverted_index_graph


@click.command()
@click.argument("input_stream_name")
@click.argument("output_stream_name")
def tf_idf(input_stream_name: str, output_stream_name: str) -> None:
    input_path = Path(input_stream_name).resolve()
    output_path = Path(output_stream_name).resolve()

    graph = inverted_index_graph(str(input_path), file=True)
    result_iter = graph.run()
    result = list(result_iter)

    with output_path.open("w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    tf_idf()
