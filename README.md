# <img src="https://raw.githubusercontent.com/lszeremeta/knows/main/logo/knows-logo.png" alt="Knows logo" width="300">

[![PyPI](https://img.shields.io/pypi/v/knows)](https://pypi.org/project/knows/) [![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/lszeremeta/knows?label=Docker%20image%20size)](https://hub.docker.com/r/lszeremeta/knows)

Knows is a powerful and user-friendly tool for generating property graphs. These graphs are crucial in many fields.
Knows supports multiple output formats, schema files and basic visualization capabilities, making it a go-to tool for researchers, educators and data enthusiasts.

## Key Features 🚀

- **Customizable Graph Generation**: Tailor your graphs by specifying the number of nodes and edges.
- **Diverse Output Formats**: Export graphs in formats like
  GraphML, [YARS-PG 5.0](https://github.com/lszeremeta/yarspg), CSV, Cypher, GEXF, GML, JSON, and others.
- **Flexible Output Options**: Display results in the console, redirect them, or save them directly to a file.
- **Integrated Graph Visualization**: Conveniently visualize your graphs in SVG, PNG, JPG, or PDF format.
- **Intuitive Command-Line Interface (CLI)**: A user-friendly CLI for streamlined graph generation and visualization.
- **Docker Compatibility**: Deploy Knows in Docker containers for a consistent and isolated runtime environment.
- **Selectable Properties**: Choose which node and edge properties should be generated.
- **Custom Schema Support**: Define custom node/edge types and properties using GQL-inspired (ISO/IEC 39075) JSON schema
  files. Includes [JSON Schema](https://github.com/lszeremeta/knows/knows/schema.json) for validation. Schemas support many data types (String, Int, Float, Date,
  enums, and more), symmetric edge properties (for mutual relationships), computed node properties (like degree), and
  type constraints. See [SCHEMA.md](https://github.com/lszeremeta/knows/blob/main/SCHEMA.md) for full documentation.
- **Reproducible graphs**: Ensure deterministic outputs by setting the `-s`/`--seed` option regardless of the selected
  output format.

> **Note on reproducibility:** The `-s`/`--seed` option makes the random aspects of graph generation deterministic
> within the same software environment. Results may still differ across versions of Python or dependencies.

## Graph Structure

Build-in graph structure:

- Generates graphs with specified or random nodes and edges.
- Creates directed graphs.
- Nodes are labeled `Person` with unique IDs (`N1, N2, N3, ..., Nn`).
- Nodes feature `firstName` and `lastName` properties by default.
- Edges are labeled `knows` and include `strength` [1..100] and `lastMeetingDate` [1955-01-01..2025-06-28] properties by
  default.
- Additional node properties:
  - `favoriteColor`
  - `company`
  - `job`
  - `phoneNumber`
  - `postalAddress`
  - `friendCount` (actual node degree - number of unique connections)
  - `preferredContactMethod` [`inPerson`, `email`, `postalMail`, `phone`, `textMessage`, `videoCall`, `noPreference`]
- Additional edge properties:
  - `lastMeetingCity`
  - `meetingCount` [1..10000]
- Edges have random nodes, avoiding cycles.
- If edges connect the same nodes in both directions, the paired edges share `lastMeetingCity`, `lastMeetingDate`, and
  `meetingCount` values.

You can define custom graph structures using schema files. See [SCHEMA.md](https://github.com/lszeremeta/knows/blob/main/SCHEMA.md) for details and examples.

## Installation 🛠️

You can install knows via PyPI, Docker or run it from the source code.

### Install via PyPI

1. **Installation**:

   ```shell
   pip install knows[draw]
   ```

   The `draw` installs a `matplotlib` and `scipy` libraries for graph visualization. You can omit the `[draw]` if you
   don't need visualization and `svg` output generation.

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
   pip install .[draw]
   ```

3. **Execute Knows**:
   ```shell
   python -m knows [options]
   ```

### Install Tkinter for Graph Visualization

The `-d`/`--draw` option requires Tkinter.

- **Ubuntu**:

  ```shell
  sudo apt update
  sudo apt install python3-tk
  ```

  See [Installing Tkinter on Ubuntu](https://www.pythonguis.com/installation/install-tkinter-linux/) for details.

- **macOS (Homebrew)**:

  ```shell
  brew install python3
  brew install python-tk
  ```

  See [Installing Tkinter on macOS](https://www.pythonguis.com/installation/install-tkinter-mac/) for details.

- **Windows**:
  On Windows, Tkinter should be installed by default with Python. No additional steps required.

## Usage 💡

### Basic Usage

```shell
usage: knows [-h] [-n NODES] [-e EDGES] [-s SEED] [-v]
             [-f {yarspg,graphml,csv,cypher,gexf,gml,svg,png,jpg,pdf,adjacency_list,multiline_adjacency_list,edge_list,json}]
             [--schema FILE]
             [-np [{firstName,lastName,company,job,phoneNumber,favoriteColor,postalAddress,preferredContactMethod,friendCount} ...]]
             [-ep [{strength,lastMeetingCity,lastMeetingDate,meetingCount} ...]] [-ap] [-d] [-l N] [--no-limit] [--hide-info]
             [output]
```

> Available options may vary depending on the version. To display all available options with their descriptions use
> `knows -h`.

### Positional arguments

- `output`: Optional path to save the graph. For CSV format two files will be created: `*_nodes.csv` and `*_edges.csv`.

### Options

- `-h`, `--help`: Show help message and exit.
- `-n NODES`, `--nodes NODES`: Number of nodes in the graph. Selected randomly if not specified.
- `-e EDGES`, `--edges EDGES`: Number of edges in the graph. Selected randomly if not specified.
- `-s SEED`, `--seed SEED`: Seed for random number generation to ensure reproducible results (also between various
  output formats).
- `-v`, `--version`: Show program version and exit.
- `-f {yarspg,graphml,csv,cypher,gexf,gml,svg,png,jpg,pdf,adjacency_list,multiline_adjacency_list,edge_list,json}, --format {yarspg,graphml,csv,cypher,gexf,gml,svg,png,jpg,pdf,adjacency_list,multiline_adjacency_list,edge_list,json}`:
  Format to output the graph. Default: `yarspg`. The `svg`, `png`, `jpg` and `pdf` formats are for simple graph
  visualization.
- `--schema FILE`: Path to JSON schema file defining custom node/edge types and properties. When specified,
  overrides `-np`, `-ep`, and `-ap` options. GQL-inspired schema format ([ISO/IEC 39075](https://www.iso.org/standard/76120.html)).
  See [SCHEMA.md](https://github.com/lszeremeta/knows/blob/main/SCHEMA.md) for details.
- `-np [{firstName,lastName,company,job,phoneNumber,favoriteColor,postalAddress,friendCount,preferredContactMethod} ...], --node-props [{firstName,lastName,company,job,phoneNumber,favoriteColor,postalAddress,friendCount,preferredContactMethod} ...]`:  
  Space-separated node properties. Available: `firstName`, `lastName`, `company`, `job`, `phoneNumber`, `favoriteColor`,
  `postalAddress`, `preferredContactMethod` `friendCount`. Ignored when `--schema` is used.
- `-ep [{strength,lastMeetingCity,lastMeetingDate,meetingCount} ...]`,  
  `--edge-props [{strength,lastMeetingCity,lastMeetingDate,meetingCount} ...]`:  
  Space-separated edge properties. Available: `strength`, `lastMeetingCity`, `lastMeetingDate`, `meetingCount`. Ignored when `--schema` is used.
- `-ap`, `--all-props`: Use all available node and edge properties. Ignored when `--schema` is used.
- `-d`, `--draw`: Show interactive graph window. Requires Tkinter. May not work in Docker.

### Graphics output options (svg, png, jpg, pdf, -d)

- `-l N`, `--limit N`: Maximum nodes to display (default: 50). Shows subgraph centered on most connected nodes.
- `--no-limit`: Show full graph without node limit.
- `--hide-info`: Hide node count info (e.g., `50/200 nodes`) from output.

### Practical Examples 🌟

1. Create a random graph in [YARS-PG 5.0 format](https://github.com/lszeremeta/yarspg) and show it:
   ```shell
   knows
   # or
   docker run --rm lszeremeta/knows
   ```
2. Create a 100-node, 70-edge graph in GraphML format:
   ```shell
   knows -n 100 -e 70 -f graphml > graph.graphml
   # or
   knows -n 100 -e 70 -f graphml graph.graphml
   # or
   docker run --rm lszeremeta/knows -n 100 -e 70 -f graphml > graph.graphml
   # or
   docker run --rm -v "$(pwd)":/data lszeremeta/knows -n 100 -e 70 -f graphml /data/graph.graphml
   ```
3. Create a random graph in CSV format and save to files (nodes are written to standard output, edges to standard
   error):
   ```shell
   knows -f csv > nodes.csv 2> edges.csv
   # or
   knows -f csv graph.csv
   # or
   docker run --rm lszeremeta/knows -f csv > nodes.csv 2> edges.csv
   # or
   docker run --rm -v "$(pwd)":/data lszeremeta/knows -f csv /data/graph.csv
   ```
   The latter command creates `graph_nodes.csv` and `graph_edges.csv`.
4. Create a 50-node, 20-edge graph in Cypher format:
   ```shell
   knows -n 50 -e 20 -f cypher > graph.cypher
   # or
   knows -n 50 -e 20 -f cypher graph.cypher
   ```
5. Create a 100-node, 50-edge graph in YARS-PG format:
   ```shell
   knows -n 100 -e 50 > graph.yarspg
   # or
   knows -n 100 -e 50 graph.yarspg
   ```
6. Create, save, and visualize a 100-node, 50-edge graph in SVG:
   ```shell
   knows -n 100 -e 50 -f svg -d > graph.svg
   # or
   knows -n 100 -e 50 -f svg -d graph.svg
   ```
7. Create, save a 70-node, 50-edge graph in SVG:
   ```shell
   knows -n 70 -e 50 -f svg > graph.svg
   # or
   knows -n 70 -e 50 -f svg graph.svg
   ```
8. Create, save a 10-node, 5-edge graph in PNG:
   ```shell
   knows -n 10 -e 5 -f png > graph.png
   # or
   knows -n 10 -e 5 -f png graph.png
   ```
9. Create a graph in JSON format:
   ```shell
   knows -f json > graph.json
   # or
   knows -f json graph.json
   ```
10. Create a graph with custom properties (20 nodes, 10 edges) and show it:

```shell
knows -n 20 -e 10 -np firstName favoriteColor job -ep lastMeetingCity
```

11. Create a graph with all possible properties in YARS-PG format and save it to file:

```shell
knows -ap > graph.yarspg
# or
knows -ap graph.yarspg
```

12. Generate a reproducible graph in CSV by setting a seed:

```shell
knows -n 3 -e 2 -s 43 -f csv
```

Running the command again with the same seed will produce the identical graph, provided the environment and dependencies
remain unchanged.

13. Generate the same graph as above but in YARS-PG format:

```shell
knows -n 3 -e 2 -s 43
```

14. Generate a graph using a custom schema file:

```shell
knows -n 10 -e 15 -S schema-examples/employee_schema.json
# or
knows -n 10 -e 15 -S schema-examples/employee_schema.json -f cypher > employees.cypher
```

See [SCHEMA.md](https://github.com/lszeremeta/knows/blob/main/SCHEMA.md) for full schema documentation and more examples.

15. Visualize a large graph with custom node limit:

```shell
knows -n 500 -e 300 -f svg -l 100 > graph.svg
```

This limits the visualization to 100 nodes (default is 50), centered on the most connected nodes.

16. Visualize the full graph without node limit:

```shell
knows -n 200 -e 150 -f png --no-limit > graph.png
```

17. Create visualization without node count info:

```shell
knows -n 300 -e 200 -f svg --hide-info > graph.svg
```

## Contribute to Knows 👥

Your ideas and contributions can make Knows even better! If you're new to open source,
read [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
and [CONTRIBUTING.md](https://github.com/lszeremeta/knows/blob/main/CONTRIBUTING.md).

## License 📜

Knows is licensed under the [MIT License](https://github.com/lszeremeta/knows/blob/main/LICENSE).
