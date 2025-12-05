from itertools import islice, cycle
from operator import itemgetter
import typing as tp

from pytest import approx

import compgraph.operations as operations
from compgraph.algorithms import Graph
from compgraph import algorithms


Row = dict[str, tp.Any]


def _run_graph(graph: Graph, **sources: tp.Iterable[Row]) -> list[Row]:
    """Run graph on named sources, returning list of rows."""
    def make_source_iter(data: tp.Iterable[Row]) -> tp.Callable[[], tp.Iterator[Row]]:
        return lambda: iter(data)

    runners = {name: make_source_iter(data) for name, data in sources.items()}
    return list(graph.run(**runners))


# --- Basic operators ----------------------------------------------------------


def test_map() -> None:
    data = [
        {"test_id": 1, "text": "one two three"},
        {"test_id": 2, "text": "testing out stuff"},
    ]

    expected = [
        {"test_id": 1, "text": "one two three"},
        {"test_id": 2, "text": "testing out stuff"},
    ]

    graph = Graph.graph_from_iter("data").map(operations.DummyMapper())
    result = _run_graph(graph, data=data)

    assert result == expected


def test_reduce() -> None:
    data = [
        {"test_id": 1, "text": "hello, world"},
        {"test_id": 1, "text": "hello, world"},
        {"test_id": 2, "text": "bye!"},
        {"test_id": 2, "text": "welihf"},
    ]

    expected = [
        {"test_id": 1, "text": "hello, world"},
        {"test_id": 2, "text": "bye!"},
    ]

    graph = Graph.graph_from_iter("data").reduce(
        operations.FirstReducer(),
        ["test_id"],
    )
    result = _run_graph(graph, data=data)

    assert result == expected


def test_join() -> None:
    data_left = [
        {"player_id": 1, "username": "XeroX"},
        {"player_id": 2, "username": "jay"},
        {"player_id": 3, "username": "Destroyer"},
    ]

    data_right = [
        {"game_id": 2, "player_id": 1, "score": 17},
        {"game_id": 3, "player_id": 1, "score": 22},
        {"game_id": 1, "player_id": 3, "score": 99},
    ]

    expected = [
        {"game_id": 2, "player_id": 1, "score": 17, "username": "XeroX"},
        {"game_id": 3, "player_id": 1, "score": 22, "username": "XeroX"},
        {"game_id": 1, "player_id": 3, "score": 99, "username": "Destroyer"},
    ]

    graph_left = Graph.graph_from_iter("data_left")
    graph_right = Graph.graph_from_iter("data_right")

    graph = graph_left.join(
        operations.InnerJoiner(),
        graph_right,
        ["player_id"],
    )

    result = _run_graph(
        graph,
        data_left=data_left,
        data_right=data_right,
    )

    assert result == expected


def test_sort() -> None:
    data = [
        {"game_id": 2, "player_id": 1, "score": 17},
        {"game_id": 5, "player_id": 1, "score": 34},
        {"game_id": 3, "player_id": 2, "score": 22},
        {"game_id": 4, "player_id": 2, "score": 41},
        {"game_id": 1, "player_id": 3, "score": 0},
    ]

    expected = [
        {"game_id": 1, "player_id": 3, "score": 0},
        {"game_id": 2, "player_id": 1, "score": 17},
        {"game_id": 3, "player_id": 2, "score": 22},
        {"game_id": 5, "player_id": 1, "score": 34},
        {"game_id": 4, "player_id": 2, "score": 41},
    ]

    graph = Graph.make_graph("data").sort(["score"])
    result = _run_graph(graph, data=data)

    assert result == expected


# --- Graph reusability / independence ----------------------------------------


def test_independence_of_word_count() -> None:
    graph = algorithms.word_count_graph(
        "docs",
        text_column="text",
        count_column="count",
    )

    docs = [
        {"doc_id": 1, "text": "hello, my little WORLD"},
        {"doc_id": 2, "text": "Hello, my little little hell"},
    ]

    expected = [
        {"count": 1, "text": "hell"},
        {"count": 1, "text": "world"},
        {"count": 2, "text": "hello"},
        {"count": 2, "text": "my"},
        {"count": 3, "text": "little"},
    ]

    result1 = _run_graph(graph, docs=docs)
    result2 = _run_graph(graph, docs=docs)

    assert result1 == expected
    assert result2 == expected
    assert result1 == result2


def test_independence_of_tf_idf() -> None:
    graph = algorithms.inverted_index_graph(
        "texts",
        doc_column="doc_id",
        text_column="text",
        result_column="tf_idf",
    )

    rows = [
        {"doc_id": 1, "text": "hello, little world"},
        {"doc_id": 2, "text": "little"},
        {"doc_id": 3, "text": "little little little"},
        {"doc_id": 4, "text": "little? hello little world"},
        {"doc_id": 5, "text": "HELLO HELLO! WORLD..."},
        {"doc_id": 6, "text": "world? world... world!!! WORLD!!! HELLO!!!"},
    ]

    expected = [
        {"doc_id": 1, "text": "hello", "tf_idf": approx(0.1351, 0.001)},
        {"doc_id": 1, "text": "world", "tf_idf": approx(0.1351, 0.001)},
        {"doc_id": 2, "text": "little", "tf_idf": approx(0.4054, 0.001)},
        {"doc_id": 3, "text": "little", "tf_idf": approx(0.4054, 0.001)},
        {"doc_id": 4, "text": "hello", "tf_idf": approx(0.1013, 0.001)},
        {"doc_id": 4, "text": "little", "tf_idf": approx(0.2027, 0.001)},
        {"doc_id": 5, "text": "hello", "tf_idf": approx(0.2703, 0.001)},
        {"doc_id": 5, "text": "world", "tf_idf": approx(0.1351, 0.001)},
        {"doc_id": 6, "text": "world", "tf_idf": approx(0.3243, 0.001)},
    ]

    result1 = _run_graph(graph, texts=rows)
    result2 = _run_graph(graph, texts=rows)

    key = itemgetter("doc_id", "text")

    assert sorted(result1, key=key) == expected
    assert sorted(result2, key=key) == expected
    assert result1 == result2


def test_independence_of_pmi() -> None:
    graph = algorithms.pmi_graph(
        "texts",
        doc_column="doc_id",
        text_column="text",
        result_column="pmi",
    )

    rows = [
        {"doc_id": 1, "text": "hello, little world"},
        {"doc_id": 2, "text": "little"},
        {"doc_id": 3, "text": "little little little"},
        {"doc_id": 4, "text": "little? hello little world"},
        {"doc_id": 5, "text": "HELLO HELLO! WORLD..."},
        {
            "doc_id": 6,
            "text": "world? world... world!!! WORLD!!! HELLO!!! HELLO!!!!!!!",
        },
    ]

    expected = [
        {"doc_id": 3, "text": "little", "pmi": approx(0.9555, 0.001)},
        {"doc_id": 4, "text": "little", "pmi": approx(0.9555, 0.001)},
        {"doc_id": 5, "text": "hello", "pmi": approx(1.1786, 0.001)},
        {"doc_id": 6, "text": "world", "pmi": approx(0.7731, 0.001)},
        {"doc_id": 6, "text": "hello", "pmi": approx(0.0800, 0.001)},
    ]

    result1 = _run_graph(graph, texts=rows)
    result2 = _run_graph(graph, texts=rows)

    assert result1 == expected
    assert result2 == expected
    assert result1 == result2


def test_independence_of_yandex_maps() -> None:
    graph = algorithms.yandex_maps_graph(
        "travel_time",
        "edge_length",
        enter_time_column="enter_time",
        leave_time_column="leave_time",
        edge_id_column="edge_id",
        start_coord_column="start",
        end_coord_column="end",
        weekday_result_column="weekday",
        hour_result_column="hour",
        speed_result_column="speed",
    )

    lengths = [
        {
            "start": [37.84870228730142, 55.73853974696249],
            "end": [37.8490418381989, 55.73832445777953],
            "edge_id": 8414926848168493057,
        },
        {
            "start": [37.524768467992544, 55.88785375468433],
            "end": [37.52415172755718, 55.88807155843824],
            "edge_id": 5342768494149337085,
        },
        {
            "start": [37.56963176652789, 55.846845586784184],
            "end": [37.57018438540399, 55.8469259692356],
            "edge_id": 5123042926973124604,
        },
        {
            "start": [37.41463478654623, 55.654487907886505],
            "end": [37.41442892700434, 55.654839486815035],
            "edge_id": 5726148664276615162,
        },
        {
            "start": [37.584684155881405, 55.78285809606314],
            "end": [37.58415022864938, 55.78177368734032],
            "edge_id": 451916977441439743,
        },
        {
            "start": [37.736429711803794, 55.62696328852326],
            "end": [37.736344216391444, 55.626937723718584],
            "edge_id": 7639557040160407543,
        },
        {
            "start": [37.83196756616235, 55.76662947423756],
            "end": [37.83191015012562, 55.766647034324706],
            "edge_id": 1293255682152955894,
        },
    ]

    times = [
        {
            "leave_time": "20171020T112238.723000",
            "enter_time": "20171020T112237.427000",
            "edge_id": 8414926848168493057,
        },
        {
            "leave_time": "20171011T145553.040000",
            "enter_time": "20171011T145551.957000",
            "edge_id": 8414926848168493057,
        },
        {
            "leave_time": "20171020T090548.939000",
            "enter_time": "20171020T090547.463000",
            "edge_id": 8414926848168493057,
        },
        {
            "leave_time": "20171024T144101.879000",
            "enter_time": "20171024T144059.102000",
            "edge_id": 8414926848168493057,
        },
        {
            "leave_time": "20171022T131828.330000",
            "enter_time": "20171022T131820.842000",
            "edge_id": 5342768494149337085,
        },
        {
            "leave_time": "20171014T134826.836000",
            "enter_time": "20171014T134825.215000",
            "edge_id": 5342768494149337085,
        },
        {
            "leave_time": "20171010T060609.897000",
            "enter_time": "20171010T060608.344000",
            "edge_id": 5342768494149337085,
        },
        {
            "leave_time": "20171027T082600.201000",
            "enter_time": "20171027T082557.571000",
            "edge_id": 5342768494149337085,
        },
    ]

    expected = [
        {"weekday": "Fri", "hour": 8, "speed": approx(62.2322, 0.001)},
        {"weekday": "Fri", "hour": 9, "speed": approx(78.1070, 0.001)},
        {"weekday": "Fri", "hour": 11, "speed": approx(88.9552, 0.001)},
        {"weekday": "Sat", "hour": 13, "speed": approx(100.9690, 0.001)},
        {"weekday": "Sun", "hour": 13, "speed": approx(21.8577, 0.001)},
        {"weekday": "Tue", "hour": 6, "speed": approx(105.3901, 0.001)},
        {"weekday": "Tue", "hour": 14, "speed": approx(41.5145, 0.001)},
        {"weekday": "Wed", "hour": 14, "speed": approx(106.4505, 0.001)},
    ]

    result1 = list(
        graph.run(
            travel_time=lambda: islice(cycle(iter(times)), len(times)),
            edge_length=lambda: iter(lengths),
        )
    )
    result2 = list(
        graph.run(
            travel_time=lambda: islice(cycle(iter(times)), len(times)),
            edge_length=lambda: iter(lengths),
        )
    )

    key = itemgetter("weekday", "hour")

    assert result1 == result2
    assert sorted(result1, key=key) == expected
    assert sorted(result2, key=key) == expected
