import random

import networkx as nx
from faker import Faker


class Graph:
    def __init__(self, num_nodes: int, num_edges: int):
        self.graph = nx.DiGraph()
        self.num_nodes = num_nodes
        self.num_edges = num_edges
        self.faker = Faker()

    def generate(self) -> None:
        self._validate_parameters()
        self._add_nodes()
        self._add_edges()

    def _validate_parameters(self) -> None:
        if self.num_nodes <= 1 or self.num_edges < 0:
            raise ValueError("Number of nodes must be greater than 1 and number of edges must be non-negative.")
        if self.num_edges > self.num_nodes * (self.num_nodes - 1):
            raise ValueError("Too many edges for the given number of nodes.")

    def _add_nodes(self) -> None:
        for i in range(1, self.num_nodes + 1):
            first_name, last_name = self.faker.first_name(), self.faker.last_name()
            self.graph.add_node(f"N{i}", label='Person', firstname=first_name, lastname=last_name)

    def _add_edges(self) -> None:
        nodes = list(self.graph.nodes)
        while len(self.graph.edges) < self.num_edges:
            u, v = random.sample(nodes, 2)
            if not self.graph.has_edge(u, v):
                self.graph.add_edge(u, v, label='knows', createDate=self.faker.date())
