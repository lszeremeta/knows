import argparse

from . import __version__
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
            description=(
                "Knows is a powerful and user-friendly property graph generation that creates graphs "
                "with specified node and edge numbers, supporting multiple "
                "output formats and visualization."
            ),
            prog="knows",
            epilog=(
                "Note on reproducibility: The -s/--seed option ensures "
                "deterministic results in the same environment, but outputs may "
                "differ across Python or dependency versions. See more on GitHub: https://github.com/lszeremeta/knows"
            ),
        )
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
            "-s",
            "--seed",
            type=int,
            default=None,
            help="Seed for random number generation to ensure reproducible results (also between various output formats).",
        )
        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version=f"%(prog)s {__version__}",
            help="Show program version and exit.",
        )
        parser.add_argument(
            "-f",
            "--format",
            choices=[
                'yarspg',
                'graphml',
                'csv',
                'cypher',
                'gexf',
                'gml',
                'svg',
                'png',
                'jpg',
                'pdf',
                'adjacency_list',
                'multiline_adjacency_list',
                'edge_list',
                'json',
            ],
            default='yarspg',
            help="Format to output the graph. Default: yarspg. The svg, png, jpg and pdf formats are for simple graph visualization.",
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
            default=['strength', 'lastMeetingDate'],
            help=(
                    "Space-separated edge properties. Available: "
                    + ', '.join(EDGE_PROPERTIES)
                    + "."
            ),
        )
        parser.add_argument(
            "-ap",
            "--all-props",
            action="store_true",
            help="Use all available node and edge properties.",
        )
        parser.add_argument("-d", "--draw", action="store_true",
                            help="Show simple image of the graph (default is no image). Requires Tkinter. This option may not work in the Docker. If you want to generate an image of the graph, use the svg output format and save it to a file.")
        parser.add_argument(
            "output",
            nargs="?",
            default=None,
            help=(
                "Optional path to save the graph. For CSV format two files will be created: "
                "*_nodes.csv and *_edges.csv."
            ),
        )
        args = parser.parse_args()
        if args.all_props:
            args.node_props = NODE_PROPERTIES
            args.edge_props = EDGE_PROPERTIES
        return args
