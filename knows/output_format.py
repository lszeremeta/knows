import csv
import inspect
import io
import json

import networkx as nx

from .graph_drawer import GraphDrawer, DEFAULT_VIZ_LIMIT


class OutputFormat:
    """A class to represent various output formats of a graph.

    Attributes:
        graph (Graph): An instance of the Graph class.
        viz_limit (int): Maximum nodes to display in visual outputs.
        show_info (bool): Whether to show node count info on visualizations.
    """

    def __init__(self, graph, viz_limit: int = DEFAULT_VIZ_LIMIT, show_info: bool = True):
        """Inits OutputFormat with a graph.

        Args:
            graph (Graph): An instance of the Graph class.
            viz_limit (int): Maximum nodes for visual formats. Set to 0 to disable.
            show_info (bool): Whether to show node count info on visualizations.
        """
        self.graph = graph
        self.viz_limit = viz_limit
        self.show_info = show_info

    def to_format(self, format_type: str) -> str:
        """Converts the graph to a specified format.

        Args:
            format_type (str): The format type to convert the graph into.

        Returns:
            str: The graph in the specified format.
        """
        format_methods = {
            'graphml': self._to_graphml,
            'yarspg': self._to_yarspg,
            'csv': self._to_csv,
            'cypher': self._to_cypher,
            'gexf': self._to_gexf,
            'gml': self._to_gml,
            'svg': self._to_svg,
            'png': self._to_png,
            'jpg': self._to_jpg,
            'pdf': self._to_pdf,
            'adjacency_list': self._to_adjacency_list,
            'multiline_adjacency_list': self._to_multiline_adjacency_list,
            'edge_list': self._to_edge_list,
            'json': self._to_json,
        }
        return format_methods[format_type]()

    def _to_graphml(self) -> str:
        """Converts the graph to GraphML format.

        Returns:
            str: The graph in GraphML format.
        """
        return '\n'.join(nx.generate_graphml(self.graph.graph))

    def _to_yarspg(self) -> str:
        """Converts the graph to YARS-PG format.

        Returns:
            str: The graph in YARS-PG format.
        """
        nodes_output = [self._format_node_yarspg(node) for node in self.graph.graph.nodes(data=True)]
        edges_output = [self._format_edge_yarspg(edge) for edge in self.graph.graph.edges(data=True)]
        return '\n'.join(nodes_output + edges_output)

    @staticmethod
    def _format_node_yarspg(node: tuple) -> str:
        """Formats a node in YARS-PG format.

        Args:
            node (tuple): A tuple containing the node ID and properties.

        Returns:
            str: The node in YARS-PG format.
        """
        node_id, properties = node
        label = properties.get('label', 'label')
        prop_list = ', '.join([f'"{key}": "{value}"' for key, value in properties.items() if key != 'label'])
        return f"({node_id} {{\"{label}\"}}[{prop_list}])"

    @staticmethod
    def _format_edge_yarspg(edge: tuple) -> str:
        """Formats an edge in YARS-PG format.

        Args:
            edge (tuple): A tuple containing the source node, target node, and properties.

        Returns:
            str: The edge in YARS-PG format.
        """
        u, v, properties = edge
        label = properties.get('label', 'label')
        prop_list = ', '.join([f'"{key}": "{value}"' for key, value in properties.items() if key != 'label'])
        return f"({u})-({{\"{label}\"}}[{prop_list}])->({v})"

    def _to_csv(self) -> tuple[str, str]:
        """Converts the graph to CSV format.

        Returns:
            tuple[str, str]: Nodes and edges in CSV format.
        """
        node_prop_keys: list[str] = []
        for _, prop in self.graph.graph.nodes(data=True):
            for key in prop.keys():
                if key not in node_prop_keys:
                    node_prop_keys.append(key)
        node_headers = ['id'] + node_prop_keys

        node_buffer = io.StringIO()
        writer = csv.writer(node_buffer)
        writer.writerow(node_headers)
        for node_id, prop in self.graph.graph.nodes(data=True):
            row = [node_id] + [prop.get(key, '') for key in node_prop_keys]
            writer.writerow(row)
        nodes_csv = node_buffer.getvalue().strip()

        edge_prop_keys: list[str] = []
        for _, _, prop in self.graph.graph.edges(data=True):
            for key in prop.keys():
                if key not in edge_prop_keys:
                    edge_prop_keys.append(key)
        edge_headers = ['id', 'id_from', 'id_to'] + edge_prop_keys

        edge_buffer = io.StringIO()
        writer = csv.writer(edge_buffer)
        writer.writerow(edge_headers)
        for edge_id, (source, target, prop) in enumerate(self.graph.graph.edges(data=True), start=1):
            row = [f"E{edge_id}", source, target] + [prop.get(key, '') for key in edge_prop_keys]
            writer.writerow(row)
        edges_csv = edge_buffer.getvalue().strip()

        return nodes_csv, edges_csv

    def _to_cypher(self) -> str:
        """Converts the graph to Cypher format.

        Returns:
            str: The graph as a sequence of Cypher CREATE statements.
        """
        cypher_statements: list[str] = []
        for node_id, properties in self.graph.graph.nodes(data=True):
            label = properties.get('label', '')
            props = ', '.join([f"{k}: \"{v}\"" for k, v in properties.items() if k != 'label'])
            cypher_statements.append(f"CREATE ({node_id}:{label} {{{props}}})")
        for source, target, properties in self.graph.graph.edges(data=True):
            label = properties.get('label', '')
            props = ', '.join([f"{k}: \"{v}\"" for k, v in properties.items() if k != 'label'])
            cypher_statements.append(f"CREATE ({source})-[:{label} {{{props}}}]->({target})")
        return '\n'.join(cypher_statements)

    def _to_svg(self) -> str:
        """Converts the graph to SVG format.

        Returns:
            str: The graph in SVG format.
        """
        drawer = GraphDrawer(self.graph.graph, max_nodes=self.viz_limit, show_info=self.show_info)
        with io.BytesIO() as buffer:
            drawer._draw_to_buffer(buffer, 'svg')
            return buffer.getvalue().decode('utf-8')

    def _to_png(self) -> bytes:
        """Converts the graph to PNG format.

        Returns:
            bytes: The graph image in PNG format.
        """
        drawer = GraphDrawer(self.graph.graph, max_nodes=self.viz_limit, show_info=self.show_info)
        return drawer.to_png()

    def _to_jpg(self) -> bytes:
        """Converts the graph to JPG format.

        Returns:
            bytes: The graph image in JPG format.
        """
        drawer = GraphDrawer(self.graph.graph, max_nodes=self.viz_limit, show_info=self.show_info)
        return drawer.to_jpg()

    def _to_pdf(self) -> bytes:
        """Converts the graph to PDF format.

        Returns:
            bytes: The graph in PDF format.
        """
        drawer = GraphDrawer(self.graph.graph, max_nodes=self.viz_limit, show_info=self.show_info)
        return drawer.to_pdf()

    def _to_gexf(self) -> str:
        """Converts the graph to GEXF format.

        Returns:
            str: The graph in GEXF format.
        """
        return '\n'.join(nx.generate_gexf(self.graph.graph))

    def _to_gml(self) -> str:
        """Converts the graph to GML format.

        Returns:
            str: The graph in GML format.
        """
        return '\n'.join(nx.generate_gml(self.graph.graph))

    def _to_adjacency_list(self) -> str:
        """Converts the graph to adjacency list format.

        Returns:
            str: The graph in adjacency list format.
        """
        return '\n'.join(nx.generate_adjlist(self.graph.graph))

    def _to_multiline_adjacency_list(self) -> str:
        """Converts the graph to multiline adjacency list format.

        Returns:
            str: The graph in multiline adjacency list format.
        """
        return '\n'.join(nx.generate_multiline_adjlist(self.graph.graph))

    def _to_edge_list(self) -> str:
        """Converts the graph to edge list format.

        Returns:
            str: The graph in edge list format.
        """
        return '\n'.join(nx.generate_edgelist(self.graph.graph, data=True))

    def _to_json(self) -> str:
        """Converts the graph to JSON format with 'edges' key.

        Returns:
            str: The graph in JSON format.
        """
        G = self.graph.graph
        data = nx.node_link_data(G, edges="edges")
        return json.dumps(data)
