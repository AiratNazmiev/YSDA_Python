import typing as tp
from pathlib import Path

import pytest
import numpy as np
import polars as pl
from polars.testing import assert_series_equal

from titanic import male_age, nan_columns, class_distribution, families_count, mean_price, max_size_group, dead_lucky


FILE_PATH = Path(__file__).parent / "titanic.csv"


@pytest.fixture(scope="function")
def dataframe() -> pl.DataFrame:
    df = pl.read_csv(FILE_PATH, separator="\t")
    yield df


def test_male_age(dataframe: pl.DataFrame) -> None:
    np.testing.assert_allclose(male_age(dataframe), 30.0)


def test_nan_columns(dataframe: pl.DataFrame) -> None:
    assert set(nan_columns(dataframe)) == {"Age", "Cabin", "Embarked"}


def test_class_distribution(dataframe: pl.DataFrame) -> None:
    class_distr_ans = pl.Series(name='Pclass', values=[0.192308, 0.192308, 0.615385], dtype=pl.Float64)
    assert_series_equal(class_distribution(dataframe).sort(), class_distr_ans, check_names=False)

@pytest.mark.parametrize(
    "count_members,count_families",
    [
        (0, 141),
        (1, 13),
        (2, 1),
        (3, 1),
        (4, 0),
    ],
)
def test_families_count(count_members: int, count_families: int, dataframe: pl.DataFrame) -> None:
    assert families_count(dataframe, count_members) == count_families


def test_mean_price(dataframe: pl.DataFrame) -> None:
    np.testing.assert_allclose(mean_price(dataframe, dataframe["Ticket"].unique()), dataframe["Fare"].mean()) # type: ignore

    for row in dataframe.iter_rows(named=True):
        np.testing.assert_allclose(mean_price(dataframe, [row["Ticket"]]), row["Fare"])

    value = 26.0
    tickets = dataframe.filter(pl.col("Fare").is_between(value - 1e-9, value + 1e-9))["Ticket"].to_list()
    assert mean_price(dataframe, tickets) == pytest.approx(value)


@pytest.mark.parametrize(
    "columns,expected_result",
    [
        (["Survived", "Sex"], (0, "male")),
        (["Survived", "Sex", "Cabin"], (0, "male", "D26")),
        (["Embarked", "Pclass"], ("S", 3)),
        (["Age"], (21.00,)),
    ],
)
def test_max_size_group(columns: list[str], expected_result: tuple[tp.Any], dataframe: pl.DataFrame) -> None:
    assert max_size_group(dataframe, columns) == expected_result


def test_dead_lucky(dataframe: pl.DataFrame) -> None:
    assert dead_lucky(dataframe) == pytest.approx(0.75)
