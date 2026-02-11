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
    try:
        cli = CommandLineInterface()
        rng = random.Random(cli.args.seed)
        num_nodes = cli.args.nodes or rng.randint(2, 100)
        num_edges = cli.args.edges or rng.randint(num_nodes // 2, num_nodes)

        # Load schema if specified
        schema = None
        if cli.args.schema:
            from .schema import load_schema
            schema = load_schema(cli.args.schema)

        graph = Graph(num_nodes, num_edges,
                      node_props=cli.args.node_props,
                      edge_props=cli.args.edge_props,
                      seed=cli.args.seed,
                      schema=schema)
        graph.generate()

        output = OutputFormat(graph, viz_limit=cli.args.limit, show_info=cli.args.show_info)
        result = output.to_format(cli.args.format)

        if cli.args.output:
            output_path = Path(cli.args.output)
            match result.kind:
                case OutputKind.MULTI_FILE:
                    base = output_path.with_suffix('')
                    for suffix, content in result.data.items():
                        file_path = base.with_name(base.name + suffix)
                        if isinstance(content, bytes):
                            file_path.write_bytes(content)
                        else:
                            file_path.write_text(content, encoding='utf-8')
                case OutputKind.BINARY:
                    output_path.write_bytes(result.data)
                case OutputKind.TEXT:
                    output_path.write_text(result.data, encoding='utf-8')
        else:
            match result.kind:
                case OutputKind.MULTI_FILE:
                    items = iter(result.data.values())
                    print(next(items))
                    for extra in items:
                        print(extra, file=sys.stderr)
                case OutputKind.BINARY:
                    sys.stdout.buffer.write(result.data)
                case OutputKind.TEXT:
                    if result.default_extension == '.svg':
                        sys.stdout.buffer.write(result.data.encode('utf-8'))
                    else:
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
                print(f"Error occurred: {e}", file=sys.stderr)

    except Exception as e:
        print(f"Error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
