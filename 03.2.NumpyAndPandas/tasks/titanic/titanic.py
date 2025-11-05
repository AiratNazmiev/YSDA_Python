import typing as tp
import polars as pl


def male_age(df: pl.DataFrame) -> float:
    """
    Return mean age of survived men, embarked in Southampton with fare > 30
    :param df: dataframe
    :return: mean age
    """
    out = (
        df.lazy()
        .filter(
            (pl.col("Survived") == 1)
            & (pl.col("Sex") == "male")
            & (pl.col("Embarked") == "S")
            & (pl.col("Fare") > 30)
        )
        .select(pl.col("Age"))
        .drop_nulls()
        .select(pl.mean("Age"))
        .collect()
    )

    return float(out.item())


def nan_columns(df: pl.DataFrame) -> tp.Iterable[str]:
    """
    Return list of columns containing nans
    :param df: dataframe
    :return: series of columns
    """
    out = (
        df
        .null_count()
        .transpose(include_header=True, header_name="column", column_names=["null_count"])
        .filter(pl.col("null_count") > 0)
        .select("column")
        .to_series()
        .to_list()
    )

    return out


def class_distribution(df: pl.DataFrame) -> pl.Series:
    """
    Return Pclass distrubution
    :param df: dataframe
    :return: series with ratios
    """
    out = (
        df.lazy()
        .with_columns(pl.len().alias("total"))
        .group_by("Pclass")
        .agg(
            (pl.len() / pl.col("total").first()).alias("ratio")
        )
        .sort("Pclass")
        .select("ratio")
        .collect()
        .get_column("ratio")
    )

    return out


def families_count(df: pl.DataFrame, k: int) -> int:
    """
    Compute number of families with more than k members
    :param df: dataframe,
    :param k: number of members,
    :return: number of families
    """
    last_counts = (
        df.with_columns(
            pl.col("Name").str.split(",").list.first().alias("Last")
        )
        .group_by("Last")
        .len()
    )

    return last_counts.filter(pl.col("len") > k).height


def mean_price(df: pl.DataFrame, tickets: tp.Iterable[str]) -> float:
    """
    Return mean price for specific tickets list
    :param df: dataframe,
    :param tickets: list of tickets,
    :return: mean fare for this tickets
    """
    out = (
        df.filter(pl.col("Ticket").is_in(list(tickets)))
          .select(pl.col("Fare").mean().alias("mean_fare"))
    )

    return float(out.item()) if out.height > 0 else float("nan")


def max_size_group(df: pl.DataFrame, columns: list[str]) -> tp.Iterable[tp.Any]:
    """
    For given set of columns compute most common combination of values of these columns
    :param df: dataframe,
    :param columns: columns for grouping,
    :return: list of most common combination
    """
    if not columns:
        return tuple()

    grouped = (
        df.drop_nulls(columns)
        .group_by(columns)
        .len()
        .sort("len", descending=True)
    )

    if grouped.is_empty():
        return tuple()

    top_row_df = grouped.select(columns).head(1)

    return tuple(top_row_df.row(0))


def dead_lucky(df: pl.DataFrame) -> float:
    """
    Compute dead ratio of passengers with lucky tickets.
    A ticket is considered lucky when it contains an even number of digits in it
    and the sum of the first half of digits equals the sum of the second part of digits
    ex:
    lucky: 123222, 2671, 935755
    not lucky: 123456, 62869, 568290
    :param df: dataframe,
    :return: ratio of dead lucky passengers
    """
    def is_lucky(number_str: str) -> int:
        if number_str is None:
            return 0
        s = str(number_str)
        if s.isnumeric():
            n = len(s)
            if n % 2 == 0:
                half = n // 2
                if sum(map(int, s[:half])) == sum(map(int, s[half:])):
                    return 1
        return 0

    lucky = df.with_columns(
        pl.col("Ticket").map_elements(is_lucky, return_dtype=pl.Int8).alias("is_lucky")
    ).filter(pl.col("is_lucky") == 1)

    total_lucky = lucky.height
    if total_lucky == 0:
        return 0.0

    dead_lucky_count = lucky.filter(pl.col("Survived") == 0).height

    return dead_lucky_count / total_lucky
