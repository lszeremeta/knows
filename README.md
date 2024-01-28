# <img src="https://raw.githubusercontent.com/lszeremeta/knows/main/logo/knows-logo.png" alt="Knows logo" width="300">

[![PyPI](https://img.shields.io/pypi/v/knows)](https://pypi.org/project/knows/) [![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/lszeremeta/knows?label=Docker%20image%20size)](https://hub.docker.com/r/lszeremeta/knows)

Knows is a user-friendly tool for benchmarking property graphs. These graphs are crucial in many fields. Knows supports
multiple output formats and visualization capabilities, making it a go-to tool for educators, researchers, and data
enthusiasts.

## Key Features 🚀

- **Customizable Graph Generation**: Tailor your graphs by specifying the number of nodes and edges.
- **Diverse Output Formats**: Export graphs in formats like GraphML, YARS-PG, GEXF, GML, SVG, JSON, and others.
- **Integrated Graph Visualization**: Conveniently visualize your graphs in SVG format.
- **Intuitive Command-Line Interface (CLI)**: A user-friendly CLI for streamlined graph generation and visualization.
- **Docker Compatibility**: Deploy Knows in Docker containers for a consistent and isolated runtime environment.

## Graph Structure

- Generates graphs with specified or random nodes and edges.
- Creates directed graphs.
- Nodes are labeled `Person` with unique IDs (`N1, N2, N3, ..., Nn`).
- Nodes feature `firstName` and `lastName` properties with randomly assigned names.
- Edges are labeled `knows` and include a `createDate` property with a random date.
- Edges have random nodes, avoiding cycles.

## Installation 🛠️

You can install knows via PyPI Docker or run it from the source code.

### Install via PyPI

1. **Installation**:
   ```shell
   pip install knows[draw]
   ```
   The `draw` installs a `matplotlib` library for graph visualization. You can omit the `[draw]` if you don't need visualization and `svg` output generation.

2. **Running Knows**:
   ```shell
   knows [nodes] [edges] [options]
   ```

### Docker Deployment 🐳

#### From Docker Hub

1. **Pull Image**:
   ```shell
   docker pull lszeremeta/knows
   ```

2. **Run Container**:
   ```shell
   docker run --rm lszeremeta/knows [nodes] [edges] [options]
   ```

#### Building from Source

1. **Build Image**:
   ```shell
   docker build -t knows .
   ```

2. **Run Container**:
   ```shell
   docker run --rm knows [nodes] [edges] [options]
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
   python -m knows [nodes] [edges] [options]
   ```

## Usage 💡

### Basic Usage

```shell
knows [nodes] [edges] [options]
```

To view all available options, use:

```shell
knows -h
```

### Positional Arguments

1. `nodes`: Specify the number of nodes in the graph. Selected randomly if not specified.
2. `edges`: Specify the number of edges in the graph. Selected randomly if not specified.

### Options

- `-h`, `--help`: Display the help message and exit the program.
- `-f {graphml,yarspg,gexf,gml,svg,adjacency_list,multiline_adjacency_list,edge_list,json}`, `--format {graphml,yarspg,gexf,gml,svg,adjacency_list,multiline_adjacency_list,edge_list,json}`:
  Choose the format to output the graph. Default: `graphml`.
- `-d`, `--draw`: Generate an image of the graph (default is no image). This option may not work in the Docker.

### Practical Examples 🌟

1. Create a random graph in GraphML format:
   ```shell
   knows
   ```
2. Create a 100-node, 70-edge graph in [YARS-PG format](https://github.com/lszeremeta/yarspg):
   ```shell
   knows 100 70 -f yarspg > graph.yarspg
   ```
3. Create a 100-node, 50-edge graph in GraphML format:
   ```shell
    knows 100 50 > graph.graphml
    ```
4. Create, save, and visualize a 100-node, 50-edge graph in SVG:
   ```shell
   knows 100 50 -f svg -d > graph.svg
   ```
5. Create, save a 100-node, 50-edge graph in SVG with a custom filename:
   ```shell
    knows 100 50 -f svg > graph.svg
    ```
6. Create a graph in JSON format:
   ```shell
   knows -f json > graph.json
   ```

## Contribute to Knows 👥

Your ideas and contributions can make Knows even better! If you're new to open source,
read [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
and [CONTRIBUTING.md](https://github.com/lszeremeta/knows/blob/main/CONTRIBUTING.md).

## License 📜

Knows is licensed under the [MIT License](https://github.com/lszeremeta/knows/blob/main/LICENSE).