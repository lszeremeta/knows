import random
from typing import List, Optional

import networkx as nx
from faker import Faker

from .schema import (
    get_computed_node_properties,
    get_schema_properties,
    get_symmetric_edge_properties,
    schema_to_generators,
)

# Built-in graph profile expressed in the same format as --schema files.
# A standalone copy lives in schema-examples/default_schema.json.
DEFAULT_SCHEMA: dict = {
    "nodeLabel": "Person",
    "edgeLabel": "knows",
    "nodeProperties": {
        "firstName": "FirstName",
        "lastName": "LastName",
        "company": "Company",
        "job": "Job",
        "phoneNumber": "Phone",
        "favoriteColor": "Color",
        "postalAddress": "Address",
        "preferredContactMethod": {
            "enum": [
                "inPerson",
                "email",
                "postalMail",
                "phone",
                "textMessage",
                "videoCall",
                "noPreference",
            ]
        },
    },
    "edgeProperties": {
        "strength": {"type": "Int", "min": 1, "max": 100},
        "lastMeetingCity": {"type": "City", "symmetric": True},
        "lastMeetingDate": {
            "type": "Date",
            "min": "1955-01-01",
            "max": "2025-06-28",
            "symmetric": True,
        },
        "meetingCount": {"type": "Int", "min": 1, "max": 10000, "symmetric": True},
    },
    "computedNodeProperties": {
        "friendCount": "degree",
    },
}

# Properties used when -np/-ep are not given on the command line.
DEFAULT_NODE_PROPS = ['firstName', 'lastName']
DEFAULT_EDGE_PROPS = ['strength', 'lastMeetingDate']

# Derived views of the default schema, kept as module-level constants for
# the CLI choices and backward compatibility.
SAME_EDGE_PROPS = get_symmetric_edge_properties(DEFAULT_SCHEMA)

# Properties computed from graph structure (post-generation)
COMPUTED_NODE_PROPERTIES = frozenset(get_computed_node_properties(DEFAULT_SCHEMA))

# All available node properties (generated + computed)
_GENERATED_NODE_PROPS, _GENERATED_EDGE_PROPS = get_schema_properties(DEFAULT_SCHEMA)
NODE_PROPERTIES = _GENERATED_NODE_PROPS + list(get_computed_node_properties(DEFAULT_SCHEMA))
EDGE_PROPERTIES = _GENERATED_EDGE_PROPS


class Graph:
    def __init__(self, num_nodes: int, num_edges: int,
                 node_props: Optional[List[str]] = None,
                 edge_props: Optional[List[str]] = None,
                 seed: Optional[int] = None,
                 schema: Optional[dict] = None,
                 locale: Optional[str] = None):
        self.graph = nx.DiGraph()
        self.num_nodes = num_nodes
        self.num_edges = num_edges
        self.random = random.Random(seed)
        self.faker = Faker(locale)
        if seed is not None:
            self.faker.seed_instance(seed)

        # Both modes share one pipeline: the default mode is just the
        # built-in DEFAULT_SCHEMA with -np/-ep selecting a subset of it.
        self.schema = schema
        self.use_schema = schema is not None
        active_schema = schema if schema is not None else DEFAULT_SCHEMA

        (self.node_generators,
         self.edge_generators,
         self.node_label,
         self.edge_label) = schema_to_generators(active_schema)
        self.symmetric_edge_props = get_symmetric_edge_properties(active_schema)
        schema_node_props, schema_edge_props = get_schema_properties(active_schema)
        computed_props = get_computed_node_properties(active_schema)

        if self.use_schema:
            # A schema file always uses all of its properties
            # (-np/-ep are ignored when --schema is given).
            self.node_props = schema_node_props
            self.edge_props = schema_edge_props
            self.computed_node_props = computed_props
        else:
            self.node_props = node_props if node_props is not None else list(DEFAULT_NODE_PROPS)
            self.edge_props = edge_props if edge_props is not None else list(DEFAULT_EDGE_PROPS)
            self.computed_node_props = {
                prop: comp_type for prop, comp_type in computed_props.items()
                if prop in self.node_props
            }

    def generate(self) -> None:
        self._validate_parameters()
        if not self.use_schema:
            self._validate_properties()
        self._add_nodes()
        self._add_edges()
        self._compute_structural_properties()

    def _validate_parameters(self) -> None:
        if self.num_nodes <= 1 or self.num_edges < 0:
            raise ValueError("Number of nodes must be greater than 1 and number of edges must be non-negative.")
        if self.num_edges > self.num_nodes * (self.num_nodes - 1):
            raise ValueError("Too many edges for the given number of nodes.")

    def _validate_properties(self) -> None:
        for prop in self.node_props:
            if prop not in NODE_PROPERTIES:
                raise ValueError(f"Unknown node property: {prop}")
        for prop in self.edge_props:
            if prop not in EDGE_PROPERTIES:
                raise ValueError(f"Unknown edge property: {prop}")

    def _add_nodes(self) -> None:
        for i in range(1, self.num_nodes + 1):
            properties = {'label': self.node_label}
            for prop in self.node_props:
                if prop in self.node_generators:
                    generator = self.node_generators[prop]
                    properties[prop] = generator(self.faker)
            self.graph.add_node(f"N{i}", **properties)

    def _add_edges(self) -> None:
        nodes = list(self.graph.nodes)
        max_edges = len(nodes) * (len(nodes) - 1)
        if self.num_edges > max_edges // 2:
            # Dense graphs: rejection sampling degenerates near saturation,
            # so draw the exact edge set from all candidate pairs instead.
            pairs = [(u, v) for u in nodes for v in nodes if u != v]
            for u, v in self.random.sample(pairs, self.num_edges):
                self._add_edge(u, v)
        else:
            while len(self.graph.edges) < self.num_edges:
                u, v = self.random.sample(nodes, 2)
                if not self.graph.has_edge(u, v):
                    self._add_edge(u, v)

    def _add_edge(self, u: str, v: str) -> None:
        """Generate properties and add one directed edge from *u* to *v*."""
        properties = {'label': self.edge_label}
        for prop in self.edge_props:
            if prop in self.edge_generators:
                generator = self.edge_generators[prop]
                properties[prop] = generator(self.faker)
        # Apply symmetric properties from reverse edge if it exists
        if self.graph.has_edge(v, u):
            reverse_props = self.graph[v][u]
            for prop in self.symmetric_edge_props:
                if prop in self.edge_props and prop in reverse_props:
                    properties[prop] = reverse_props[prop]
        self.graph.add_edge(u, v, **properties)

    def _compute_structural_properties(self) -> None:
        """Compute node properties that depend on graph structure.

        This method is called after edge generation to ensure properties
        like degree reflect the actual graph topology.
        """
        if not self.computed_node_props:
            return

        # Compute degree properties (unique connections in undirected view)
        degree_props = [
            prop for prop, comp_type in self.computed_node_props.items()
            if comp_type == 'degree'
        ]

        if degree_props:
            # Using undirected view is O(1) per node for degree lookup
            undirected_view = self.graph.to_undirected(as_view=True)
            for node_id in self.graph.nodes():
                degree = undirected_view.degree(node_id)
                for prop in degree_props:
                    self.graph.nodes[node_id][prop] = degree
