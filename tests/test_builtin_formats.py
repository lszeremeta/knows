"""Parametrized tests for all 14 built-in format plugins via the registry."""

import csv
import io
import math

import pytest

from knows.format_plugin import ConvertContext, FormatPlugin, FormatResult, OutputKind
from knows.format_registry import FormatRegistry
from knows.graph import Graph


@pytest.fixture(autouse=True)
def _reset_registry():
    """Isolate each test from the format registry singleton cache."""
    FormatRegistry().reset()
    yield
    FormatRegistry().reset()


@pytest.fixture
def small_graph():
    """Create a small generated graph shared by format smoke tests."""
    graph = Graph(3, 2)
    graph.generate()
    return graph.graph


TEXT_FORMATS = [
    'graphml', 'yarspg', 'cypher', 'gexf', 'gml',
    'adjacency_list', 'multiline_adjacency_list', 'edge_list', 'json',
]

BINARY_FORMATS = ['png', 'jpg', 'pdf']


@pytest.mark.parametrize("name", TEXT_FORMATS)
def test_text_format_produces_string(small_graph, name):
    """Each text plugin should return a non-empty text result."""
    plugin = FormatRegistry().get(name)
    assert isinstance(plugin, FormatPlugin)
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert isinstance(result, FormatResult)
    assert result.kind == OutputKind.TEXT
    assert isinstance(result.data, str)
    assert len(result.data) > 0


@pytest.mark.parametrize("name", BINARY_FORMATS)
def test_binary_format_produces_bytes(small_graph, name):
    """Each binary plugin should return a non-empty byte sequence."""
    plugin = FormatRegistry().get(name)
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert result.kind == OutputKind.BINARY
    assert isinstance(result.data, bytes)
    assert len(result.data) > 0


def test_svg_is_text_format(small_graph):
    """SVG output should be returned as text containing an SVG element."""
    plugin = FormatRegistry().get('svg')
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert result.kind == OutputKind.TEXT
    assert '<svg' in result.data


def test_csv_is_multi_file(small_graph):
    """CSV conversion should return separate node and edge files."""
    plugin = FormatRegistry().get('csv')
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert result.kind == OutputKind.MULTI_FILE
    assert isinstance(result.data, dict)
    assert '_nodes.csv' in result.data
    assert '_edges.csv' in result.data


def test_csv_preserves_quoted_and_trailing_whitespace_values():
    """CSV round-tripping should preserve quoting, newlines, and trailing spaces."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node(
        'N1',
        label='Person',
        note='comma, quote " and newline\n',
        tail='ends with spaces   ',
    )
    graph.add_node('N2', label='Person')
    graph.add_edge('N1', 'N2', label='knows', tail='edge spaces   ')

    result = FormatRegistry().get('csv').convert(graph, ConvertContext())
    node_rows = list(csv.DictReader(io.StringIO(result.data['_nodes.csv'])))
    edge_rows = list(csv.DictReader(io.StringIO(result.data['_edges.csv'])))

    assert node_rows[0]['note'] == 'comma, quote " and newline\n'
    assert node_rows[0]['tail'] == 'ends with spaces   '
    assert edge_rows[0]['tail'] == 'edge spaces   '


@pytest.fixture
def tricky_graph():
    """Graph with values that need escaping and non-string types."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node(
        'N1',
        label='Person',
        address='12 Main St\nSpringfield',
        note='He said "hi"',
        controls='tab\tback\bform\freturn\r',
    )
    graph.add_node('N2', label='Person', address='Backslash \\ path', note='plain')
    graph.add_edge(
        'N1', 'N2', label='knows', strength=59, active=True, archived=False,
    )
    return graph


def test_cypher_escapes_special_characters(tricky_graph):
    """Cypher strings should escape quotes, slashes, and control whitespace."""
    plugin = FormatRegistry().get('cypher')
    result = plugin.convert(tricky_graph, ConvertContext())
    assert '"12 Main St\\nSpringfield"' in result.data
    assert '"He said \\"hi\\""' in result.data
    assert '"Backslash \\\\ path"' in result.data
    assert '"tab\\tback\\bform\\freturn\\r"' in result.data


def test_cypher_preserves_value_types(tricky_graph):
    """Cypher output should retain numeric and Boolean literal types."""
    plugin = FormatRegistry().get('cypher')
    result = plugin.convert(tricky_graph, ConvertContext())
    assert '`strength`: 59' in result.data
    assert '`active`: true' in result.data


def test_cypher_formats_special_float_values():
    """Cypher output should use valid literals for non-finite floats."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node(
        'N1',
        label='Number',
        nan=math.nan,
        positive_infinity=math.inf,
        negative_infinity=-math.inf,
    )
    result = FormatRegistry().get('cypher').convert(graph, ConvertContext())
    assert '`nan`: NaN' in result.data
    assert '`positive_infinity`: Infinity' in result.data
    assert '`negative_infinity`: -Infinity' in result.data


def test_cypher_quotes_non_identifier_labels():
    """Cypher labels containing spaces should be backtick-quoted."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node('N1', label='My Node')
    plugin = FormatRegistry().get('cypher')
    result = plugin.convert(graph, ConvertContext())
    assert '(`N1`:`My Node` ' in result.data


def test_cypher_quotes_non_identifier_property_keys():
    """Cypher property keys should escape special and control characters."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node(
        'N1',
        label='Person',
        **{
            'first name': 'Alice',
            'tick`key': 'value',
            r'\u0060key': 'unicode',
            'path\\key': 'backslash',
            'null\x00key': 'control',
            'tab\tkey': 'whitespace',
        },
    )
    plugin = FormatRegistry().get('cypher')
    result = plugin.convert(graph, ConvertContext())
    assert '`first name`: "Alice"' in result.data
    assert '`tick``key`: "value"' in result.data
    assert r'`\u005Cu0060key`: "unicode"' in result.data
    assert r'`path\u005Ckey`: "backslash"' in result.data
    assert r'`null\u0000key`: "control"' in result.data
    assert r'`tab\u0009key`: "whitespace"' in result.data


def test_cypher_quotes_non_identifier_node_ids():
    """Cypher node identifiers should be quoted and escaped consistently."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node('node 1', label='Person')
    graph.add_node('tick`id', label='Person')
    graph.add_edge('node 1', 'tick`id', label='knows')
    result = FormatRegistry().get('cypher').convert(graph, ConvertContext())
    assert 'CREATE (`node 1`:`Person` {})' in result.data
    assert 'CREATE (`tick``id`:`Person` {})' in result.data
    assert 'CREATE (`node 1`)-[:`knows` {}]->(`tick``id`)' in result.data


def test_cypher_quotes_keyword_identifiers():
    """Cypher keywords used as names should remain valid quoted identifiers."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node('MATCH', label='CREATE', **{'RETURN': 'value'})
    graph.add_node('N2', label='Node')
    graph.add_edge('MATCH', 'N2', label='DELETE', **{'SET': True})

    result = FormatRegistry().get('cypher').convert(graph, ConvertContext())

    assert 'CREATE (`MATCH`:`CREATE` {`RETURN`: "value"})' in result.data
    assert 'CREATE (`MATCH`)-[:`DELETE` {`SET`: true}]->(`N2`)' in result.data


def test_cypher_handles_missing_labels_explicitly():
    """Cypher should allow unlabeled nodes but reject unlabeled relationships."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node('N1')
    result = FormatRegistry().get('cypher').convert(graph, ConvertContext())
    assert result.data == 'CREATE (`N1` {})'

    graph.add_node('N2')
    graph.add_edge('N1', 'N2')
    with pytest.raises(ValueError, match='non-empty label'):
        FormatRegistry().get('cypher').convert(graph, ConvertContext())


def test_yarspg_quotes_and_escapes_all_values(tricky_graph):
    """YARS-PG should quote values and escape supported special characters."""
    plugin = FormatRegistry().get('yarspg')
    result = plugin.convert(tricky_graph, ConvertContext())
    assert '"address": "12 Main St\\nSpringfield"' in result.data
    assert '"note": "He said \\"hi\\""' in result.data
    assert '"strength": "59"' in result.data
    assert '"active": "true"' in result.data
    assert '"archived": "false"' in result.data


def test_yarspg_emits_control_characters_per_grammar():
    """YARS-PG escapes named whitespace controls and emits other control bytes raw."""
    import networkx as nx

    nul, soh = chr(0), chr(1)
    graph = nx.DiGraph()
    graph.add_node('N1', label='Person', mixed='tab\there' + nul + 'nul' + soh + 'soh')
    result = FormatRegistry().get('yarspg').convert(graph, ConvertContext())
    assert '"mixed": "tab\\there' + nul + 'nul' + soh + 'soh"' in result.data


def test_yarspg_rejects_invalid_node_identifiers():
    """YARS-PG should reject node identifiers outside its allowed syntax."""
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_node('node 1', label='Person')
    plugin = FormatRegistry().get('yarspg')
    with pytest.raises(ValueError, match='Invalid YARS-PG node identifier'):
        plugin.convert(graph, ConvertContext())


def test_all_plugins_have_required_properties():
    """Every discovered plugin should expose valid format metadata."""
    for name in FormatRegistry().names():
        plugin = FormatRegistry().get(name)
        assert isinstance(plugin.name, str)
        assert isinstance(plugin.description, str)
        assert isinstance(plugin.output_kind, OutputKind)
        assert isinstance(plugin.default_extension, str)
        assert plugin.default_extension.startswith('.')
