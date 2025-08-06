# <img src="https://raw.githubusercontent.com/lszeremeta/knows/main/logo/knows-logo.png" alt="Knows logo" width="300">

[![PyPI](https://img.shields.io/pypi/v/knows)](https://pypi.org/project/knows/) [![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/lszeremeta/knows?label=Docker%20image%20size)](https://hub.docker.com/r/lszeremeta/knows) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10605343.svg)](https://doi.org/10.5281/zenodo.10605343)

Knows is a user-friendly tool for benchmarking property graphs. These graphs are crucial in many fields. Knows supports
multiple output formats and visualization capabilities, making it a go-to tool for educators, researchers, and data
enthusiasts.

## Key Features 🚀

- **Customizable Graph Generation**: Tailor your graphs by specifying the number of nodes and edges.
- **Diverse Output Formats**: Export graphs in formats like GraphML, YARS-PG, CSV, Cypher, GEXF, GML, SVG, JSON, and
  others.
- **Flexible Output Options**: Display results in the console, redirect them, or save them directly to a file.
- **Integrated Graph Visualization**: Conveniently visualize your graphs in SVG format.
- **Intuitive Command-Line Interface (CLI)**: A user-friendly CLI for streamlined graph generation and visualization.
- **Docker Compatibility**: Deploy Knows in Docker containers for a consistent and isolated runtime environment.
- **Selectable Properties**: Choose which node and edge properties should be generated.

## Graph Structure

- Generates graphs with specified or random nodes and edges.
- Creates directed graphs.
- Nodes are labeled `Person` with unique IDs (`N1, N2, N3, ..., Nn`).
- Nodes feature `firstName` and `lastName` properties by default.
- Edges are labeled `knows` and include a `createDate` property by default.
- Additional node properties: `favoriteColor`, `company`, `job`, `phoneNumber`.
- Additional edge properties: `meetingCity`, `strength`.
- Edges have random nodes, avoiding cycles.

## Installation 🛠️

You can install knows via PyPI Docker or run it from the source code.

### Install via PyPI

1. **Installation**:
   ```shell
   pip install knows[draw]
   ```
   The `draw` installs a `matplotlib` library for graph visualization. You can omit the `[draw]` if you don't need
   visualization and `svg` output generation.

2. **Running Knows**:
   ```shell
   knows [options]
   ```

### Docker Deployment 🐳

#### From Docker Hub

1. **Pull Image**:
   ```shell
   docker pull lszeremeta/knows
   ```

2. **Run Container**:
   ```shell
   docker run --rm lszeremeta/knows [options]
   ```

#### Building from Source

1. **Build Image**:
   ```shell
   docker build -t knows .
   ```

2. **Run Container**:
   ```shell
   docker run --rm knows [options]
   ```

### Python from Source

1. **Clone Repository**:
   ```shell
   git clone git@github.com:lszeremeta/knows.git
   cd knows
   ```

2. **Install Requirements**:
   ```shell
   pip install -r requirements.txt
   ```

3. **Execute Knows**:
   ```shell
   python -m knows [options]
   ```

## Usage 💡

### Basic Usage

```shell
knows [options]
```

To view all available options, use:

```shell
knows -h
```

### Options

- `-h`, `--help`: Display the help message and exit the program.
- `-n`, `--nodes`: Specify the number of nodes in the graph. Selected randomly if not provided.
- `-e`, `--edges`: Specify the number of edges in the graph. Selected randomly if not provided.
- `-f {graphml,yarspg,csv,gexf,gml,svg,adjacency_list,multiline_adjacency_list,edge_list,json}`,
  `--format {graphml,yarspg,gexf,gml,svg,adjacency_list,multiline_adjacency_list,edge_list,json}`:
  Choose the format to output the graph. Default: `graphml`.
- `-d`, `--draw`: Generate an image of the graph (default is no image). This option may not work in the Docker.
- `-np`, `--node-props`: Space-separated node properties to include. Available: firstName, lastName, favoriteColor,
  company, job, phoneNumber.
- `-ep`, `--edge-props`: Space-separated edge properties to include. Available: createDate, meetingCity, strength.
- `-a`, `--all-props`: Use all available node and edge properties.

You may also provide an optional path at the end of the command to save the output directly to a file. For the CSV
format, two
files will be created with suffixes `_nodes.csv` and `_edges.csv`.

### Practical Examples 🌟

1. Create a random graph in GraphML format and show it:
   ```shell
   knows
   ```
2. Create a 100-node, 70-edge graph in [YARS-PG format](https://github.com/lszeremeta/yarspg):
   ```shell
   knows -n 100 -e 70 -f yarspg > graph.yarspg
   # or
   knows -n 100 -e 70 -f yarspg graph.yarspg
   ```
3. Create a random graph in CSV format and save to files (nodes are written to standard output, edges to standard
   error):
   ```shell
   knows -f csv > nodes.csv 2> edges.csv
   # or
   knows -f csv graph.csv
   ```
   The latter command creates `graph_nodes.csv` and `graph_edges.csv`.
4. Create a 50-node, 20-edge graph in Cypher format:
   ```shell
   knows -n 50 -e 20 -f cypher > graph.cypher
   # or
   knows -n 50 -e 20 -f cypher graph.cypher
   ```
5. Create a 100-node, 50-edge graph in GraphML format:
   ```shell
   knows -n 100 -e 50 > graph.graphml
   # or
   knows -n 100 -e 50 graph.graphml
   ```
6. Create, save, and visualize a 100-node, 50-edge graph in SVG:
   ```shell
   knows -n 100 -e 50 -f svg -d > graph.svg
   # or
   knows -n 100 -e 50 -f svg -d graph.svg
   ```
7. Create, save a 100-node, 50-edge graph in SVG:
   ```shell
   knows -n 100 -e 50 -f svg > graph.svg
   # or
   knows -n 100 -e 50 -f svg graph.svg
   ```
8. Create a graph in JSON format:
   ```shell
   knows -f json > graph.json
   # or
   knows -f json graph.json
   ```
9. Create a graph with custom properties (20 nodes, 10 edges) and show it:
   ```shell
   knows -n 20 -e 10 --node-props firstName favoriteColor job --edge-props meetingCity
   ```
10. Create a graph with all possible properties in YARS-PG format and save it to file:
   ```shell
   knows -a -f yarspg > graph.yarspg
   # or
   knows -a -f yarspg > graph.yarspg
   ```

## Contribute to Knows 👥

Your ideas and contributions can make Knows even better! If you're new to open source,
read [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
and [CONTRIBUTING.md](https://github.com/lszeremeta/knows/blob/main/CONTRIBUTING.md).

## License 📜

Knows is licensed under the [MIT License](https://github.com/lszeremeta/knows/blob/main/LICENSE).