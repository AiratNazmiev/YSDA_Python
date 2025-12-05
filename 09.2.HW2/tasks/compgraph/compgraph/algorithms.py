from .graph import Graph
import compgraph.operations as ops


def word_count_graph(
    input_stream_name: str,
    text_column: str = "text",
    count_column: str = "count",
    file: bool = False,
) -> Graph:
    """
    Construct a computation graph that counts word occurrences in a text column.

    The input is expected to be a stream of rows, each containing a text field.
    The resulting graph will:

    1. Remove punctuation from the text.
    2. Convert the text to lowercase.
    3. Split the text into separate words.
    4. Count how many times each word appears.
    5. Sort the result by count and then by word.

    Args:
        input_stream_name: Name or identifier of the input data stream.
        text_column: Name of the column containing raw text.
        count_column: Name of the column in which the word counts will be stored.
        file: Whether the input stream comes from a file-backed source.

    Returns:
        Graph: A graph that produces a table of (word, count) pairs.
    """

    return (
        Graph.make_graph(input_stream_name, file)
        .map(ops.FilterPunctuation(text_column))
        .map(ops.LowerCase(text_column))
        .map(ops.Split(text_column))
        .sort([text_column])
        .reduce(ops.Count(count_column), [text_column])
        .sort([count_column, text_column])
    )


def inverted_index_graph(
    input_stream_name: str,
    doc_column: str = "doc_id",
    text_column: str = "text",
    result_column: str = "tf_idf",
    file: bool = False,
) -> Graph:
    """
    Construct a computation graph that calculates TF-IDF for each (word, document) pair.

    The pipeline performs the following steps:

    1. Preprocess text (remove punctuation, lowercase, split into words).
    2. Compute:
       - `docs_count`: total number of documents.
       - `docs_with_word`: number of documents containing each word.
       - `idf`: inverse document frequency for each word.
       - `tf`: term frequency of each word in each document.
    3. Compute `tf_idf = tf * idf` for every (word, document) pair.
    4. For each word, keep the top 3 documents by TF-IDF.
    5. Project to (doc_column, text_column, result_column).

    Args:
        input_stream_name: Name or identifier of the input data stream.
        doc_column: Name of the document identifier column.
        text_column: Name of the column containing raw text.
        result_column: Name of the resulting TF-IDF column.
        file: Whether the input stream comes from a file-backed source.

    Returns:
        Graph: A graph that produces a table of (doc_id, word, tf_idf) rows.
    """

    split_words_graph = (
        Graph.make_graph(input_stream_name, file)
        .map(ops.FilterPunctuation(text_column))
        .map(ops.LowerCase(text_column))
        .map(ops.Split(text_column))
    )

    count_docs_graph = (
        Graph.make_graph(input_stream_name, file)
        .reduce(ops.Count("docs_count"), [])
    )

    idf_graph = (
        split_words_graph.sort([doc_column, text_column])
        .reduce(ops.FirstReducer(), [doc_column, text_column])
        .sort([text_column])
        .reduce(ops.Count("docs_with_word"), [text_column])
        .join(ops.InnerJoiner(), count_docs_graph, [])
        .map(ops.IDF(["docs_count", "docs_with_word"], "idf"))
    )

    tf_graph = (
        split_words_graph.sort([doc_column])
        .reduce(ops.TermFrequency(text_column), [doc_column])
    )

    return (
        tf_graph.sort([text_column])
        .join(ops.InnerJoiner(), idf_graph, [text_column])
        .map(ops.Product(["tf", "idf"], result_column))
        .sort([text_column])
        .reduce(ops.TopN(result_column, n=3), [text_column])
        .map(ops.Project([doc_column, text_column, result_column]))
    )


def pmi_graph(
    input_stream_name: str,
    doc_column: str = "doc_id",
    text_column: str = "text",
    result_column: str = "pmi",
    file: bool = False,
) -> Graph:
    """
    Construct a computation graph that computes pointwise mutual information (PMI)
    between documents and words and returns the top 10 words per document by PMI.

    The pipeline roughly does:

    1. Preprocess text:
       - remove punctuation,
       - lowercase,
       - split into words,
       - filter out short words (<= 4 characters),
       - count how many times each word appears in each document,
       - filter out rare words in a document (`word_in_doc_count` < 2).
    2. Compute term frequency per document (`tf`) for the filtered words.
    3. Compute global frequency of each word across all documents (`freq_in_all`).
    4. Join per-document frequencies with global frequencies and compute PMI.
    5. For each document, keep top 10 words by PMI.
    6. Sort results by document and PMI.

    Args:
        input_stream_name: Name or identifier of the input data stream.
        doc_column: Name of the document identifier column.
        text_column: Name of the column containing raw text.
        result_column: Name of the resulting PMI score column.
        file: Whether the input stream comes from a file-backed source.

    Returns:
        Graph: A graph producing (doc_id, word, pmi) rows, top 10 per document.
    """

    filtered_word_occurrences_graph = (
        Graph.make_graph(input_stream_name, file)
        .map(ops.FilterPunctuation(text_column))
        .map(ops.LowerCase(text_column))
        .map(ops.Split(text_column))
        .map(ops.Filter(condition=lambda row: len(row[text_column]) > 4))
        .sort([doc_column, text_column])
        .reduce(ops.Count("word_in_doc_count"), [doc_column, text_column])
        .map(ops.Filter(condition=lambda row: row["word_in_doc_count"] >= 2))
    )

    freq_of_word_in_doc_graph = (
        filtered_word_occurrences_graph.sort([doc_column])
        .reduce(
            ops.WeightedTermFrequency(
                text_column, "word_in_doc_count", result_column="tf"
            ),
            [doc_column],
        )
    )

    word_totals_graph = (
        filtered_word_occurrences_graph.sort([text_column])
        .reduce(ops.Sum("word_in_doc_count"), [text_column])
    )

    freq_of_word_in_all_graph = word_totals_graph.reduce(
        ops.WeightedTermFrequency(
            text_column, "word_in_doc_count", result_column="freq_in_all"
        ),
        [],
    )

    pmi_graph_inner = (
        freq_of_word_in_doc_graph.sort([text_column])
        .join(
            ops.InnerJoiner(),
            freq_of_word_in_all_graph.sort([text_column]),
            [text_column],
        )
        .map(ops.PMI(["tf", "freq_in_all"], result_column))
    )

    return (
        pmi_graph_inner.sort([doc_column])
        .map(ops.Project([doc_column, text_column, result_column]))
        .sort([doc_column])
        .reduce(ops.TopN(result_column, 10), [doc_column])
        .map(ops.Multiply(result_column, -1))
        .sort([doc_column, result_column])
        .map(ops.Multiply(result_column, -1))
    )


def yandex_maps_graph(
    input_stream_name_time: str,
    input_stream_name_length: str,
    enter_time_column: str = "enter_time",
    leave_time_column: str = "leave_time",
    edge_id_column: str = "edge_id",
    start_coord_column: str = "start",
    end_coord_column: str = "end",
    weekday_result_column: str = "weekday",
    hour_result_column: str = "hour",
    speed_result_column: str = "speed",
    file: bool = False,
) -> Graph:
    """
    Construct a computation graph that estimates average speed (km/h) by weekday and hour.

    Input is split into two streams:

    * Time stream:
        - Edge identifier and enter/leave times.
    * Length stream:
        - Edge identifier and coordinates (start, end).

    The pipeline performs:

    1. On the time stream:
       - Compute edge traversal duration.
       - Extract weekday and hour from the enter_time field.
       - Project to (edge_id, duration, weekday, hour).

    2. On the length stream:
       - Compute distance between coordinates using Haversine formula.
       - Project to (edge_id, distance).

    3. Join time and length streams on edge_id.

    4. For each (weekday, hour):
       - Sum distance and duration separately.
       - Join totals and compute average speed in km/h.

    5. Project to (weekday_result_column, hour_result_column, speed_result_column).

    Args:
        input_stream_name_time: Name of the time-related input stream.
        input_stream_name_length: Name of the length-related input stream.
        enter_time_column: Column containing the entry timestamp.
        leave_time_column: Column containing the exit timestamp.
        edge_id_column: Column identifying the road segment / edge.
        start_coord_column: Column with the starting coordinates of the edge.
        end_coord_column: Column with the ending coordinates of the edge.
        weekday_result_column: Name of the weekday column in the result.
        hour_result_column: Name of the hour column in the result.
        speed_result_column: Name of the average speed column in the result.
        file: Whether the input streams come from file-backed sources.

    Returns:
        Graph: A graph producing (weekday, hour, speed) style aggregate rows.
    """

    time_graph = (
        Graph.make_graph(input_stream_name_time, file)
        .map(ops.GetDuration(enter_time_column, leave_time_column, "duration"))
        .map(
            ops.GetWeekdayAndHour(
                enter_time_column,
                weekday_result_column,
                hour_result_column,
            )
        )
        .map(
            ops.Project(
                [edge_id_column, "duration", weekday_result_column, hour_result_column]
            )
        )
    )

    length_graph = (
        Graph.make_graph(input_stream_name_length, file)
        .map(ops.GetHaversineDist(start_coord_column, end_coord_column, "distance"))
        .map(ops.Project([edge_id_column, "distance"]))
    )

    merged_graph = (
        time_graph.sort([edge_id_column])
        .join(
            ops.InnerJoiner(),
            length_graph.sort([edge_id_column]),
            [edge_id_column],
        )
        .sort([weekday_result_column, hour_result_column])
    )

    totals_graph = merged_graph.reduce(
        ops.SumColumns(["distance", "duration"]),
        [weekday_result_column, hour_result_column],
    )

    return (
        totals_graph
        .map(
            ops.GetAverageSpeed(
                "distance",
                "duration",
                speed_result_column,
            )
        )
        .map(
            ops.Project(
                [weekday_result_column, hour_result_column, speed_result_column]
            )
        )
    )
