"""NDJSON (JSON Lines) format plugin for Knows.

Exports the graph as newline-delimited JSON: one JSON object per line,
first all nodes then all edges.  See https://jsonlines.org/ for the
format specification.

This module serves as a complete, working example of an external format
plugin.  Copy this project, rename the package, and replace the
conversion logic with your own.
"""

import json

import networkx as nx
from knows.format_plugin import ConvertContext, FormatResult, OutputKind


class NdjsonFormat:
    """Export a graph as NDJSON (one JSON object per line).

    No base-class inheritance is needed - Knows checks the protocol
    structurally (duck typing).
    """

    @property
    def name(self) -> str:
        return "ndjson"

    @property
    def description(self) -> str:
        return "NDJSON (JSON Lines) format"

    @property
    def output_kind(self) -> OutputKind:
        return OutputKind.TEXT

    @property
    def default_extension(self) -> str:
        return ".ndjson"

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        """Convert *graph* to NDJSON.

        Each line is a JSON object with a ``"type"`` key (``"node"`` or
        ``"edge"``) and the corresponding properties.

        Args:
            graph: The NetworkX directed graph to convert.
            ctx: Conversion parameters (unused for this text format).
        """
        lines: list[str] = []
        for node_id, props in graph.nodes(data=True):
            record = {"type": "node", "id": node_id, **props}
            lines.append(json.dumps(record, ensure_ascii=False))
        for source, target, props in graph.edges(data=True):
            record = {"type": "edge", "source": source, "target": target, **props}
            lines.append(json.dumps(record, ensure_ascii=False))
        return FormatResult(
            data="\n".join(lines),
            kind=OutputKind.TEXT,
            default_extension=".ndjson",
        )


def create_plugin() -> NdjsonFormat:
    """Entry-point factory called by Knows at startup."""
    return NdjsonFormat()
