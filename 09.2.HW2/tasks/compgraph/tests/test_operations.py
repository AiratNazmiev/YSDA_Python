import copy
import dataclasses
import typing as tp

import pytest
from pytest import approx

from compgraph import operations as ops


class _Key:
    def __init__(self, *keys: str) -> None:
        self._keys = keys

    def __call__(self, row: tp.Mapping[str, tp.Any]) -> tuple[str, ...]:
        return tuple(str(row.get(key)) for key in self._keys)


@dataclasses.dataclass
class MapCase:
    mapper: ops.Mapper
    data: list[ops.TRow]
    ground_truth: list[ops.TRow]
    cmp_keys: tuple[str, ...]
    mapper_item: int = 0
    mapper_ground_truth_items: tuple[int, ...] = (0,)


MAP_CASES: list[MapCase] = [
    MapCase(
        mapper=ops.IDF(
            columns=["num_of_docs", "num_of_docs_with_word"],
            result_col="idf",
        ),
        data=[
            {"num_of_docs": 5, "num_of_docs_with_word": 2},
            {"num_of_docs": 5, "num_of_docs_with_word": 3},
            {"num_of_docs": 5, "num_of_docs_with_word": 1},
        ],
        ground_truth=[
            {
                "num_of_docs": 5,
                "num_of_docs_with_word": 2,
                "idf": approx(0.9162, 0.001),
            },
            {
                "num_of_docs": 5,
                "num_of_docs_with_word": 3,
                "idf": approx(0.5108, 0.001),
            },
            {
                "num_of_docs": 5,
                "num_of_docs_with_word": 1,
                "idf": approx(1.6094, 0.001),
            },
        ],
        cmp_keys=("idf",),
    ),
    MapCase(
        mapper=ops.PMI(
            columns=["freq_doc", "freq_all"],
            result_col="pmi",
        ),
        data=[
            {"freq_doc": 0.1, "freq_all": 0.01},
            {"freq_doc": 0.4, "freq_all": 0.03},
            {"freq_doc": 0.3, "freq_all": 0.01},
        ],
        ground_truth=[
            {
                "freq_doc": 0.1,
                "freq_all": 0.01,
                "pmi": approx(2.3025, 0.001),
            },
            {
                "freq_doc": 0.4,
                "freq_all": 0.03,
                "pmi": approx(2.5902, 0.001),
            },
            {
                "freq_doc": 0.3,
                "freq_all": 0.01,
                "pmi": approx(3.4011, 0.001),
            },
        ],
        cmp_keys=("pmi",),
    ),
    MapCase(
        mapper=ops.Reveal(column="count"),
        data=[
            {"freq_all": 0.01, "freq_doc": 0.1, "count": 1},
        ],
        ground_truth=[
            {"freq_all": 0.01, "freq_doc": 0.1},
        ],
        cmp_keys=("freq_all", "freq_doc"),
    ),
    MapCase(
        mapper=ops.Multiply(column="freq_doc", factor=-1),
        data=[
            {"freq_doc": 0.1, "freq_all": 0.01},
            {"freq_doc": 0.4, "freq_all": 0.03},
            {"freq_doc": 0.3, "freq_all": 0.01},
        ],
        ground_truth=[
            {"freq_doc": -0.1, "freq_all": 0.01},
            {"freq_doc": -0.4, "freq_all": 0.03},
            {"freq_doc": -0.3, "freq_all": 0.01},
        ],
        cmp_keys=("freq_doc",),
    ),
    MapCase(
        mapper=ops.Multiply(column="freq_all", factor=2),
        data=[
            {"freq_doc": 0.1, "freq_all": 0.01},
        ],
        ground_truth=[
            {"freq_doc": 0.1, "freq_all": 0.02},
        ],
        cmp_keys=("freq_all",),
    ),
    MapCase(
        mapper=ops.GetDuration(
            start_col="start",
            leave_col="leave",
            res_col_name="duration",
        ),
        data=[
            {"start": "20191022T131820.842000", "leave": "20191022T131828.330000"},
            {"start": "20181022T131820.842000", "leave": "20181022T131828.330000"},
            {"start": "20171022T131820.842000", "leave": "20171022T131828.330000"},
        ],
        ground_truth=[
            {
                "start": "20191022T131820.842000",
                "leave": "20191022T131828.330000",
                "duration": approx(0.002, 0.1),
            },
            {
                "start": "20181022T131820.842000",
                "leave": "20181022T131828.330000",
                "duration": approx(0.002, 0.1),
            },
            {
                "start": "20171022T131820.842000",
                "leave": "20171022T131828.330000",
                "duration": approx(0.002, 0.1),
            },
        ],
        cmp_keys=("duration",),
    ),
    MapCase(
        mapper=ops.GetDuration(
            start_col="start",
            leave_col="leave",
            res_col_name="duration",
        ),
        data=[
            {"start": "20190101T120000", "leave": "20190101T130000"},
            {"start": "20190101T120000.000001", "leave": "20190101T125959"},
        ],
        ground_truth=[
            {
                "start": "20190101T120000",
                "leave": "20190101T130000",
                "duration": approx(1.0, rel=1e-3),
            },
            {
                "start": "20190101T120000.000001",
                "leave": "20190101T125959",
                "duration": approx(0.9994, rel=1e-3),
            },
        ],
        cmp_keys=("duration",),
    ),
    MapCase(
        mapper=ops.GetWeekdayAndHour(
            enter_time_col="start",
            weekday_res_col="week",
            hour_res_col="hour",
        ),
        data=[
            {"start": "20191022T131820.842000"},
            {"start": "20181022T131820.842000"},
            {"start": "20171022T131820.842000"},
        ],
        ground_truth=[
            {"hour": 13, "start": "20191022T131820.842000", "week": "Tue"},
            {"hour": 13, "start": "20181022T131820.842000", "week": "Mon"},
            {"hour": 13, "start": "20171022T131820.842000", "week": "Sun"},
        ],
        cmp_keys=("week", "hour"),
    ),
    MapCase(
        mapper=ops.GetWeekdayAndHour(
            enter_time_col="start",
            weekday_res_col="week",
            hour_res_col="hour",
        ),
        data=[
            {"start": "20240101T000000"},
            {"start": "20240101T235959"},
        ],
        ground_truth=[
            {"hour": 0, "start": "20240101T000000", "week": "Mon"},
            {"hour": 23, "start": "20240101T235959", "week": "Mon"},
        ],
        cmp_keys=("week", "hour"),
    ),
    MapCase(
        mapper=ops.GetHaversineDist(
            start="start",
            end="end",
            res_col_name="distance",
        ),
        data=[
            {
                "start": [37.41463478654623, 55.654487907886505],
                "end": [37.41442892700434, 55.654839486815035],
            },
            {
                "start": [37.584684155881405, 55.78285809606314],
                "end": [37.58415022864938, 55.78177368734032],
            },
            {
                "start": [37.736429711803794, 55.62696328852326],
                "end": [37.736344216391444, 55.626937723718584],
            },
        ],
        ground_truth=[
            {
                "start": [37.41463478654623, 55.654487907886505],
                "end": [37.41442892700434, 55.654839486815035],
                "distance": approx(0.041, 0.1),
            },
            {
                "start": [37.584684155881405, 55.78285809606314],
                "end": [37.58415022864938, 55.78177368734032],
                "distance": approx(0.125, 0.1),
            },
            {
                "start": [37.736429711803794, 55.62696328852326],
                "end": [37.736344216391444, 55.626937723718584],
                "distance": approx(0.006, 0.1),
            },
        ],
        cmp_keys=("start", "end", "distance"),
    ),
    MapCase(
        mapper=ops.GetAverageSpeed(
            dist="dist",
            duration="duration",
            res_col_name="speed",
        ),
        data=[
            {"dist": 5, "duration": 6},
            {"dist": 1, "duration": 3},
            {"dist": 10, "duration": 2},
        ],
        ground_truth=[
            {"dist": 5, "duration": 6, "speed": approx(0.8333, 0.1)},
            {"dist": 1, "duration": 3, "speed": approx(0.3333, 0.1)},
            {"dist": 10, "duration": 2, "speed": 5.0},
        ],
        cmp_keys=("speed",),
    ),
]


@pytest.mark.parametrize("case", MAP_CASES)
def test_mapper(case: MapCase) -> None:
    mapper_input_row = copy.deepcopy(case.data[case.mapper_item])
    mapper_expected_rows = [
        copy.deepcopy(case.ground_truth[i]) for i in case.mapper_ground_truth_items
    ]

    key_func = _Key(*case.cmp_keys)

    mapper_result = case.mapper(mapper_input_row)
    assert isinstance(mapper_result, tp.Iterator)

    assert sorted(mapper_result, key=key_func) == sorted(
        mapper_expected_rows,
        key=key_func,
    )

    map_wrapper_result = ops.Map(case.mapper)(iter(case.data))
    assert isinstance(map_wrapper_result, tp.Iterator)

    assert sorted(map_wrapper_result, key=key_func) == sorted(
        case.ground_truth,
        key=key_func,
    )
    
def test_weighted_term_frequency() -> None:
    reducer = ops.WeightedTermFrequency("word", "count", result_column="tf")

    rows = [
        {"doc": 1, "word": "a", "count": 2},
        {"doc": 1, "word": "b", "count": 1},
    ]

    assert sorted(
        reducer(("doc",), iter(rows)),
        key=_Key("word"),
    ) == sorted(
        [
            {"doc": 1, "word": "a", "tf": approx(2 / 3, rel=1e-3)},
            {"doc": 1, "word": "b", "tf": approx(1 / 3, rel=1e-3)},
        ],
        key=_Key("word"),
    )


def test_sum_columns() -> None:
    reducer = ops.SumColumns(["distance", "duration"])

    rows = [
        {"weekday": "Mon", "hour": 9, "distance": 2, "duration": 1},
        {"weekday": "Mon", "hour": 9, "distance": 3, "duration": 2},
    ]

    assert list(reducer(("weekday", "hour"), iter(rows))) == [
        {"weekday": "Mon", "hour": 9, "distance": 5, "duration": 3}
    ]
