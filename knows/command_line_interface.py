import argparse


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
        parser.add_argument("nodes", type=int, nargs='?', default=None, help="Number of nodes in the graph. Selected randomly if not specified.")
        parser.add_argument("edges", type=int, nargs='?', default=None, help="Number of edges in the graph. Selected randomly if not specified.")
        parser.add_argument("-f", "--format", choices=['graphml', 'yarspg', 'gexf', 'gml', 'svg', 'adjacency_list',
                                                       'multiline_adjacency_list', 'edge_list', 'json'],
                            default='graphml', help="Format to output the graph. Default: graphml.")
        parser.add_argument("-d", "--draw", action="store_true",
                            help="Generate an image of the graph (default is no image). This option may not work in the Docker. If you want to generate an image of the graph, use the svg output format and save it to a file.")
        return parser.parse_args()
