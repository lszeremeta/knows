"""Tests for the NDJSON format plugin."""

import json

import networkx as nx
from knows.format_plugin import ConvertContext, FormatPlugin, OutputKind

from knows_ndjson.plugin import NdjsonFormat, create_plugin


def test_satisfies_protocol():
    """The plugin must pass the FormatPlugin isinstance check."""
    assert isinstance(NdjsonFormat(), FormatPlugin)


def test_factory_returns_plugin():
    """The entry-point factory must return a valid plugin."""
    plugin = create_plugin()
    assert isinstance(plugin, FormatPlugin)
    assert plugin.name == "ndjson"


def test_convert_produces_ndjson_output():
    """Basic NDJSON output must contain one JSON object per line."""
    plugin = NdjsonFormat()
    graph = nx.DiGraph()
    graph.add_node("N1", label="Person", firstName="Alice")
    graph.add_node("N2", label="Person", firstName="Bob")
    graph.add_edge("N1", "N2", label="knows")

    result = plugin.convert(graph, ConvertContext(viz_limit=50, show_info=True))

    assert result.kind == OutputKind.TEXT
    assert result.default_extension == ".ndjson"

    lines = result.data.splitlines()
    assert len(lines) == 3  # 2 nodes + 1 edge

    node1 = json.loads(lines[0])
    assert node1["type"] == "node"
    assert node1["id"] == "N1"
    assert node1["firstName"] == "Alice"

    edge = json.loads(lines[2])
    assert edge["type"] == "edge"
    assert edge["source"] == "N1"
    assert edge["target"] == "N2"


def test_empty_graph():
    """An empty graph should produce empty output."""
    result = NdjsonFormat().convert(nx.DiGraph(), ConvertContext(viz_limit=50, show_info=True))
    assert result.data == ""
