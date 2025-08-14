import datetime

import pytest

from knows.graph import Graph, SAME_EDGE_PROPS


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


def test_graph_node_properties_are_correctly_set():
    """
    Test if the node properties are correctly set in the graph.

    Ensures that each node in the graph has the expected properties: 'firstName', 'lastName', and 'label'.
    """
    graph = Graph(3, 2)
    graph.generate()
    for _, properties in graph.graph.nodes(data=True):
        assert 'firstName' in properties
        assert 'lastName' in properties
        assert properties['label'] == 'Person'


def test_graph_custom_properties():
    """Ensure custom node and edge properties are applied."""
    graph = Graph(
        3,
        1,
        node_props=['firstName', 'favoriteColor', 'job'],
        edge_props=['strength', 'lastMeetingCity'],
    )
    graph.generate()
    for _, properties in graph.graph.nodes(data=True):
        assert 'firstName' in properties
        assert 'favoriteColor' in properties
        assert 'job' in properties
        assert 'lastName' not in properties
    for _, _, properties in graph.graph.edges(data=True):
        assert 'strength' in properties
        assert 'lastMeetingCity' in properties
        assert 'lastMeetingDate' not in properties


def test_invalid_property_name_raises_error():
    """Unknown property names should raise ValueError."""
    with pytest.raises(ValueError):
        graph = Graph(2, 1, node_props=['unknown'])
        graph.generate()


def test_graph_seed_reproducibility():
    """Graphs generated with the same seed should be identical."""
    graph1 = Graph(5, 4, seed=42)
    graph1.generate()
    graph2 = Graph(5, 4, seed=42)
    graph2.generate()
    assert list(graph1.graph.nodes(data=True)) == list(graph2.graph.nodes(data=True))
    assert list(graph1.graph.edges(data=True)) == list(graph2.graph.edges(data=True))


def test_graph_seed_variation():
    """Different seeds should yield different graphs."""
    graph1 = Graph(5, 4, seed=1)
    graph1.generate()
    graph2 = Graph(5, 4, seed=2)
    graph2.generate()
    assert list(graph1.graph.nodes(data=True)) != list(graph2.graph.nodes(data=True)) or \
           list(graph1.graph.edges(data=True)) != list(graph2.graph.edges(data=True))


def test_new_node_and_edge_properties():
    """Ensure new properties are generated within valid ranges."""
    graph = Graph(
        4,
        3,
        node_props=['postalAddress', 'friendCount', 'preferredContactMethod'],
        edge_props=list(SAME_EDGE_PROPS),
    )
    graph.generate()

    for _, props in graph.graph.nodes(data=True):
        assert 'postalAddress' in props and isinstance(props['postalAddress'], str)
        assert 1 <= props['friendCount'] <= 1000
        assert props['preferredContactMethod'] in {
            'inPerson',
            'email',
            'postalMail',
            'phone',
            'textMessage',
            'videoCall',
            'noPreference',
        }

    for _, _, props in graph.graph.edges(data=True):
        assert 'lastMeetingCity' in props and isinstance(props['lastMeetingCity'], str)
        date = datetime.date.fromisoformat(props['lastMeetingDate'])
        assert datetime.date(1955, 1, 1) <= date <= datetime.date(2025, 6, 28)
        assert 1 <= props['meetingCount'] <= 10000


def test_paired_edge_properties_sync():
    """Paired edges should share last meeting data."""
    graph = Graph(
        2,
        2,
        edge_props=list(SAME_EDGE_PROPS),
        seed=0,
    )
    graph.generate()

    props_ab = graph.graph['N1']['N2']
    props_ba = graph.graph['N2']['N1']
    for key in SAME_EDGE_PROPS:
        assert props_ab[key] == props_ba[key]
