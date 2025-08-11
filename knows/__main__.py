import random
import sys
from pathlib import Path

from .command_line_interface import CommandLineInterface
from .graph import Graph
from .graph_drawer import GraphDrawer
from .output_format import OutputFormat


def main():
    try:
        cli = CommandLineInterface()
        rng = random.Random(cli.args.seed)
        num_nodes = cli.args.nodes or rng.randint(2, 100)
        num_edges = cli.args.edges or rng.randint(num_nodes // 2, num_nodes)

        graph = Graph(num_nodes, num_edges,
                      node_props=cli.args.node_props,
                      edge_props=cli.args.edge_props,
                      seed=cli.args.seed)
        graph.generate()

        output = OutputFormat(graph)
        formatted_output = output.to_format(cli.args.format)
        binary_formats = {'png', 'jpg', 'pdf'}
        if cli.args.output:
            output_path = Path(cli.args.output)
            if cli.args.format == 'csv':
                nodes_csv, edges_csv = formatted_output
                base = output_path.with_suffix('')
                nodes_path = base.with_name(base.name + '_nodes').with_suffix('.csv')
                edges_path = base.with_name(base.name + '_edges').with_suffix('.csv')
                nodes_path.write_text(nodes_csv, encoding='utf-8')
                edges_path.write_text(edges_csv, encoding='utf-8')
            elif cli.args.format in binary_formats:
                output_path.write_bytes(formatted_output)
            else:
                output_path.write_text(formatted_output, encoding='utf-8')
        else:
            if cli.args.format == 'svg':
                sys.stdout.buffer.write(formatted_output.encode('utf-8'))
            elif cli.args.format in binary_formats:
                sys.stdout.buffer.write(formatted_output)
            elif cli.args.format == 'csv':
                nodes_csv, edges_csv = formatted_output

                # Print nodes to stdout and edges to stderr
                print(nodes_csv)
                print(edges_csv, file=sys.stderr)
            else:
                print(formatted_output)

        if cli.args.draw:
            try:
                drawer = GraphDrawer(graph.graph)
                drawer.configure_and_draw()
            except RuntimeError as e:
                print(f"Error occurred: {e}", file=sys.stderr)

    except Exception as e:
        print(f"Error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
