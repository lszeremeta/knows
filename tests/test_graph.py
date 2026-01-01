import datetime

import pytest

from knows.graph import Graph, SAME_EDGE_PROPS, NODE_PROPERTIES, COMPUTED_NODE_PROPERTIES


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
        assert 'friendCount' in props and isinstance(props['friendCount'], int)
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


def test_friendcount_equals_actual_degree():
    """friendCount should equal the actual number of unique neighbors."""
    graph = Graph(
        5,
        6,
        node_props=['firstName', 'friendCount'],
        seed=42,
    )
    graph.generate()
    
    # Create undirected view to count unique neighbors
    undirected = graph.graph.to_undirected(as_view=True)
    
    for node_id, props in graph.graph.nodes(data=True):
        expected_degree = undirected.degree(node_id)
        assert props['friendCount'] == expected_degree, \
            f"Node {node_id}: friendCount={props['friendCount']} != degree={expected_degree}"


def test_friendcount_with_bidirectional_edges():
    """friendCount should count bidirectional connections as one friend."""
    # With 2 nodes and 2 edges, both directions exist (N1->N2, N2->N1)
    # Each node should have friendCount=1 (one unique friend)
    graph = Graph(
        2,
        2,
        node_props=['friendCount'],
        seed=0,
    )
    graph.generate()
    
    for node_id, props in graph.graph.nodes(data=True):
        assert props['friendCount'] == 1, \
            f"Node {node_id} should have exactly 1 friend (bidirectional edge counts as 1)"


def test_friendcount_isolated_except_one():
    """Test friendCount when some nodes have no connections."""
    # 5 nodes, 1 edge means 3 nodes are isolated
    graph = Graph(
        5,
        1,
        node_props=['friendCount'],
        seed=123,
    )
    graph.generate()
    
    friend_counts = [props['friendCount'] for _, props in graph.graph.nodes(data=True)]
    
    # Exactly 2 nodes should have friendCount=1, rest should have 0
    assert friend_counts.count(1) == 2
    assert friend_counts.count(0) == 3


def test_friendcount_fully_connected():
    """Test friendCount in a nearly fully connected graph."""
    # 4 nodes, 12 edges = fully connected (each node connects to all others in both directions)
    graph = Graph(
        4,
        12,  # 4 * 3 = 12 (full directed graph)
        node_props=['friendCount'],
        seed=0,
    )
    graph.generate()
    
    for node_id, props in graph.graph.nodes(data=True):
        # Each node should be friends with all 3 other nodes
        assert props['friendCount'] == 3, \
            f"Node {node_id} should have 3 friends in fully connected graph"


def test_friendcount_not_generated_when_not_requested():
    """friendCount should not appear if not in node_props."""
    graph = Graph(
        3,
        2,
        node_props=['firstName', 'lastName'],
    )
    graph.generate()
    
    for _, props in graph.graph.nodes(data=True):
        assert 'friendCount' not in props


def test_friendcount_in_node_properties_list():
    """Ensure friendCount is listed in NODE_PROPERTIES."""
    assert 'friendCount' in NODE_PROPERTIES


def test_friendcount_in_computed_properties():
    """Ensure friendCount is marked as computed property."""
    assert 'friendCount' in COMPUTED_NODE_PROPERTIES


def test_friendcount_reproducibility_with_seed():
    """friendCount should be reproducible with same seed."""
    graph1 = Graph(10, 15, node_props=['friendCount'], seed=999)
    graph1.generate()
    
    graph2 = Graph(10, 15, node_props=['friendCount'], seed=999)
    graph2.generate()
    
    counts1 = [props['friendCount'] for _, props in graph1.graph.nodes(data=True)]
    counts2 = [props['friendCount'] for _, props in graph2.graph.nodes(data=True)]
    
    assert counts1 == counts2