import pytest

from knows.graph import Graph


@pytest.mark.parametrize("num_nodes, num_edges", [(5, 4), (10, 15), (0, 0)])
def test_graph_generation_with_various_sizes(num_nodes: int, num_edges: int):
    """
    Test the graph generation with various sizes.

    Checks if the Graph class correctly generates graphs with the specified number of nodes and edges.
    Additionally, it verifies that a ValueError is raised in scenarios where the number of edges
    not matching the number of nodes (e.g., too many edges for too few nodes, or negative numbers).


    Args:
        num_nodes (int): The number of nodes in the graph.
        num_edges (int): The number of edges in the graph.
    """
    if num_nodes > 0 and num_edges >= 0 and num_edges <= num_nodes * (num_nodes - 1):
        graph = Graph(num_nodes, num_edges)
        graph.generate()
        assert len(graph.graph.nodes) == num_nodes
        assert len(graph.graph.edges) == num_edges
    else:
        with pytest.raises(ValueError):
            graph = Graph(num_nodes, num_edges)
            graph.generate()


def test_graph_node_attributes_are_correctly_set():
    """
    Test if the node attributes are correctly set in the graph.

    Ensures that each node in the graph has the expected attributes: 'firstname', 'lastname', and 'label'.
    """
    graph = Graph(3, 2)
    graph.generate()
    for _, attributes in graph.graph.nodes(data=True):
        assert 'firstname' in attributes
        assert 'lastname' in attributes
        assert attributes['label'] == 'Person'
