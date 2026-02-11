"""Tests for format_plugin module: OutputKind, FormatResult, FormatPlugin Protocol."""

from dataclasses import FrozenInstanceError

import networkx as nx
import pytest

from knows.format_plugin import ConvertContext, FormatPlugin, FormatResult, OutputKind


def test_output_kind_values():
    assert OutputKind.TEXT.value == "text"
    assert OutputKind.BINARY.value == "binary"
    assert OutputKind.MULTI_FILE.value == "multi_file"


def test_format_result_text():
    result = FormatResult(data="hello", kind=OutputKind.TEXT, default_extension=".txt")
    assert result.data == "hello"
    assert result.kind == OutputKind.TEXT
    assert result.default_extension == ".txt"


def test_format_result_binary():
    result = FormatResult(data=b"\x89PNG", kind=OutputKind.BINARY, default_extension=".png")
    assert isinstance(result.data, bytes)


def test_format_result_multi_file():
    result = FormatResult(
        data={"_nodes.csv": "a,b", "_edges.csv": "c,d"},
        kind=OutputKind.MULTI_FILE,
        default_extension=".csv",
    )
    assert isinstance(result.data, dict)
    assert len(result.data) == 2


def test_format_result_frozen():
    result = FormatResult(data="x", kind=OutputKind.TEXT, default_extension=".txt")
    with pytest.raises(FrozenInstanceError):
        result.data = "y"


class _DummyPlugin:
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def description(self) -> str:
        return "A dummy format"

    @property
    def output_kind(self) -> OutputKind:
        return OutputKind.TEXT

    @property
    def default_extension(self) -> str:
        return ".dummy"

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        return FormatResult(data="dummy", kind=OutputKind.TEXT, default_extension=".dummy")


def test_protocol_isinstance_check():
    plugin = _DummyPlugin()
    assert isinstance(plugin, FormatPlugin)


def test_protocol_rejects_non_conforming():
    class _Bad:
        pass

    assert not isinstance(_Bad(), FormatPlugin)
