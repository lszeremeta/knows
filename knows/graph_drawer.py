# graph_drawer.py
import io

import networkx as nx

try:
    from matplotlib import pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import tkinter

    TKINTER_AVAILABLE = True
except Exception:
    TKINTER_AVAILABLE = False


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
        if not TKINTER_AVAILABLE:
            raise RuntimeError(
                "Tkinter is required for displaying graphs. Install it with 'sudo apt install python3-tk' on Ubuntu or 'brew install python-tk' on macOS."
            )
        self.draw()

        try:
            # Set the window title if possible
            plt.gcf().canvas.manager.set_window_title("Graph Visualization - Knows")
        except Exception:
            pass

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
            self._draw_to_buffer(buffer, 'svg')
            return buffer.getvalue().decode('utf-8')

    def to_png(self) -> bytes:
        """Exports the graph to PNG format.

        Returns:
            bytes: The graph image in PNG format.
        """
        with io.BytesIO() as buffer:
            self._draw_to_buffer(buffer, 'png')
            return buffer.getvalue()

    def to_jpg(self) -> bytes:
        """Exports the graph to JPG format.

        Returns:
            bytes: The graph image in JPG format.
        """
        with io.BytesIO() as buffer:
            self._draw_to_buffer(buffer, 'jpg')
            return buffer.getvalue()

    def to_pdf(self) -> bytes:
        """Exports the graph to PDF format.

        Returns:
            bytes: The graph in PDF format.
        """
        with io.BytesIO() as buffer:
            self._draw_to_buffer(buffer, 'pdf')
            return buffer.getvalue()

    def _draw_to_buffer(self, buffer: io.BytesIO, fmt: str) -> None:
        """Helper method for drawing the graph into a buffer for various formats."""
        plt.figure()
        self.draw()
        plt.savefig(buffer, format=fmt, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
