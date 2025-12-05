import json
from pathlib import Path

import click

from compgraph.algorithms import yandex_maps_graph


@click.command()
@click.argument("first_input_filepath", nargs=1)
@click.argument("second_input_filepath", nargs=1)
@click.argument("output_filepath", nargs=1)
def yandex_maps(
    first_input_filepath: str,
    second_input_filepath: str,
    output_filepath: str,
) -> None:
    """Compute average speeds per weekday/hour and write results to JSON."""
    time_path = Path(first_input_filepath).resolve()
    length_path = Path(second_input_filepath).resolve()
    output_path = Path(output_filepath).resolve()

    graph = yandex_maps_graph(
        input_stream_name_time=str(time_path),
        input_stream_name_length=str(length_path),
        file=True,
    )

    result = list(graph.run())

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    yandex_maps()
