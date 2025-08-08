import datetime
import random

import networkx as nx
from faker import Faker

NODE_PROPERTY_GENERATORS: dict[str, callable] = {
    'firstName': lambda f: f.first_name(),
    'lastName': lambda f: f.last_name(),
    'company': lambda f: f.company(),
    'job': lambda f: f.job(),
    'phoneNumber': lambda f: f.phone_number(),
    'favoriteColor': lambda f: f.color_name(),
    'postalAddress': lambda f: f.address(),
    'friendCount': lambda f: f.random_int(min=1, max=1000),
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

EDGE_PROPERTY_GENERATORS: dict[str, callable] = {
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

NODE_PROPERTIES = list(NODE_PROPERTY_GENERATORS.keys())
EDGE_PROPERTIES = list(EDGE_PROPERTY_GENERATORS.keys())

from typing import Optional, List


class Graph:
    def __init__(self, num_nodes: int, num_edges: int,
                 node_props: Optional[List[str]] = None,
                 edge_props: Optional[List[str]] = None,
                 seed: Optional[int] = None):
        self.graph = nx.DiGraph()
        self.num_nodes = num_nodes
        self.num_edges = num_edges
        self.node_props = node_props or ['firstName', 'lastName']
        self.edge_props = edge_props or ['strength', 'lastMeetingDate']
        self.random = random.Random(seed)
        self.faker = Faker()
        if seed is not None:
            self.faker.seed_instance(seed)

    def generate(self) -> None:
        self._validate_parameters()
        self._validate_properties()
        self._add_nodes()
        self._add_edges()

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
            properties = {'label': 'Person'}
            for prop in self.node_props:
                generator = NODE_PROPERTY_GENERATORS[prop]
                properties[prop] = generator(self.faker)
            self.graph.add_node(f"N{i}", **properties)

    def _add_edges(self) -> None:
        nodes = list(self.graph.nodes)
        while len(self.graph.edges) < self.num_edges:
            u, v = self.random.sample(nodes, 2)
            if not self.graph.has_edge(u, v):
                properties = {'label': 'knows'}
                for prop in self.edge_props:
                    generator = EDGE_PROPERTY_GENERATORS[prop]
                    properties[prop] = generator(self.faker)
                if self.graph.has_edge(v, u):
                    reverse_props = self.graph[v][u]
                    for prop in SAME_EDGE_PROPS:
                        if prop in self.edge_props and prop in reverse_props:
                            properties[prop] = reverse_props[prop]
                self.graph.add_edge(u, v, **properties)
