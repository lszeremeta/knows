"""Tests for FormatRegistry: discovery, singleton, reset, errors, mock plugins."""

from unittest.mock import patch, MagicMock

import networkx as nx
import pytest

from knows.format_plugin import ConvertContext, FormatPlugin, FormatResult, OutputKind
from knows.format_registry import FormatRegistry


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset the registry singleton before and after each test."""
    FormatRegistry().reset()
    yield
    FormatRegistry().reset()


def test_singleton():
    a = FormatRegistry()
    b = FormatRegistry()
    assert a is b


def test_names_returns_list():
    names = FormatRegistry().names()
    assert isinstance(names, list)
    assert 'yarspg' in names
    assert 'graphml' in names
    assert len(names) >= 14  # 14 built-in + any installed external plugins


def test_get_known_format():
    plugin = FormatRegistry().get('graphml')
    assert isinstance(plugin, FormatPlugin)
    assert plugin.name == 'graphml'


def test_get_unknown_format():
    with pytest.raises(KeyError, match="Unknown format"):
        FormatRegistry().get('nonexistent')


def test_reset_clears_cache():
    reg = FormatRegistry()
    reg.names()  # trigger discovery
    reg.reset()
    # After reset, next access should re-discover
    assert 'yarspg' in reg.names()


def test_mock_external_plugin():
    """Simulate an external plugin entry point."""
    class _ExternalPlugin:
        @property
        def name(self):
            return "custom_fmt"

        @property
        def description(self):
            return "Custom"

        @property
        def output_kind(self):
            return OutputKind.TEXT

        @property
        def default_extension(self):
            return ".custom"

        def convert(self, graph, ctx):
            return FormatResult(data="custom", kind=OutputKind.TEXT, default_extension=".custom")

    mock_ep = MagicMock()
    mock_ep.name = "custom"
    mock_ep.load.return_value = lambda: [_ExternalPlugin()]

    from importlib.metadata import entry_points as real_ep

    def patched_entry_points(group):
        real = list(real_ep(group=group))
        return real + [mock_ep]

    reg = FormatRegistry()
    reg.reset()

    with patch("knows.format_registry.entry_points", side_effect=patched_entry_points):
        reg._discover()

    assert "custom_fmt" in reg.names()
    result = reg.get("custom_fmt").convert(nx.DiGraph(), ConvertContext(viz_limit=50, show_info=True))
    assert result.data == "custom"


def test_broken_plugin_warns():
    """A broken entry point emits a warning but doesn't crash."""
    mock_ep = MagicMock()
    mock_ep.name = "broken"
    mock_ep.load.side_effect = ImportError("no such module")

    from importlib.metadata import entry_points as real_ep

    def patched_entry_points(group):
        real = list(real_ep(group=group))
        return real + [mock_ep]

    reg = FormatRegistry()
    reg.reset()

    with patch("knows.format_registry.entry_points", side_effect=patched_entry_points):
        with pytest.warns(match="Failed to load format plugin"):
            reg._discover()

    # Built-in formats should still be available
    assert 'yarspg' in reg.names()
