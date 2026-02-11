"""Parametrized tests for all 14 built-in format plugins via the registry."""

import pytest

from knows.format_plugin import ConvertContext, FormatPlugin, FormatResult, OutputKind
from knows.format_registry import FormatRegistry
from knows.graph import Graph


@pytest.fixture(autouse=True)
def _reset_registry():
    FormatRegistry().reset()
    yield
    FormatRegistry().reset()


@pytest.fixture
def small_graph():
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
    plugin = FormatRegistry().get(name)
    assert isinstance(plugin, FormatPlugin)
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert isinstance(result, FormatResult)
    assert result.kind == OutputKind.TEXT
    assert isinstance(result.data, str)
    assert len(result.data) > 0


@pytest.mark.parametrize("name", BINARY_FORMATS)
def test_binary_format_produces_bytes(small_graph, name):
    plugin = FormatRegistry().get(name)
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert result.kind == OutputKind.BINARY
    assert isinstance(result.data, bytes)
    assert len(result.data) > 0


def test_svg_is_text_format(small_graph):
    plugin = FormatRegistry().get('svg')
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert result.kind == OutputKind.TEXT
    assert '<svg' in result.data


def test_csv_is_multi_file(small_graph):
    plugin = FormatRegistry().get('csv')
    result = plugin.convert(small_graph, ConvertContext(viz_limit=50, show_info=True))
    assert result.kind == OutputKind.MULTI_FILE
    assert isinstance(result.data, dict)
    assert '_nodes.csv' in result.data
    assert '_edges.csv' in result.data


def test_all_plugins_have_required_properties():
    for name in FormatRegistry().names():
        plugin = FormatRegistry().get(name)
        assert isinstance(plugin.name, str)
        assert isinstance(plugin.description, str)
        assert isinstance(plugin.output_kind, OutputKind)
        assert isinstance(plugin.default_extension, str)
        assert plugin.default_extension.startswith('.')
