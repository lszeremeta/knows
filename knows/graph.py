import datetime
import random
from typing import Any, Callable, Dict, List, Optional

import networkx as nx
from faker import Faker

NODE_PROPERTY_GENERATORS: Dict[str, Callable[[Faker], Any]] = {
    'firstName': lambda f: f.first_name(),
    'lastName': lambda f: f.last_name(),
    'company': lambda f: f.company(),
    'job': lambda f: f.job(),
    'phoneNumber': lambda f: f.phone_number(),
    'favoriteColor': lambda f: f.color_name(),
    'postalAddress': lambda f: f.address(),
    'preferredContactMethod': lambda f: f.random_element(
        (
            'inPerson',
            'email',
            'postalMail',
            'phone',
            'textMessage',
            'videoCall',
            'noPreference',
        )
    ),
}

EDGE_PROPERTY_GENERATORS: Dict[str, Callable[[Faker], Any]] = {
    'strength': lambda f: f.random_int(min=1, max=100),
    'lastMeetingCity': lambda f: f.city(),
    'lastMeetingDate': lambda f: f.date_between(
        datetime.date(1955, 1, 1), datetime.date(2025, 6, 28)
    ).isoformat(),
    'meetingCount': lambda f: f.random_int(min=1, max=10000),
}

SAME_EDGE_PROPS = frozenset({
    'lastMeetingCity',
    'lastMeetingDate',
    'meetingCount',
})

# Properties computed from graph structure (post-generation)
COMPUTED_NODE_PROPERTIES = frozenset({'friendCount'})

# All available node properties (generated + computed)
NODE_PROPERTIES = list(NODE_PROPERTY_GENERATORS.keys()) + list(COMPUTED_NODE_PROPERTIES)
EDGE_PROPERTIES = list(EDGE_PROPERTY_GENERATORS.keys())


class Graph:
    def __init__(self, num_nodes: int, num_edges: int,
                 node_props: Optional[List[str]] = None,
                 edge_props: Optional[List[str]] = None,
                 seed: Optional[int] = None,
                 schema: Optional[dict] = None):
        self.graph = nx.DiGraph()
        self.num_nodes = num_nodes
        self.num_edges = num_edges
        self.random = random.Random(seed)
        self.faker = Faker()
        if seed is not None:
            self.faker.seed_instance(seed)

        # Schema-based configuration
        self.schema = schema
        if schema:
            from .schema import (
                schema_to_generators,
                get_schema_properties,
                get_symmetric_edge_properties,
                get_computed_node_properties,
            )
            (self.node_generators,
             self.edge_generators,
             self.node_label,
             self.edge_label) = schema_to_generators(schema)
            schema_node_props, schema_edge_props = get_schema_properties(schema)
            # Use schema properties (ignore -np/-ep when schema is used)
            self.node_props = schema_node_props
            self.edge_props = schema_edge_props
            # Get symmetric edge properties from schema
            self.symmetric_edge_props = get_symmetric_edge_properties(schema)
            # Get computed node properties from schema
            self.computed_node_props = get_computed_node_properties(schema)
            self.use_schema = True
        else:
            # Default behavior - use built-in generators
            self.node_generators = NODE_PROPERTY_GENERATORS
            self.edge_generators = EDGE_PROPERTY_GENERATORS
            self.node_label = 'Person'
            self.edge_label = 'knows'
            self.node_props = node_props if node_props is not None else ['firstName', 'lastName']
            self.edge_props = edge_props if edge_props is not None else ['strength', 'lastMeetingDate']
            # Use hardcoded symmetric properties for default mode
            self.symmetric_edge_props = SAME_EDGE_PROPS
            # Use hardcoded computed properties for default mode
            self.computed_node_props = {'friendCount': 'degree'} if 'friendCount' in self.node_props else {}
            self.use_schema = False

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
        while len(self.graph.edges) < self.num_edges:
            u, v = self.random.sample(nodes, 2)
            if not self.graph.has_edge(u, v):
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
