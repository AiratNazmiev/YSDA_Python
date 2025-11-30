import pyarrow as pa
import pyarrow.parquet as pq


ValueType = int | list[int] | str | dict[str, str]


def get_pa_type(value: ValueType) -> pa.DataType:
    if isinstance(value, int):
        return pa.int64()
    if isinstance(value, list):
        return pa.list_(pa.int64())
    if isinstance(value, str):
        return pa.string()
    if isinstance(value, dict):
        return pa.map_(pa.string(), pa.string())
    raise TypeError("Unsupported value type")


def save_rows_to_parquet(rows: list[dict[str, ValueType]], output_filepath: str) -> None:
    """
    Save rows to parquet file.

    :param rows: list of rows containing data.
    :param output_filepath: local filepath for the resulting parquet file.
    :return: None.
    """
    field_order: list[str] = []
    field_types: dict[str, pa.DataType] = {}
    field_counts: dict[str, int] = {}

    for row in rows:
        for key, value in row.items():
            pa_type = get_pa_type(value)
            if key not in field_types:
                field_order.append(key)
                field_types[key] = pa_type
                field_counts[key] = 1
            else:
                if pa_type != field_types[key]:
                    raise TypeError(f"Field {key} has different types")
                field_counts[key] += 1

    schema = pa.schema([
        pa.field(
            name,
            field_types[name],
            nullable=(field_counts[name] < len(rows)),
        )
        for name in field_order
    ])

    cols = {name: [row.get(name) for row in rows] for name in field_order}

    table = pa.table(cols, schema=schema)

    pq.write_table(table, output_filepath)
