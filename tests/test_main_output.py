"""Tests for writing graph output files from the main entry point."""

import pytest

from knows.__main__ import main


@pytest.mark.parametrize(
    "fmt, ext, marker",
    [
        ("graphml", ".graphml", "<graphml"),
        ("yarspg", ".yarspg", "->"),
        ("cypher", ".cypher", "CREATE"),
        ("gexf", ".gexf", "<gexf"),
        ("gml", ".gml", "graph"),
        ("svg", ".svg", "<svg"),
        ("adjacency_list", ".adj", "N"),
        ("multiline_adjacency_list", ".adj", "N"),
        ("edge_list", ".edgelist", "N"),
        ("json", ".json", "\"nodes\""),
    ],
)
def test_main_writes_single_file_formats(tmp_path, monkeypatch, fmt, ext, marker):
    """Ensure `main` writes a file when given an output path for non-CSV formats.

    Args:
        tmp_path (pathlib.Path): Temporary directory for output files.
        monkeypatch: A pytest fixture for monkey-patching ``sys.argv``.
        fmt (str): Output format to test.
        ext (str): File extension to use for the output file.
        marker (str): Substring expected in the written file.
    """
    output = tmp_path / f"graph{ext}"
    monkeypatch.setattr('sys.argv', ['prog', '-n', '3', '-e', '2', '-f', fmt, str(output)])
    main()
    assert output.exists()
    content = output.read_text()
    assert marker in content


@pytest.mark.parametrize(
    "fmt, ext, signature",
    [
        ("png", ".png", b"\x89PNG"),
        ("jpg", ".jpg", b"\xff\xd8"),
        ("pdf", ".pdf", b"%PDF"),
    ],
)
def test_main_writes_binary_file_formats(tmp_path, monkeypatch, fmt, ext, signature):
    """Ensure `main` writes binary files for image/PDF formats."""
    output = tmp_path / f"graph{ext}"
    monkeypatch.setattr('sys.argv', ['prog', '-n', '3', '-e', '2', '-f', fmt, str(output)])
    main()
    assert output.exists()
    content = output.read_bytes()
    assert content.startswith(signature)


def test_main_writes_csv_files(tmp_path, monkeypatch):
    """Ensure `main` writes CSV nodes and edges files when CSV format is chosen.

    Args:
        tmp_path (pathlib.Path): Temporary directory for output files.
        monkeypatch: A pytest fixture for monkey-patching ``sys.argv``.
    """
    output = tmp_path / "graph"
    monkeypatch.setattr('sys.argv', ['prog', '-n', '3', '-e', '2', '-f', 'csv', str(output)])
    main()
    nodes = tmp_path / "graph_nodes.csv"
    edges = tmp_path / "graph_edges.csv"
    assert nodes.exists()
    assert edges.exists()
    assert 'id' in nodes.read_text()
    assert 'id_from' in edges.read_text()
