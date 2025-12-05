import json
from pathlib import Path

import click

from compgraph.algorithms import pmi_graph


@click.command()
@click.argument("input_filepath", nargs=1)
@click.argument("output_filepath", nargs=1)
def pmi(input_filepath: str, output_filepath: str) -> None:
    """Compute PMI scores from input JSON and write result to output JSON."""
    input_path = Path(input_filepath).resolve()
    output_path = Path(output_filepath).resolve()

    graph = pmi_graph(
        input_stream_name=str(input_path),
        file=True
    )
    result_iter = graph.run()
    result = list(result_iter)

    with output_path.open("w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    pmi()
