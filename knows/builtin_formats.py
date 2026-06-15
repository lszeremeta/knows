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
import math
import re
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

    @classmethod
    def _format_props(cls, properties: dict[str, Any]) -> str:
        """Serialize non-label properties as a YARS-PG property list."""
        return ', '.join(
            f'{cls._format_string(key)}: {cls._format_value(value)}'
            for key, value in properties.items()
            if key != 'label'
        )

    # Named escape sequences from the YARS-PG STR grammar; every other
    # character (printable Unicode and raw control bytes alike) is literal.
    _ESCAPES = {
        '"': r'\"',
        '\\': r'\\',
        '\n': r'\n',
        '\r': r'\r',
        '\t': r'\t',
        '\b': r'\b',
        '\f': r'\f',
    }

    @classmethod
    def _format_string(cls, value: Any) -> str:
        r"""Quote *value* as a YARS-PG string literal.

        Grammar: STR : '"' (~["\\\r\n] | '\\' [tbnrf"'\\])* '"'.  The only escape
        sequences are \t \b \n \r \f \" \' \\ -- there is
        no \uXXXX form.  I escape " \ and CR/LF and pass
        every other character through literally; printable Unicode and even
        raw C0/C1 control bytes are valid inside a YARS-PG string.
        """
        return '"' + ''.join(cls._ESCAPES.get(ch, ch) for ch in str(value)) + '"'

    @classmethod
    def _format_value(cls, value: Any) -> str:
        """Render a property value as a quoted YARS-PG literal."""
        text = ('true' if value else 'false') if isinstance(value, bool) else str(value)
        return cls._format_string(text)

    @staticmethod
    def _format_identifier(identifier: Any) -> str:
        """Validate and render a YARS-PG node identifier."""
        text = str(identifier)
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', text):
            raise ValueError(f"Invalid YARS-PG node identifier: {text!r}")
        return text

    @classmethod
    def _format_node(cls, node: tuple[Any, dict[str, Any]]) -> str:
        """Format a single node in YARS-PG syntax."""
        node_id, properties = node
        node_id = cls._format_identifier(node_id)
        label = cls._format_string(properties.get('label', 'label'))
        return f"({node_id} {{{label}}}[{cls._format_props(properties)}])"

    @classmethod
    def _format_edge(cls, edge: tuple[Any, Any, dict[str, Any]]) -> str:
        """Format a single edge in YARS-PG syntax."""
        u, v, properties = edge
        u = cls._format_identifier(u)
        v = cls._format_identifier(v)
        label = cls._format_string(properties.get('label', 'label'))
        return f"({u})-({{{label}}}[{cls._format_props(properties)}])->({v})"


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
        return buf.getvalue().rstrip('\r\n')

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
        return buf.getvalue().rstrip('\r\n')


class CypherFormat(_BaseFormat):
    """Cypher ``CREATE`` statement export (Neo4j-compatible)."""

    def __init__(self) -> None:
        super().__init__("cypher", "Cypher CREATE statements", OutputKind.TEXT, ".cypher")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        statements: list[str] = []
        for node_id, properties in graph.nodes(data=True):
            variable = self._format_identifier(node_id)
            raw_label = properties.get('label')
            label = (
                f":{self._format_identifier(raw_label)}"
                if raw_label not in (None, '')
                else ''
            )
            props = self._format_props(properties)
            statements.append(f"CREATE ({variable}{label} {{{props}}})")
        for source, target, properties in graph.edges(data=True):
            raw_label = properties.get('label')
            if raw_label in (None, ''):
                raise ValueError("Cypher relationships require a non-empty label")
            source = self._format_identifier(source)
            target = self._format_identifier(target)
            label = self._format_identifier(raw_label)
            props = self._format_props(properties)
            statements.append(f"CREATE ({source})-[:{label} {{{props}}}]->({target})")
        return self._result('\n'.join(statements))

    @classmethod
    def _format_props(cls, properties: dict[str, Any]) -> str:
        """Serialize properties (minus the label) as a Cypher map."""
        return ', '.join(
            f"{cls._format_identifier(k)}: {cls._format_value(v)}"
            for k, v in properties.items()
            if k != 'label'
        )

    @staticmethod
    def _format_value(value: Any) -> str:
        """Render a property value as a Cypher literal.

        Numbers and booleans keep their type; everything else becomes a
        quoted string with Cypher-compatible JSON escaping.
        """
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            if math.isnan(value):
                return 'NaN'
            if math.isinf(value):
                return 'Infinity' if value > 0 else '-Infinity'
            return str(value)
        return json.dumps(str(value), ensure_ascii=False)

    @staticmethod
    def _format_identifier(identifier: Any) -> str:
        r"""Backtick-quote a Cypher name and escape its contents.

        Neo4j resolves ``\uXXXX`` escapes inside backtick-quoted names, so a
        literal backslash is emitted as ``\u005C`` (otherwise a value like
        ``\u0060`` in the input could be reinterpreted as a backtick).
        Backticks themselves are doubled, and C0/C1 control characters are
        written as ``\uXXXX`` escapes.
        """
        out: list[str] = []
        for char in str(identifier):
            code = ord(char)
            if char == '`':
                out.append('``')
            elif char == '\\':
                out.append(r'\u005C')
            elif code < 0x20 or 0x7F <= code <= 0x9F:
                out.append(f'\\u{code:04X}')
            else:
                out.append(char)
        return f'`{"".join(out)}`'


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
