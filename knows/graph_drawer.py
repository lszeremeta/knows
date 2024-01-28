# graph_drawer.py
import io

import networkx as nx

try:
    from matplotlib import pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class GraphDrawer:
    def __init__(self, graph: nx.Graph):
        """Initializes with a given graph.

        Args:
            graph (networkx.Graph): The graph to be drawn.
        """
        self.graph = graph

        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError(
                "Matplotlib is not available. Drawing functionality is disabled. Use pip install knows[draw] to install the required dependencies.")

    def configure_and_draw(self) -> None:
        """Configures and displays the graph.

        Sets up the graph to be drawn and then displays it.
        """
        self.draw()
        plt.show()

    def draw(self) -> None:
        """Configures the graph drawing settings without displaying it."""
        nx.draw(self.graph, with_labels=True, node_color='#38b4b6ff', edge_color='#284d5cff', font_color='#203445ff',
                arrows=True)

    def to_svg(self) -> str:
        """Exports the graph to SVG format.

        Returns:
            str: The graph representation in SVG format.
        """
        with io.BytesIO() as buffer:
            self._draw_to_buffer(buffer)
            return buffer.getvalue().decode('utf-8')

    def _draw_to_buffer(self, buffer: io.BytesIO) -> None:
        """Helper method for drawing the graph into a buffer for SVG export."""
        plt.figure(figsize=(10, 8))
        self.draw()
        plt.savefig(buffer, format='svg', bbox_inches='tight')
        buffer.seek(0)
        plt.close()
