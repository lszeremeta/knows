import json

from knows.graph import Graph
from knows.output_format import OutputFormat


def test_output_format_graphml():
    """
    Tests if the graph is correctly converted to GraphML format.
    """
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    graphml_output = output_format.to_format('graphml')
    assert '<graphml' in graphml_output
    assert '<node' in graphml_output
    assert '<edge' in graphml_output
    assert 'N1' in graphml_output
    assert 'N2' in graphml_output
    assert 'N3' in graphml_output


def test_output_format_yarspg():
    """
    Tests if the graph is correctly converted to YARS-PG format.
    """
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    yarspg_output = output_format.to_format('yarspg')
    assert '(' in yarspg_output
    assert ')-({' in yarspg_output
    assert 'knows' in yarspg_output
    assert 'firstname' in yarspg_output
    assert 'lastname' in yarspg_output
    assert 'N1' in yarspg_output
    assert 'N2' in yarspg_output
    assert 'N3' in yarspg_output


def test_output_format_csv():
    """Tests CSV conversion for nodes and edges."""
    graph = Graph(2, 1)
    graph.generate()
    output_format = OutputFormat(graph)
    nodes_csv, edges_csv = output_format.to_format('csv')
    assert 'id,label,firstname,lastname' in nodes_csv
    assert 'id,id_from,id_to,label,createDate' in edges_csv
    assert len(nodes_csv.splitlines()) == 3  # Header + 2 nodes
    assert len(edges_csv.splitlines()) == 2  # Header + 1 edge
    assert 'N1' in nodes_csv
    assert 'N1' in edges_csv
    assert 'N2' in nodes_csv
    assert 'N2' in edges_csv


def test_output_format_json():
    """
    Tests if the graph is correctly converted to JSON format.
    """
    graph = Graph(2, 1)
    graph.generate()
    output_format = OutputFormat(graph)
    json_output = output_format.to_format('json')
    json_data = json.loads(json_output)
    assert 'nodes' in json_data
    assert 'links' in json_data
    assert len(json_data['nodes']) == 2
    assert len(json_data['links']) == 1
    assert 'N1' in json_output
    assert 'N2' in json_output


def test_output_format_gexf():
    """
    Tests if the graph is correctly converted to GEXF format.
    """
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    gexf_output = output_format.to_format('gexf')
    assert '<gexf' in gexf_output
    assert '<nodes>' in gexf_output
    assert '<edges>' in gexf_output
    assert 'N1' in gexf_output
    assert 'N2' in gexf_output
    assert 'N3' in gexf_output


def test_output_format_gml():
    """
    Tests if the graph is correctly converted to GML format.
    """
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    gml_output = output_format.to_format('gml')
    assert 'graph' in gml_output
    assert 'node' in gml_output
    assert 'edge' in gml_output
    assert 'N1' in gml_output
    assert 'N2' in gml_output
    assert 'N3' in gml_output


def test_output_format_adjacency_list():
    """
    Tests if the graph is correctly converted to adjacency list format.
    """
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    adjacency_list_output = output_format.to_format('adjacency_list')
    assert len(adjacency_list_output.splitlines()) == 3  # One line per node
    assert 'N1' in adjacency_list_output
    assert 'N2' in adjacency_list_output
    assert 'N3' in adjacency_list_output
