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


def test_default_viz_limit_is_50():
    """Tests that the default visualization limit is 50 nodes."""
    from knows.graph_drawer import DEFAULT_VIZ_LIMIT
    assert DEFAULT_VIZ_LIMIT == 50


def test_graph_truncation_with_limit():
    """Tests that large graphs are truncated to the specified limit."""
    graph = nx.DiGraph()
    for i in range(100):
        graph.add_node(i)
    for i in range(50):
        graph.add_edge(i, i + 1)

    drawer = GraphDrawer(graph, max_nodes=30)
    assert drawer.was_truncated is True
    assert len(drawer.graph) == 30
    assert drawer.original_node_count == 100


def test_graph_no_truncation_when_under_limit():
    """Tests that small graphs are not truncated."""
    graph = nx.DiGraph()
    for i in range(20):
        graph.add_node(i)

    drawer = GraphDrawer(graph, max_nodes=50)
    assert drawer.was_truncated is False
    assert len(drawer.graph) == 20


def test_no_limit_shows_all_nodes():
    """Tests that max_nodes=0 disables truncation."""
    graph = nx.DiGraph()
    for i in range(100):
        graph.add_node(i)

    drawer = GraphDrawer(graph, max_nodes=0)
    assert drawer.was_truncated is False
    assert len(drawer.graph) == 100


def test_truncation_info():
    """Tests the get_truncation_info method."""
    graph = nx.DiGraph()
    for i in range(100):
        graph.add_node(i)
    for i in range(50):
        graph.add_edge(i, i + 1)

    drawer = GraphDrawer(graph, max_nodes=40)
    was_truncated, displayed, original = drawer.get_truncation_info()
    assert was_truncated is True
    assert displayed == 40
    assert original == 100


def test_show_info_in_svg_when_truncated():
    """Tests that truncation info appears in SVG when show_info=True."""
    graph = nx.DiGraph()
    for i in range(100):
        graph.add_node(i)
    for i in range(50):
        graph.add_edge(i, i + 1)

    drawer = GraphDrawer(graph, max_nodes=30, show_info=True)
    svg = drawer.to_svg()
    assert '30/100 nodes' in svg


def test_hide_info_in_svg_when_truncated():
    """Tests that truncation info is hidden when show_info=False."""
    graph = nx.DiGraph()
    for i in range(100):
        graph.add_node(i)
    for i in range(50):
        graph.add_edge(i, i + 1)

    drawer = GraphDrawer(graph, max_nodes=30, show_info=False)
    svg = drawer.to_svg()
    assert '30/100 nodes' not in svg


def test_truncation_prioritizes_high_degree_nodes():
    """Tests that truncation starts from the highest-degree node."""
    graph = nx.DiGraph()
    # Create a star graph with node 0 as the hub
    for i in range(1, 20):
        graph.add_node(i)
        graph.add_edge(0, i)

    drawer = GraphDrawer(graph, max_nodes=10)
    # Node 0 (hub) should be in the subgraph
    assert 0 in drawer.graph.nodes()


def test_truncation_spans_multiple_components():
    """Tests that truncation collects nodes from multiple disconnected components."""
    graph = nx.DiGraph()
    # Create 5 disconnected components of 10 nodes each
    for component in range(5):
        base = component * 10
        for i in range(10):
            graph.add_node(base + i)
        for i in range(9):
            graph.add_edge(base + i, base + i + 1)

    drawer = GraphDrawer(graph, max_nodes=25)
    # Should have exactly 25 nodes from multiple components
    assert len(drawer.graph) == 25
    assert drawer.was_truncated is True
