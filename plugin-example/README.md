# knows-ndjson (Example Plugin)

An example external format plugin for [Knows](https://github.com/lszeremeta/knows). Exports graphs as
[NDJSON (JSON Lines)](https://jsonlines.org/) - one JSON object per line, first all nodes then all edges.

This project serves as a **template** for creating your own Knows format plugins. Copy the directory, rename the
package, and replace the conversion logic.

## Installation

From the `plugin-example/` directory:

```shell
pip install -e .
```

The `ndjson` format is now available in Knows automatically:

```shell
knows -f ndjson
knows -n 10 -e 5 -f ndjson graph.ndjson
```

## Project Structure

```
plugin-example/
├── pyproject.toml              # Package metadata + entry-point registration
├── knows_ndjson/
│   ├── __init__.py
│   └── plugin.py               # NdjsonFormat class + create_plugin() factory
└── tests/
    └── test_ndjson_plugin.py
```

## Running Tests

```shell
pip install -e ".[test]"
pytest tests/ -v
```

## How It Works

The plugin registers itself via the `knows.formats` entry-point group in `pyproject.toml`. At startup, Knows discovers
it and adds `ndjson` to the available `--format` choices. See
[PLUGINS.md](https://github.com/lszeremeta/knows/blob/main/PLUGINS.md) for the full plugin development guide.
