# Compgraph Library

This repository implements a lightweight computation-graph framework for streaming MapReduce-like pipelines together with four example algorithms (word count, tf-idf inverted index, PMI-based keywords, and average travel speed in Moscow).

## Installation

```bash
uv pip install -e compgraph --force-reinstall
```

## Usage

The `examples/` directory now exposes runnable entry points for every algorithm. Each expects newline-delimited JSON with the columns described in the homework statement.

```bash
# 1. Word count
python examples/run_word_count.py resources/text_corpus.txt word_count.json

# 2. Inverted index with tf-idf
python examples/run_inverted_index.py resources/text_corpus.txt inverted_index.json

# 3. Keywords per document
python examples/run_pmi.py resources/text_corpus.txt pmi.json

# 4. Average speed by weekday/hour
python examples/run_yandex_maps.py resources/travel_times.txt resources/road_graph_data.txt speed.json
```

## Testing

Run the full suite (correctness, memory, and library-level tests):

```bash
pytest
```

For a test coverage check run:

```bash
pytest --cov=compgraph --cov-report=term-missing --cov-fail-under=95
```
