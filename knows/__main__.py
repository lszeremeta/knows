"""Entry point for the ``knows`` CLI.

Running ``python -m knows`` or the ``knows`` console script both invoke
:func:`main`.
"""

import random
import sys
from pathlib import Path

from .command_line_interface import CommandLineInterface
from .format_plugin import OutputKind
from .graph import Graph
from .graph_drawer import GraphDrawer
from .output_format import OutputFormat


def main() -> None:
    """Parse CLI arguments, generate a graph and write the chosen format."""
    cli = CommandLineInterface()
    try:
        # Text output may contain non-ASCII characters (e.g. localized
        # property values); force UTF-8 regardless of console encoding.
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8')

        rng = random.Random(cli.args.seed)
        num_nodes = cli.args.nodes if cli.args.nodes is not None else rng.randint(2, 100)
        num_edges = cli.args.edges if cli.args.edges is not None else rng.randint(num_nodes // 2, num_nodes)

        # Load schema if specified
        schema = None
        if cli.args.schema:
            from .schema import load_schema
            schema = load_schema(cli.args.schema)

        graph = Graph(num_nodes, num_edges,
                      node_props=cli.args.node_props,
                      edge_props=cli.args.edge_props,
                      seed=cli.args.seed,
                      schema=schema,
                      locale=cli.args.locale)
        graph.generate()

        output = OutputFormat(graph, viz_limit=cli.args.limit, show_info=cli.args.show_info)
        result = output.to_format(cli.args.format)

        if cli.args.output:
            output_path = Path(cli.args.output)
            match result.kind:
                case OutputKind.MULTI_FILE:
                    if not isinstance(result.data, dict):
                        raise TypeError("Multi-file format returned invalid data")
                    base = output_path.with_suffix('')
                    for suffix, content in result.data.items():
                        file_path = base.with_name(base.name + suffix)
                        if isinstance(content, bytes):
                            file_path.write_bytes(content)
                        else:
                            file_path.write_text(content, encoding='utf-8')
                case OutputKind.BINARY:
                    if not isinstance(result.data, bytes):
                        raise TypeError("Binary format returned invalid data")
                    output_path.write_bytes(result.data)
                case OutputKind.TEXT:
                    if not isinstance(result.data, str):
                        raise TypeError("Text format returned invalid data")
                    output_path.write_text(result.data, encoding='utf-8')
        else:
            match result.kind:
                case OutputKind.MULTI_FILE:
                    if not isinstance(result.data, dict):
                        raise TypeError("Multi-file format returned invalid data")
                    for index, content in enumerate(result.data.values()):
                        stream = sys.stdout if index == 0 else sys.stderr
                        if isinstance(content, bytes):
                            stream.flush()
                            stream.buffer.write(content)
                            stream.buffer.flush()
                        else:
                            print(content, file=stream)
                case OutputKind.BINARY:
                    if not isinstance(result.data, bytes):
                        raise TypeError("Binary format returned invalid data")
                    sys.stdout.buffer.write(result.data)
                case OutputKind.TEXT:
                    if not isinstance(result.data, str):
                        raise TypeError("Text format returned invalid data")
                    print(result.data)

        if cli.args.draw:
            try:
                drawer = GraphDrawer(graph.graph, max_nodes=cli.args.limit, show_info=cli.args.show_info)
                if drawer.was_truncated:
                    print(
                        f"Note: Displaying {len(drawer.graph)}/{drawer.original_node_count} nodes "
                        f"(use --no-limit to show all)",
                        file=sys.stderr
                    )
                drawer.configure_and_draw()
            except RuntimeError as e:
                if cli.args.debug:
                    raise
                print(f"Error occurred: {e}", file=sys.stderr)

    except Exception as e:
        if cli.args.debug:
            raise
        print(f"Error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
