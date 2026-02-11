"""Built-in format plugins shipped with Knows.

All 14 standard output formats are implemented here as lightweight
classes that satisfy the :class:`~knows.format_plugin.FormatPlugin`
protocol.  They are registered via the ``knows.formats`` entry-point
group; the factory callable is :func:`builtin_formats`.

Internal helpers:

* :class:`_BaseFormat` -- DRY property storage and a tiny :meth:`_result`
  helper shared by every plugin.
* :class:`_NxTextFormat` -- one-liner for formats that just join a
  NetworkX generator.
* :class:`_VisualFormat` -- matplotlib-based rendering for SVG/PNG/JPG/PDF.
"""

import csv
import io
import json
from collections.abc import Callable, Iterable
from typing import Any

import networkx as nx

from .format_plugin import ConvertContext, FormatResult, OutputKind


# ---------------------------------------------------------------------------
# Internal base classes (not part of the public API)
# ---------------------------------------------------------------------------

class _BaseFormat:
    """Common property storage for all built-in format plugins.

    Subclasses only need to implement :meth:`convert`.

    Args:
        name: Short CLI identifier (e.g. ``"graphml"``).
        description: Human-readable help text.
        output_kind: Discriminator for the produced output.
        default_extension: File extension with leading dot.
    """

    __slots__ = ("_name", "_description", "_output_kind", "_default_extension")

    def __init__(
        self,
        name: str,
        description: str,
        output_kind: OutputKind,
        default_extension: str,
    ) -> None:
        self._name = name
        self._description = description
        self._output_kind = output_kind
        self._default_extension = default_extension

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def output_kind(self) -> OutputKind:
        return self._output_kind

    @property
    def default_extension(self) -> str:
        return self._default_extension

    def _result(self, data: str | bytes | dict[str, str | bytes]) -> FormatResult:
        """Build a :class:`FormatResult` reusing this plugin's metadata."""
        return FormatResult(
            data=data,
            kind=self._output_kind,
            default_extension=self._default_extension,
        )


class _NxTextFormat(_BaseFormat):
    """Text format that delegates to a NetworkX line generator.

    Covers GraphML, GEXF, GML, adjacency list, multiline adjacency list
    and edge list - all follow the same ``'\\n'.join(generator(graph))``
    pattern.

    Args:
        name: CLI identifier.
        description: Human-readable help text.
        default_extension: File extension with leading dot.
        generator: Callable that takes a ``DiGraph`` and returns an
            iterable of strings (e.g. ``nx.generate_graphml``).
    """

    __slots__ = ("_generator",)

    def __init__(
        self,
        name: str,
        description: str,
        default_extension: str,
        generator: Callable[[nx.DiGraph], Iterable[str]],
    ) -> None:
        super().__init__(name, description, OutputKind.TEXT, default_extension)
        self._generator = generator

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        return self._result('\n'.join(self._generator(graph)))


class _VisualFormat(_BaseFormat):
    """Format rendered via :class:`GraphDrawer`.

    The ``GraphDrawer`` import is deferred so that ``matplotlib`` is only
    loaded when a visual format is actually requested.

    Args:
        name: CLI identifier.
        description: Human-readable help text.
        output_kind: ``TEXT`` for SVG, ``BINARY`` for raster/PDF.
        default_extension: File extension with leading dot.
        draw_method: Name of the ``GraphDrawer`` method to call
            (e.g. ``"to_png"``).
    """

    __slots__ = ("_draw_method",)

    def __init__(
        self,
        name: str,
        description: str,
        output_kind: OutputKind,
        default_extension: str,
        draw_method: str,
    ) -> None:
        super().__init__(name, description, output_kind, default_extension)
        self._draw_method = draw_method

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        from .graph_drawer import GraphDrawer

        drawer = GraphDrawer(graph, max_nodes=ctx.viz_limit, show_info=ctx.show_info)
        data: str | bytes = getattr(drawer, self._draw_method)()
        return self._result(data)


# ---------------------------------------------------------------------------
# Formats with custom conversion logic
# ---------------------------------------------------------------------------

class YARSPGFormat(_BaseFormat):
    """YARS-PG property-graph serialization."""

    def __init__(self) -> None:
        super().__init__("yarspg", "YARS-PG format", OutputKind.TEXT, ".yarspg")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        nodes = [self._format_node(n) for n in graph.nodes(data=True)]
        edges = [self._format_edge(e) for e in graph.edges(data=True)]
        return self._result('\n'.join(nodes + edges))

    @staticmethod
    def _format_node(node: tuple[str, dict[str, Any]]) -> str:
        """Format a single node in YARS-PG syntax."""
        node_id, properties = node
        label = properties.get('label', 'label')
        prop_list = ', '.join(
            f'"{key}": "{value}"'
            for key, value in properties.items()
            if key != 'label'
        )
        return f"({node_id} {{\"{label}\"}}[{prop_list}])"

    @staticmethod
    def _format_edge(edge: tuple[str, str, dict[str, Any]]) -> str:
        """Format a single edge in YARS-PG syntax."""
        u, v, properties = edge
        label = properties.get('label', 'label')
        prop_list = ', '.join(
            f'"{key}": "{value}"'
            for key, value in properties.items()
            if key != 'label'
        )
        return f"({u})-({{\"{label}\"}}[{prop_list}])->({v})"


class CSVFormat(_BaseFormat):
    """CSV export producing separate node and edge files."""

    def __init__(self) -> None:
        super().__init__("csv", "CSV nodes and edges files", OutputKind.MULTI_FILE, ".csv")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        return self._result({
            '_nodes.csv': self._nodes_to_csv(graph),
            '_edges.csv': self._edges_to_csv(graph),
        })

    @staticmethod
    def _nodes_to_csv(graph: nx.DiGraph) -> str:
        """Serialize all nodes to a CSV string."""
        prop_keys: dict[str, None] = {}
        for _, props in graph.nodes(data=True):
            for key in props:
                prop_keys.setdefault(key, None)
        headers = ['id'] + list(prop_keys)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for node_id, props in graph.nodes(data=True):
            writer.writerow([node_id] + [props.get(k, '') for k in prop_keys])
        return buf.getvalue().strip()

    @staticmethod
    def _edges_to_csv(graph: nx.DiGraph) -> str:
        """Serialize all edges to a CSV string."""
        prop_keys: dict[str, None] = {}
        for _, _, props in graph.edges(data=True):
            for key in props:
                prop_keys.setdefault(key, None)
        headers = ['id', 'id_from', 'id_to'] + list(prop_keys)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for edge_id, (source, target, props) in enumerate(graph.edges(data=True), start=1):
            writer.writerow(
                [f"E{edge_id}", source, target] + [props.get(k, '') for k in prop_keys]
            )
        return buf.getvalue().strip()


class CypherFormat(_BaseFormat):
    """Cypher ``CREATE`` statement export (Neo4j-compatible)."""

    def __init__(self) -> None:
        super().__init__("cypher", "Cypher CREATE statements", OutputKind.TEXT, ".cypher")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        statements: list[str] = []
        for node_id, properties in graph.nodes(data=True):
            label = properties.get('label', '')
            props = ', '.join(f"{k}: \"{v}\"" for k, v in properties.items() if k != 'label')
            statements.append(f"CREATE ({node_id}:{label} {{{props}}})")
        for source, target, properties in graph.edges(data=True):
            label = properties.get('label', '')
            props = ', '.join(f"{k}: \"{v}\"" for k, v in properties.items() if k != 'label')
            statements.append(f"CREATE ({source})-[:{label} {{{props}}}]->({target})")
        return self._result('\n'.join(statements))


class JSONFormat(_BaseFormat):
    """JSON node-link serialization."""

    def __init__(self) -> None:
        super().__init__("json", "JSON node-link format", OutputKind.TEXT, ".json")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        return self._result(json.dumps(nx.node_link_data(graph, edges="edges")))


# ---------------------------------------------------------------------------
# Entry-point factory
# ---------------------------------------------------------------------------

def builtin_formats() -> list[_BaseFormat]:
    """Return instances of all 14 built-in format plugins.

    This function is the target of the ``knows.formats`` entry point
    declared in ``pyproject.toml``.
    """
    return [
        _NxTextFormat("graphml", "GraphML XML format", ".graphml", nx.generate_graphml),
        YARSPGFormat(),
        CSVFormat(),
        CypherFormat(),
        _NxTextFormat("gexf", "GEXF XML format", ".gexf", nx.generate_gexf),
        _NxTextFormat("gml", "GML format", ".gml", nx.generate_gml),
        _VisualFormat("svg", "SVG vector image", OutputKind.TEXT, ".svg", "to_svg"),
        _VisualFormat("png", "PNG raster image", OutputKind.BINARY, ".png", "to_png"),
        _VisualFormat("jpg", "JPEG raster image", OutputKind.BINARY, ".jpg", "to_jpg"),
        _VisualFormat("pdf", "PDF document", OutputKind.BINARY, ".pdf", "to_pdf"),
        _NxTextFormat("adjacency_list", "Adjacency list format", ".adj", nx.generate_adjlist),
        _NxTextFormat(
            "multiline_adjacency_list", "Multiline adjacency list format",
            ".adj", nx.generate_multiline_adjlist,
        ),
        _NxTextFormat(
            "edge_list", "Edge list format", ".edgelist",
            lambda g: nx.generate_edgelist(g, data=True),
        ),
        JSONFormat(),
    ]
