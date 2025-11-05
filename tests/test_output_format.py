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
    assert 'firstName' in graphml_output
    assert 'lastName' in graphml_output
    assert 'strength' in graphml_output
    assert 'lastMeetingDate' in graphml_output
    assert graphml_output.count('<node') == 3  # One for each node
    assert graphml_output.count('<edge') == 2  # One for each edge
    assert graphml_output.count('knows') == 2  # One relationship for each edge
    assert graphml_output.count('label') == 2  # One for each edge label


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
    assert 'N1' in yarspg_output
    assert 'N2' in yarspg_output
    assert 'N3' in yarspg_output
    assert yarspg_output.count(')-({') == 2  # One for each edge
    assert yarspg_output.count('knows') == 2  # One relationship for each edge
    assert yarspg_output.count('firstName') == 3  # One for each node
    assert yarspg_output.count('lastName') == 3  # One for each node
    assert yarspg_output.count('strength') == 2  # One for each edge
    assert yarspg_output.count('lastMeetingDate') == 2  # One for each edge


def test_output_format_csv():
    """Tests CSV conversion for nodes and edges."""
    graph = Graph(2, 1)
    graph.generate()
    output_format = OutputFormat(graph)
    nodes_csv, edges_csv = output_format.to_format('csv')
    assert 'id,label,firstName,lastName' in nodes_csv
    assert 'id,id_from,id_to,label,strength,lastMeetingDate' in edges_csv
    assert len(nodes_csv.splitlines()) == 3  # Header + 2 nodes
    assert len(edges_csv.splitlines()) == 2  # Header + 1 edge
    assert 'N1' in nodes_csv
    assert 'N1' in edges_csv
    assert 'N2' in nodes_csv
    assert 'N2' in edges_csv
    assert 'knows' in edges_csv
    assert 'strength' in edges_csv
    assert 'lastMeetingDate' in edges_csv
    assert 'firstName' in nodes_csv
    assert 'lastName' in nodes_csv
    assert 'N3' not in nodes_csv  # Only 2 nodes in this test case
    assert 'N3' not in edges_csv  # Only 2 nodes in this test case


def test_output_format_cypher():
    """Tests Cypher conversion for nodes and edges."""
    graph = Graph(3, 1)
    graph.generate()
    output_format = OutputFormat(graph)
    cypher_output = output_format.to_format('cypher')
    assert 'CREATE' in cypher_output
    assert ']->(' in cypher_output
    assert ')-[' in cypher_output
    assert ':' in cypher_output
    assert 'knows' in cypher_output
    assert 'N1' in cypher_output
    assert 'N2' in cypher_output
    assert 'N3' in cypher_output
    assert not cypher_output.endswith(';')
    assert cypher_output.count('CREATE') == 4  # One for each node and one for the edge
    assert cypher_output.count('knows') == 1  # One relationship creation


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
    assert 'edges' in json_data
    assert len(json_data['nodes']) == 2
    assert len(json_data['edges']) == 1
    assert 'N1' in json_output
    assert 'N2' in json_output
    assert 'N3' not in json_output  # Only 2 nodes in this test case
    assert 'knows' in json_output
    assert json_output.count('"id":') == 2  # One for each node
    assert json_output.count('"source":') == 1  # One for the edge
    assert json_output.count('"target":') == 1  # One for the edge
    assert json_output.count('"strength":') == 1  # One for the edge
    assert json_output.count('"lastMeetingDate":') == 1  # One for the edge
    assert json_output.count('"firstName":') == 2  # One for each node
    assert json_output.count('"lastName":') == 2  # One for each node


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
    assert 'knows' in gml_output
    assert gml_output.count('node') == 3  # One for each node
    assert gml_output.count('edge') == 2  # One for each edge
    assert gml_output.count('strength') == 2  # One for each edge
    assert gml_output.count('lastMeetingDate') == 2  # One for each edge
    assert gml_output.count('firstName') == 3  # One for each node
    assert gml_output.count('lastName') == 3  # One for each node


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


def test_output_format_multiline_adjacency_list():
    """Tests if the graph is converted to multiline adjacency list format."""
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    multiline_output = output_format.to_format('multiline_adjacency_list')
    assert 'N1' in multiline_output
    assert len(multiline_output.splitlines()) >= 3


def test_output_format_edge_list():
    """Tests if the graph is converted to edge list format."""
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    edge_list_output = output_format.to_format('edge_list')
    assert 'knows' in edge_list_output
    assert len(edge_list_output.splitlines()) == 2


def test_output_format_svg():
    """Tests if the graph is converted to SVG format."""
    graph = Graph(3, 2)
    graph.generate()
    output_format = OutputFormat(graph)
    svg_output = output_format.to_format('svg')
    assert '<svg' in svg_output
    assert '</svg>' in svg_output


def test_output_format_png():
    """Tests if the graph is converted to PNG format."""
    graph = Graph(2, 1)
    graph.generate()
    output_format = OutputFormat(graph)
    png_output = output_format.to_format('png')
    assert isinstance(png_output, bytes)
    assert png_output.startswith(b'\x89PNG')


def test_output_format_jpg():
    """Tests if the graph is converted to JPG format."""
    graph = Graph(2, 1)
    graph.generate()
    output_format = OutputFormat(graph)
    jpg_output = output_format.to_format('jpg')
    assert isinstance(jpg_output, bytes)
    assert jpg_output.startswith(b'\xff\xd8')


def test_output_format_jpg_big():
    """Tests if the graph is converted to JPG format for a bigger graph."""
    graph = Graph(500, 300)
    graph.generate()
    output_format = OutputFormat(graph)
    jpg_output = output_format.to_format('jpg')
    assert isinstance(jpg_output, bytes)
    assert jpg_output.startswith(b'\xff\xd8')


def test_output_format_pdf():
    """Tests if the graph is converted to PDF format."""
    graph = Graph(2, 1)
    graph.generate()
    output_format = OutputFormat(graph)
    pdf_output = output_format.to_format('pdf')
    assert isinstance(pdf_output, bytes)
    assert pdf_output.startswith(b'%PDF')
