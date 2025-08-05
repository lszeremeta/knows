import argparse

from .graph import NODE_PROPERTIES, EDGE_PROPERTIES


class CommandLineInterface:
    """A class to handle the command line interface."""

    def __init__(self):
        """Inits CommandLineInterface and parses the arguments."""
        self.args = self._parse_args()

    @staticmethod
    def _parse_args():
        """Parses the command line arguments.

        Returns:
            Namespace: The parsed arguments.
        """

        parser = argparse.ArgumentParser(
            description="Knows is a simple property graph benchmark that creates graphs with specified node and edge numbers, supporting multiple output formats and visualization.",
            prog='knows')
        parser.add_argument(
            "-n",
            "--nodes",
            type=int,
            default=None,
            help=(
                "Number of nodes in the graph. Selected randomly if not specified."
            ),
        )
        parser.add_argument(
            "-e",
            "--edges",
            type=int,
            default=None,
            help=(
                "Number of edges in the graph. Selected randomly if not specified."
            ),
        )
        parser.add_argument(
            "-f",
            "--format",
            choices=[
                'graphml',
                'yarspg',
                'csv',
                'cypher',
                'gexf',
                'gml',
                'svg',
                'adjacency_list',
                'multiline_adjacency_list',
                'edge_list',
                'json',
            ],
            default='graphml',
            help="Format to output the graph. Default: graphml.",
        )
        parser.add_argument(
            "-np",
            "--node-props",
            nargs='*',
            choices=NODE_PROPERTIES,
            default=['firstName', 'lastName'],
            help=(
                    "Space-separated node properties. Available: "
                    + ', '.join(NODE_PROPERTIES)
                    + "."
            ),
        )
        parser.add_argument(
            "-ep",
            "--edge-props",
            nargs='*',
            choices=EDGE_PROPERTIES,
            default=['createDate'],
            help=(
                    "Space-separated edge properties. Available: "
                    + ', '.join(EDGE_PROPERTIES)
                    + "."
            ),
        )
        parser.add_argument(
            "-a",
            "--all-props",
            action="store_true",
            help="Use all available node and edge properties.",
        )
        parser.add_argument("-d", "--draw", action="store_true",
                            help="Generate an image of the graph (default is no image). This option may not work in the Docker. If you want to generate an image of the graph, use the svg output format and save it to a file.")
        args = parser.parse_args()
        if args.all_props:
            args.node_props = NODE_PROPERTIES
            args.edge_props = EDGE_PROPERTIES
        return args
