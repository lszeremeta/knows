"""Tests for writing graph output files from the main entry point."""

import io

import pytest

from knows.__main__ import main
from knows.format_plugin import FormatResult, OutputKind
from knows.output_format import OutputFormat


class ReconfigurableStringIO(io.StringIO):
    """String buffer that records requested output encoding changes."""

    def __init__(self):
        """Initialize the buffer without a requested encoding."""
        super().__init__()
        self.configured_encoding = None

    def reconfigure(self, *, encoding):
        """Record the encoding requested by the CLI."""
        self.configured_encoding = encoding


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


def test_main_honors_zero_edges(tmp_path, monkeypatch):
    """`-e 0` must produce a graph with no edges (0 is a valid count)."""
    import json

    output = tmp_path / "graph.json"
    monkeypatch.setattr('sys.argv', ['prog', '-n', '5', '-e', '0', '-f', 'json', str(output)])
    main()
    data = json.loads(output.read_text())
    assert len(data['nodes']) == 5
    assert data['edges'] == []


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


def test_main_writes_mixed_multi_file_output_to_console(monkeypatch, capfdbinary):
    """MULTI_FILE output may contain both bytes and text."""
    result = FormatResult(
        data={'_first.bin': b'first', '_second.txt': 'second'},
        kind=OutputKind.MULTI_FILE,
        default_extension='.bin',
    )
    monkeypatch.setattr(OutputFormat, 'to_format', lambda self, fmt: result)
    monkeypatch.setattr('sys.argv', ['prog', '-n', '2', '-e', '0', '-f', 'csv'])

    main()

    captured = capfdbinary.readouterr()
    assert captured.out == b'first'
    assert captured.err == b'second\n'


def test_main_accepts_empty_multi_file_output(monkeypatch, capfdbinary):
    """An empty MULTI_FILE result should produce no console output."""
    result = FormatResult(
        data={},
        kind=OutputKind.MULTI_FILE,
        default_extension='.empty',
    )
    monkeypatch.setattr(OutputFormat, 'to_format', lambda self, fmt: result)
    monkeypatch.setattr('sys.argv', ['prog', '-n', '2', '-e', '0', '-f', 'csv'])

    main()

    captured = capfdbinary.readouterr()
    assert captured.out == b''
    assert captured.err == b''


def test_main_configures_stdout_and_stderr_as_utf8(monkeypatch):
    """The CLI should configure both text streams for localized UTF-8 output."""
    stdout = ReconfigurableStringIO()
    stderr = ReconfigurableStringIO()
    result = FormatResult(
        data={'_nodes.csv': 'Białystok', '_edges.csv': 'Tomaszów'},
        kind=OutputKind.MULTI_FILE,
        default_extension='.csv',
    )
    monkeypatch.setattr(OutputFormat, 'to_format', lambda self, fmt: result)
    monkeypatch.setattr('sys.argv', ['prog', '-n', '2', '-e', '0', '-f', 'csv'])
    monkeypatch.setattr('sys.stdout', stdout)
    monkeypatch.setattr('sys.stderr', stderr)

    main()

    assert stdout.configured_encoding == 'utf-8'
    assert stderr.configured_encoding == 'utf-8'
    assert stdout.getvalue() == 'Białystok\n'
    assert stderr.getvalue() == 'Tomaszów\n'
