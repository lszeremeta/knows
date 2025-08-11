from unittest.mock import patch

import matplotlib

# Use 'Agg' backend for matplotlib to avoid GUI issues in headless environments
matplotlib.use('Agg')

import networkx as nx

from knows.graph_drawer import GraphDrawer


def test_graph_drawer_initialization():
    """
    Tests whether GraphDrawer initializes correctly with a given graph.
    """
    graph = nx.DiGraph()
    drawer = GraphDrawer(graph)
    assert drawer.graph is graph


def test_to_svg_returns_string():
    """
    Tests whether the to_svg method returns a string representation of the graph in SVG format.
    """
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    drawer = GraphDrawer(graph)
    svg_output = drawer.to_svg()
    assert isinstance(svg_output, str)


def test_svg_output_length():
    """
    Tests whether the SVG output is of reasonable length for a simple graph.
    """
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    drawer = GraphDrawer(graph)
    svg_output = drawer.to_svg()
    assert len(svg_output) > 100


def test_svg_output_contains_svg_tag():
    """
    Tests whether the SVG output contains the '<svg' tag, indicating a valid SVG format.
    """
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    drawer = GraphDrawer(graph)
    svg_output = drawer.to_svg()
    assert '<svg' in svg_output


def test_to_png_returns_bytes():
    """Ensure PNG export returns bytes with PNG signature."""
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    drawer = GraphDrawer(graph)
    png_output = drawer.to_png()
    assert isinstance(png_output, bytes)
    assert png_output.startswith(b'\x89PNG')


def test_to_jpg_returns_bytes():
    """Ensure JPG export returns bytes with JPEG signature."""
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    drawer = GraphDrawer(graph)
    jpg_output = drawer.to_jpg()
    assert isinstance(jpg_output, bytes)
    assert jpg_output.startswith(b'\xff\xd8')


def test_to_pdf_returns_bytes():
    """Ensure PDF export returns bytes with PDF signature."""
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    drawer = GraphDrawer(graph)
    pdf_output = drawer.to_pdf()
    assert isinstance(pdf_output, bytes)
    assert pdf_output.startswith(b'%PDF')


def test_graph_properties_unchanged_after_drawing():
    """
    Tests whether the properties of the graph remain unchanged after drawing.
    """
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    num_nodes_before = len(graph.nodes())
    num_edges_before = len(graph.edges())

    drawer = GraphDrawer(graph)
    drawer.draw()

    num_nodes_after = len(graph.nodes())
    num_edges_after = len(graph.edges())

    assert num_nodes_before == num_nodes_after
    assert num_edges_before == num_edges_after


@patch('knows.graph_drawer.TKINTER_AVAILABLE', True)
@patch('matplotlib.pyplot.show')
def test_configure_and_draw_calls_show(mock_show):
    """
    Tests whether the configure_and_draw method calls the matplotlib.pyplot.show function.
    """
    graph = nx.DiGraph()
    graph.add_node(1)
    drawer = GraphDrawer(graph)
    drawer.configure_and_draw()
    mock_show.assert_called_once()
