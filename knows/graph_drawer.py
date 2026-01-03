# graph_drawer.py
import io
from collections import deque

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

DEFAULT_VIZ_LIMIT = 50


class GraphDrawer:
    def __init__(self, graph: nx.Graph, max_nodes: int = DEFAULT_VIZ_LIMIT, show_info: bool = True):
        """Initializes with a given graph.

        Args:
            graph (networkx.Graph): The graph to be drawn.
            max_nodes (int): Maximum nodes to display. Set to 0 or None to disable limiting.
            show_info (bool): Whether to show node count info on the visualization.
        """
        self.original_graph = graph
        self.original_node_count = len(graph)
        self.max_nodes = max_nodes
        self.show_info = show_info

        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError(
                "Matplotlib is not available. Drawing functionality is disabled. Use pip install knows[draw] to install the required dependencies.")

        # Apply subgraph limiting if needed
        if max_nodes and max_nodes > 0 and len(graph) > max_nodes:
            self.graph, self.was_truncated = self._extract_subgraph(graph, max_nodes)
        else:
            self.graph = graph
            self.was_truncated = False

    def _extract_subgraph(self, graph: nx.Graph, max_nodes: int) -> tuple:
        """Extract a subgraph using BFS, spanning multiple components if needed.

        Args:
            graph (networkx.Graph): The original graph.
            max_nodes (int): Maximum number of nodes to include.

        Returns:
            tuple: (subgraph, was_truncated)
        """
        if len(graph) <= max_nodes:
            return graph, False

        # Sort nodes by degree (descending) to prioritize well-connected nodes
        nodes_by_degree = sorted(graph.nodes(), key=lambda n: graph.degree(n), reverse=True)

        visited = set()
        for start_node in nodes_by_degree:
            if len(visited) >= max_nodes:
                break
            if start_node in visited:
                continue

            # BFS from this node
            queue = deque([start_node])
            while queue and len(visited) < max_nodes:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    if len(visited) >= max_nodes:
                        break
                    # Add neighbors to queue (both directions for DiGraph)
                    if graph.is_directed():
                        neighbors = set(graph.successors(node)) | set(graph.predecessors(node))
                    else:
                        neighbors = set(graph.neighbors(node))
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            queue.append(neighbor)

        # Return induced subgraph
        return graph.subgraph(visited).copy(), True

    def get_truncation_info(self) -> tuple:
        """Returns information about truncation.

        Returns:
            tuple: (was_truncated, displayed_count, original_count)
        """
        return self.was_truncated, len(self.graph), self.original_node_count

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
            # Set the window title with truncation info if applicable
            if self.was_truncated:
                title = f"Graph Visualization ({len(self.graph)}/{self.original_node_count} nodes) - Knows"
            else:
                title = "Graph Visualization - Knows"
            plt.gcf().canvas.manager.set_window_title(title)
        except Exception:
            pass

        plt.show()

    def draw(self) -> None:
        """Configures the graph drawing settings without displaying it."""
        # Calculate layout with spacing proportional to node count to prevent overlap
        num_nodes = len(self.graph)
        if num_nodes > 0:
            # k controls node spacing: higher k = more space between nodes
            k = 2.0 / (num_nodes ** 0.5) if num_nodes > 1 else 1.0
            pos = nx.spring_layout(self.graph, k=k, iterations=50, seed=42)
        else:
            pos = {}

        nx.draw(self.graph, pos=pos, with_labels=True,
                node_color='#38b4b6ff', edge_color='#284d5cff', font_color='#203445ff',
                arrows=True, node_size=300, font_size=8)
        # Add title showing node count info if enabled
        if self.show_info and self.was_truncated:
            plt.title(f"{len(self.graph)}/{self.original_node_count} nodes", fontsize=10, color='#666666')

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
