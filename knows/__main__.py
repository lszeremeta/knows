import random
import sys

from .command_line_interface import CommandLineInterface
from .graph import Graph
from .graph_drawer import GraphDrawer
from .output_format import OutputFormat


def main():
    try:
        cli = CommandLineInterface()
        num_nodes = cli.args.nodes or random.randint(2, 100)
        num_edges = cli.args.edges or random.randint(num_nodes // 2, num_nodes)

        graph = Graph(num_nodes, num_edges)
        graph.generate()

        output = OutputFormat(graph)
        formatted_output = output.to_format(cli.args.format)
        if cli.args.format == 'svg':
            sys.stdout.buffer.write(formatted_output.encode('utf-8'))
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
