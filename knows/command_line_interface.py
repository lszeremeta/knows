import argparse
from pathlib import Path

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
                "output formats, graph schema and visualization."
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
            "--schema",
            type=str,
            default=None,
            metavar="FILE",
            help=(
                "Path to JSON schema file defining custom node/edge types and properties. "
                "When specified, overrides -np, -ep, and -ap options. "
                "GQL-inspired schema format (ISO/IEC 39075). "
                "See https://github.com/lszeremeta/knows/blob/main/SCHEMA.md for details."
            ),
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
                    + ". Ignored when --schema is used."
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
                    + ". Ignored when --schema is used."
            ),
        )
        parser.add_argument(
            "-ap",
            "--all-props",
            action="store_true",
            help="Use all available node and edge properties. Ignored when --schema is used.",
        )
        parser.add_argument(
            "-d", "--draw",
            action="store_true",
            help="Show interactive graph window. Requires Tkinter. May not work in Docker.",
        )
        # Graphics output options (svg, png, jpg, pdf, --draw)
        gfx_group = parser.add_argument_group('Graphics output options (svg, png, jpg, pdf, -d)')
        gfx_group.add_argument(
            "-l",
            "--limit",
            type=int,
            default=50,
            metavar="N",
            help="Maximum nodes to display (default: 50). Shows subgraph centered on most connected nodes.",
        )
        gfx_group.add_argument(
            "--no-limit",
            action="store_true",
            help="Show full graph without node limit.",
        )
        gfx_group.add_argument(
            "--hide-info",
            action="store_true",
            help="Hide node count info (e.g., '50/200 nodes') from output.",
        )

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

        # Handle --no-limit flag
        if args.no_limit:
            args.limit = 0

        # Derive show_info from hide_info
        args.show_info = not args.hide_info

        # Validate schema file exists if specified
        if args.schema:
            schema_path = Path(args.schema)
            if not schema_path.exists():
                parser.error(f"Schema file not found: {args.schema}")
            if not schema_path.suffix.lower() == '.json':
                parser.error(f"Schema file must be JSON format: {args.schema}")

        return args
