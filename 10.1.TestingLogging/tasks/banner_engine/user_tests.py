import typing

import pytest

from .banner_engine import (
    BannerStat,
    Banner,
    BannerStorage,
    EpsilonGreedyBannerEngine,
    EmptyBannerStorageError,
)
from . import banner_engine as banner_engine_module

TEST_DEFAULT_CTR = 0.1


@pytest.fixture(scope="function")
def test_banners() -> list[Banner]:
    return [
        Banner("b1", cost=1, stat=BannerStat(10, 20)),
        Banner("b2", cost=250, stat=BannerStat(20, 20)),
        Banner("b3", cost=100, stat=BannerStat(0, 20)),
        Banner("b4", cost=100, stat=BannerStat(1, 20)),
    ]


@pytest.mark.parametrize("clicks, shows, expected_ctr", [(1, 1, 1.0), (20, 100, 0.2), (5, 100, 0.05)])
def test_banner_stat_ctr_value(clicks: int, shows: int, expected_ctr: float) -> None:
    stat = BannerStat(clicks, shows)
    ctr = stat.compute_ctr(TEST_DEFAULT_CTR)
    assert ctr == pytest.approx(expected_ctr)


def test_empty_stat_compute_ctr_returns_default_ctr() -> None:
    stat = BannerStat(0, 0)
    ctr = stat.compute_ctr(TEST_DEFAULT_CTR)
    assert ctr == pytest.approx(TEST_DEFAULT_CTR)


def test_banner_stat_add_show_lowers_ctr() -> None:
    stat = BannerStat(10, 20)
    ctr_before = stat.compute_ctr(TEST_DEFAULT_CTR)
    stat.add_show()
    ctr_after = stat.compute_ctr(TEST_DEFAULT_CTR)

    assert stat.shows == 21
    assert ctr_after < ctr_before


def test_banner_stat_add_click_increases_ctr() -> None:
    stat = BannerStat(10, 20)
    ctr_before = stat.compute_ctr(TEST_DEFAULT_CTR)
    stat.add_click()
    ctr_after = stat.compute_ctr(TEST_DEFAULT_CTR)

    assert stat.clicks == 11
    assert ctr_after > ctr_before


def test_get_banner_with_highest_cpc_returns_banner_with_highest_cpc(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners, default_ctr=TEST_DEFAULT_CTR)

    def cpc(b: Banner) -> float:
        return b.stat.compute_ctr(TEST_DEFAULT_CTR) * b.cost

    expected_best = max(test_banners, key=cpc)
    best_banner = storage.banner_with_highest_cpc()

    assert best_banner.banner_id == expected_best.banner_id


def test_banner_engine_raise_empty_storage_exception_if_constructed_with_empty_storage() -> None:
    storage = BannerStorage([], default_ctr=TEST_DEFAULT_CTR)

    with pytest.raises(EmptyBannerStorageError):
        EpsilonGreedyBannerEngine(storage, random_banner_probability=0.5)


def test_engine_send_click_not_fails_on_unknown_banner(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners, default_ctr=TEST_DEFAULT_CTR)
    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=0.5)

    total_cost_before = engine.total_cost
    clicks_before = {b.banner_id: b.stat.clicks for b in test_banners}

    engine.send_click("unknown_banner")

    clicks_after = {b.banner_id: b.stat.clicks for b in test_banners}
    assert engine.total_cost == total_cost_before
    assert clicks_after == clicks_before


def test_engine_with_zero_random_probability_shows_banner_with_highest_cpc(
    test_banners: list[Banner],
    monkeypatch: typing.Any,
) -> None:
    storage = BannerStorage(test_banners, default_ctr=TEST_DEFAULT_CTR)

    def cpc(b: Banner) -> float:
        return b.stat.compute_ctr(TEST_DEFAULT_CTR) * b.cost

    best_banner = max(test_banners, key=cpc)
    non_best_banner = next(b for b in test_banners if b.banner_id != best_banner.banner_id)

    def fake_random_banner(self: BannerStorage) -> Banner:
        return non_best_banner

    monkeypatch.setattr(banner_engine_module.BannerStorage, "random_banner", fake_random_banner)

    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=0.0)
    shown_banner_id = engine.show_banner()

    assert shown_banner_id == best_banner.banner_id


@pytest.mark.parametrize("expected_random_banner", ["b1", "b2", "b3", "b4"])
def test_engine_with_1_random_banner_probability_gets_random_banner(
    expected_random_banner: str,
    test_banners: list[Banner],
    monkeypatch: typing.Any,
) -> None:
    storage = BannerStorage(test_banners, default_ctr=TEST_DEFAULT_CTR)

    def fake_choice(seq: list[str]) -> str:
        return expected_random_banner

    monkeypatch.setattr(banner_engine_module.random, "choice", fake_choice)

    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=1.0)
    shown_banner_id = engine.show_banner()

    assert shown_banner_id == expected_random_banner


def test_total_cost_equals_to_cost_of_clicked_banners(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners, default_ctr=TEST_DEFAULT_CTR)
    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=0.5)

    # Click each banner twice
    click_sequence = [b.banner_id for b in test_banners for _ in range(2)]
    expected_total_cost = sum(storage.get_banner(b_id).cost for b_id in click_sequence)

    for b_id in click_sequence:
        engine.send_click(b_id)

    assert engine.total_cost == expected_total_cost


def test_engine_show_increases_banner_show_stat(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners, default_ctr=TEST_DEFAULT_CTR)
    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=0.5)

    total_shows_before = sum(b.stat.shows for b in test_banners)
    engine.show_banner()
    total_shows_after = sum(b.stat.shows for b in test_banners)

    assert total_shows_after == total_shows_before + 1
    assert engine.shown_count == 1


def test_engine_click_increases_banner_click_stat(test_banners: list[Banner]) -> None:
    storage = BannerStorage(test_banners, default_ctr=TEST_DEFAULT_CTR)
    engine = EpsilonGreedyBannerEngine(storage, random_banner_probability=0.5)

    banner = test_banners[0]
    clicks_before = banner.stat.clicks

    engine.send_click(banner.banner_id)

    assert banner.stat.clicks == clicks_before + 1
