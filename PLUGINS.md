# Output Format Plugins

Knows uses a plugin system for output formats. Every format - including all 14 built-in ones - is a plugin discovered at
runtime via Python's standard [`entry_points`](https://packaging.python.org/en/latest/specifications/entry-points/)
mechanism. This guide explains how it works and how to create your own format plugins.

## How It Works

```
pyproject.toml              FormatRegistry             CLI / OutputFormat
──────────────              ──────────────             ──────────────────
[project.entry-points       Reads entry points         registry.get("xml")
 ."knows.formats"]    ───►  Calls each factory   ───►  plugin.convert(graph, ctx)
xml = "my_pkg:factory"      Caches plugins             returns FormatResult
```

1. When Knows starts, `FormatRegistry` scans the `knows.formats` entry-point group using `importlib.metadata`.
2. Each entry point references a **factory callable** that returns one plugin instance or a list of them.
3. The registry caches every plugin by its `name` property. The CLI reads `registry.names()` to build the `--format`
   choices.
4. When the user picks a format, `plugin.convert(graph, ...)` is called and returns a `FormatResult`.

## Plugin Interface

A format plugin is any Python object that has the following properties and method. No base class inheritance is
required - Knows uses structural typing (a `Protocol` with `@runtime_checkable`).

| Member              | Type                                | Description                                         |
|---------------------|-------------------------------------|-----------------------------------------------------|
| `name`              | `str` (property)                    | Unique CLI identifier, e.g. `"graphml"`             |
| `description`       | `str` (property)                    | Human-readable help text                            |
| `output_kind`       | `OutputKind` (property)             | `TEXT`, `BINARY`, or `MULTI_FILE`                   |
| `default_extension` | `str` (property)                    | File extension with leading dot, e.g. `".graphml"`  |
| `convert()`         | `(DiGraph, ConvertContext) → FormatResult` | Converts the graph and returns the result    |

### OutputKind

| Value        | `FormatResult.data` type       | Description                              |
|--------------|-------------------------------|------------------------------------------|
| `TEXT`       | `str`                         | Single text output                       |
| `BINARY`    | `bytes`                       | Single binary blob (images, PDF, ...)      |
| `MULTI_FILE`| `dict[str, str \| bytes]`     | Multiple named files (keys are suffixes) |

### FormatResult

An immutable (frozen) dataclass:

```python
from knows.format_plugin import FormatResult, OutputKind

result = FormatResult(
    data="<graphml>...</graphml>",
    kind=OutputKind.TEXT,
    default_extension=".graphml",
)
```

## Creating an External Plugin (pip Package)

This is the recommended approach for third-party formats. Users install your package and the format appears in `knows -f`
automatically.

### 1. Write the Plugin Class

Create a file, e.g. `knows_xml/plugin.py`:

```python
import networkx as nx
from knows.format_plugin import ConvertContext, FormatPlugin, FormatResult, OutputKind


class XmlFormat:
    """Custom XML export for Knows."""

    @property
    def name(self) -> str:
        return "xml"

    @property
    def description(self) -> str:
        return "Custom XML format"

    @property
    def output_kind(self) -> OutputKind:
        return OutputKind.TEXT

    @property
    def default_extension(self) -> str:
        return ".xml"

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        lines = ['<?xml version="1.0"?>', "<graph>"]
        for node_id, props in graph.nodes(data=True):
            attrs = " ".join(f'{k}="{v}"' for k, v in props.items())
            lines.append(f'  <node id="{node_id}" {attrs}/>')
        for src, tgt, props in graph.edges(data=True):
            attrs = " ".join(f'{k}="{v}"' for k, v in props.items())
            lines.append(f'  <edge source="{src}" target="{tgt}" {attrs}/>')
        lines.append("</graph>")
        return FormatResult(
            data="\n".join(lines),
            kind=OutputKind.TEXT,
            default_extension=".xml",
        )
```

The `convert()` method receives a NetworkX `DiGraph` and a `ConvertContext`. The context carries parameters like
`viz_limit` and `show_info` that visual formats use; text formats can safely ignore `ctx`.

### 2. Write the Factory Function

The entry point must reference a callable that returns a single plugin or a list of plugins:

```python
# knows_xml/plugin.py  (continued)

def create_plugin() -> XmlFormat:
    """Entry-point factory."""
    return XmlFormat()
```

If your package provides multiple formats, return a list:

```python
def create_plugins() -> list:
    return [XmlFormat(), AnotherFormat()]
```

### 3. Register the Entry Point

In your package's `pyproject.toml`:

```toml
[project]
name = "knows-xml"
version = "1.0.0"
dependencies = ["knows"]

[tool.setuptools.packages.find]
include = ["knows_xml"]

[project.entry-points."knows.formats"]
xml = "knows_xml.plugin:create_plugin"
```

The key (`xml`) is just a label for the entry point - the actual format name comes from the plugin's `name` property.

### 4. Install and Use

```shell
pip install -e .          # or publish to PyPI and `pip install knows-xml`
knows -f xml              # your format is now available
knows -f xml graph.xml    # save to file
```

No changes to Knows itself are needed. The format appears in `knows --help` automatically.

### Project Structure

A minimal plugin package looks like this:

```
knows-xml/
├── pyproject.toml
└── knows_xml/
    ├── __init__.py
    └── plugin.py       # XmlFormat class + create_plugin() factory
```

A complete, working example is in the
[`plugin-example/`](https://github.com/lszeremeta/knows/tree/main/plugin-example) directory.
Copy it, rename the package, and replace the conversion logic:

```shell
cp -r plugin-example/ my-knows-plugin/
cd my-knows-plugin/
pip install -e .
knows -f ndjson  # works immediately
```

## Adding a Built-in Format

To add a new format to the Knows core, you only modify one file: `knows/builtin_formats.py`.

### Simple format (wraps a NetworkX generator)

If your format just joins lines from a NetworkX function, add a single `_NxTextFormat` entry to `builtin_formats()`:

```python
def builtin_formats() -> list[_BaseFormat]:
    return [
        # ... existing formats ...
        _NxTextFormat("pajek", "Pajek NET format", ".net", nx.generate_pajek),
    ]
```

That's it - no new class needed.

### Format with custom logic

If your format needs its own conversion logic, write a class inheriting from `_BaseFormat`:

```python
class PajekFormat(_BaseFormat):
    """Pajek NET serialization with custom handling."""

    def __init__(self) -> None:
        super().__init__("pajek", "Pajek NET format", OutputKind.TEXT, ".net")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        node_index = {}
        lines = [f"*vertices {graph.number_of_nodes()}"]
        for i, (node_id, props) in enumerate(graph.nodes(data=True), 1):
            node_index[node_id] = i
            label = props.get("label", node_id)
            lines.append(f'{i} "{label}"')
        lines.append("*arcs")
        for src, tgt, props in graph.edges(data=True):
            label = props.get("label", "")
            lines.append(f"{node_index[src]} {node_index[tgt]} 1.0 {label}")
        return self._result("\n".join(lines))
```

Then add `PajekFormat()` to the list in `builtin_formats()`.

Key points:

- Use `self._result(data)` helper instead of constructing `FormatResult` manually - it fills in `kind` and
  `default_extension` automatically.
- The four built-in visual formats (SVG, PNG, JPG, PDF) use `_VisualFormat` which delegates to a `GraphDrawer`
  method by name - e.g. `_VisualFormat("png", "PNG raster image", OutputKind.BINARY, ".png", "to_png")`. No custom
  class is needed unless you want a format that `GraphDrawer` does not support natively (see the
  [WebP example](#using-graphdrawer) below).

### 3. Reinstall and Test

```shell
pip install -e ".[test]"
knows -f pajek            # verify it works
knows --help              # verify it appears in format list
pytest tests/ -v          # verify nothing broke
```

## Binary and Multi-File Formats

### Binary Format Example

For formats that produce raw bytes (images, archives, etc.):

```python
class CustomBinaryFormat(_BaseFormat):
    def __init__(self) -> None:
        super().__init__("mybin", "Custom binary", OutputKind.BINARY, ".bin")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        data: bytes = my_serialize(graph)
        return self._result(data)
```

When `OutputKind.BINARY` is used:

- File output → `path.write_bytes(result.data)`
- Stdout → `sys.stdout.buffer.write(result.data)`

### Multi-File Format Example

For formats that produce multiple files (like CSV with separate node and edge files):

```python
class SplitFormat(_BaseFormat):
    def __init__(self) -> None:
        super().__init__("split", "Split files", OutputKind.MULTI_FILE, ".txt")

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        nodes_data = "..."
        edges_data = "..."
        return self._result({
            "_nodes.txt": nodes_data,
            "_edges.txt": edges_data,
        })
```

When `OutputKind.MULTI_FILE` is used:

- File output → for each key-value pair, a file is written as `<base><suffix>` (e.g. `graph_nodes.txt`)
- Stdout → first entry to stdout, remaining entries to stderr

The dict keys are **filename suffixes** appended to the base name. For example, if the user runs
`knows -f split output.txt`, the files will be `output_nodes.txt` and `output_edges.txt`.

## Visual Format Plugins

External plugins can produce visual (image) output. The `ConvertContext` passed to `convert()` carries two fields that
visual formats should respect:

- `ctx.viz_limit` - maximum number of nodes to render (0 = unlimited).
- `ctx.show_info` - whether to display a node-count label on the image.

### Using `GraphDrawer`

Knows ships a `GraphDrawer` helper (`knows.graph_drawer`) that handles graph layout, truncation, and rendering via
matplotlib. The four built-in visual formats (SVG, PNG, JPG, PDF) all delegate to it. External plugins can use it too:

```python
import networkx as nx
from knows.format_plugin import ConvertContext, FormatResult, OutputKind
from knows.graph_drawer import GraphDrawer


class WebpFormat:
    """WEBP raster image export."""

    @property
    def name(self) -> str:
        return "webp"

    @property
    def description(self) -> str:
        return "WEBP raster image"

    @property
    def output_kind(self) -> OutputKind:
        return OutputKind.BINARY

    @property
    def default_extension(self) -> str:
        return ".webp"

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        import io
        import matplotlib.pyplot as plt

        drawer = GraphDrawer(graph, max_nodes=ctx.viz_limit, show_info=ctx.show_info)
        plt.figure()
        drawer.draw()
        buf = io.BytesIO()
        plt.savefig(buf, format="webp")
        plt.close()
        return FormatResult(data=buf.getvalue(), kind=OutputKind.BINARY, default_extension=".webp")
```

`GraphDrawer` requires matplotlib (`pip install knows[draw]`). If your plugin needs it, declare the dependency in your
`pyproject.toml`:

```toml
dependencies = ["knows[draw]"]
```

### Custom rendering

You can also skip `GraphDrawer` entirely and use your own rendering pipeline. As long as `convert()` returns a valid
`FormatResult`, any library (Graphviz, Plotly, PIL, ...) works.

## Error Handling

The registry is resilient to broken plugins:

- If an entry point **fails to load** (e.g. missing dependency), a warning is emitted and the plugin is skipped.
- If a factory returns an object that **does not satisfy** the `FormatPlugin` protocol, a warning is emitted and the
  object is skipped.
- If two plugins have the **same name**, the first one wins and a warning is emitted for the duplicate.

Warnings are printed via Python's `warnings` module and never crash the application.

## Testing Your Plugin

```python
import networkx as nx
from knows.format_plugin import ConvertContext, FormatPlugin, OutputKind

from my_package import MyFormat


def test_protocol_conformance():
    plugin = MyFormat()
    assert isinstance(plugin, FormatPlugin)


def test_convert_produces_correct_result():
    plugin = MyFormat()
    graph = nx.DiGraph()
    graph.add_node("N1", label="Person", firstName="Alice")
    graph.add_edge("N1", "N2", label="knows")

    result = plugin.convert(graph, ConvertContext(viz_limit=50, show_info=True))

    assert result.kind == OutputKind.TEXT  # or BINARY / MULTI_FILE
    assert isinstance(result.data, str)   # matches the kind
    assert len(result.data) > 0
```

You can also test via the registry to verify that entry-point registration works correctly:

```python
from knows.format_registry import FormatRegistry


def test_plugin_is_registered():
    # Requires `pip install -e .` first
    registry = FormatRegistry()
    assert "my_format_name" in registry.names()
```

## Reference

| Module                  | Purpose                                              |
|-------------------------|------------------------------------------------------|
| `knows.format_plugin`   | `OutputKind`, `FormatResult`, `ConvertContext`, `FormatPlugin` protocol |
| `knows.format_registry` | `FormatRegistry` singleton (discovery and caching)                     |
| `knows.builtin_formats` | 14 built-in format implementations + factory                          |
| `knows.output_format`   | `OutputFormat` facade used by the CLI                                  |
| `knows.graph_drawer`    | `GraphDrawer` - matplotlib-based rendering (requires `knows[draw]`)    |
