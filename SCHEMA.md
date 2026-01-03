# Schema Support in Knows

Knows supports custom graph schemas via JSON files, allowing you to define your own node and edge types with custom
properties. GQL-inspired schema format (ISO/IEC 39075).

A [JSON Schema](https://github.com/lszeremeta/knows/knows/schema.json) is provided for validation and IDE autocompletion. To enable it, add `"$schema"` to your
schema file:

```json
{
    "$schema": "https://raw.githubusercontent.com/lszeremeta/knows/main/knows/schema.json",
    "nodeLabel": "MyNode",
    ...
}
```

### Validating Your Schema

**IDE Validation (recommended)**

Most modern IDEs validate JSON Schema automatically when `$schema` is present:
- **VS Code**: Built-in support, shows errors inline
- **JetBrains IDEs**: Built-in support (PyCharm, IntelliJ, WebStorm)
- **Sublime Text**: Use LSP or SublimeLinter-json plugin

**Online Validators**

- [JSON Schema Validator](https://www.jsonschemavalidator.net/) - Paste schema and data, get instant results
- [JSON Schema Lint](https://jsonschemalint.com/) - Real-time validation with detailed error messages
- [Hyperjump JSON Schema Validator](https://json-schema.hyperjump.io/) - Supports Draft 2020-12

**Command Line**

Using [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) (Python):

```shell
pip install check-jsonschema
check-jsonschema --schemafile schema.json my_schema.json
```

Using [ajv-cli](https://github.com/ajv-validator/ajv-cli) (Node.js):

```shell
npm install -g ajv-cli
ajv validate -s schema.json -d my_schema.json
```

**Python**

```python
import json
from jsonschema import validate, ValidationError

with open('schema.json') as f:
    json_schema = json.load(f)

with open('my_schema.json') as f:
    my_schema = json.load(f)

try:
    validate(instance=my_schema, schema=json_schema)
    print("Schema is valid!")
except ValidationError as e:
    print(f"Validation error: {e.message}")
```

## Quick Start

Create a schema file (e.g., `my_schema.json`):

```json
{
    "nodeLabel": "Product",
    "edgeLabel": "relatedTo",
    "nodeProperties": {
        "name": "String",
        "price": {"type": "Float", "min": 0.99, "max": 999.99},
        "category": {"enum": ["Electronics", "Clothing", "Food"]}
    },
    "edgeProperties": {
        "similarity": {"type": "Float", "min": 0.0, "max": 1.0}
    }
}
```

Then generate a graph:

```shell
knows -n 20 -e 30 -S my_schema.json
```

## Schema Structure

A schema file is a JSON object with the following optional fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `nodeLabel` | string | `"Node"` | Label for all generated nodes |
| `edgeLabel` | string | `"edge"` | Label for all generated edges |
| `nodeProperties` | object | `{}` | Property definitions for nodes |
| `edgeProperties` | object | `{}` | Property definitions for edges (supports `symmetric`) |
| `computedNodeProperties` | object | `{}` | Properties computed from graph structure |

## Property Types

Properties can be defined in two ways:

### Simple Type (string)

```json
{
    "nodeProperties": {
        "name": "String",
        "age": "Int",
        "active": "Boolean"
    }
}
```

### Complex Type (object with constraints)

```json
{
    "nodeProperties": {
        "salary": {"type": "Int", "min": 30000, "max": 200000},
        "rating": {"type": "Float", "min": 0.0, "max": 5.0, "precision": 1},
        "status": {"enum": ["active", "inactive", "pending"]}
    }
}
```

## Available Types

### String Types

| Type | Description | Example Output |
|------|-------------|----------------|
| `String` | Random word | `"lorem"` |
| `Name` | Full name | `"John Smith"` |
| `FirstName` | First name | `"John"` |
| `LastName` | Last name | `"Smith"` |
| `FullName` | Full name (alias for Name) | `"Jane Doe"` |
| `Email` | Email address | `"john@example.com"` |
| `Phone` | Phone number | `"+1-555-123-4567"` |
| `Address` | Full address | `"123 Main St, City"` |
| `City` | City name | `"New York"` |
| `Country` | Country name | `"United States"` |
| `Company` | Company name | `"Acme Inc"` |
| `Job` | Job title | `"Software Engineer"` |
| `Text` | Paragraph of text | Long text (configurable via `maxLength`) |
| `Sentence` | Single sentence | `"Lorem ipsum dolor sit."` |
| `Paragraph` | Full paragraph | Multiple sentences |
| `Url` | URL | `"https://example.com"` |
| `Color` | Color name | `"blue"` |
| `Uuid` | UUID string | `"550e8400-e29b-41d4-a716-446655440000"` |

### Numeric Types

| Type | Description | Constraints |
|------|-------------|-------------|
| `Int` / `Integer` | Integer number | `min`, `max` (default: 0-10000) |
| `Float` | Floating-point number | `min`, `max`, `precision` (default: 0.0-1000.0, precision 2) |
| `Double` | Double-precision float | `min`, `max`, `precision` (default: 0.0-1000.0, precision 4) |
| `Boolean` / `Bool` | Boolean value | - |

### Date/Time Types

| Type | Description | Constraints |
|------|-------------|-------------|
| `Date` | ISO date string | `min`, `max` (default: 1970-01-01 to 2025-12-31) |
| `DateTime` | ISO datetime string | `min`, `max` (default: -30 years to now) |
| `Time` | Time string | - |
| `Year` | Year number | `min`, `max` (default: 1950-2025) |

### Enum Type

Define a fixed set of possible values:

```json
{
    "status": {"enum": ["pending", "approved", "rejected"]}
}
```

## Type Constraints

### For Numeric Types (`Int`, `Float`, `Double`)

- `min`: Minimum value (inclusive)
- `max`: Maximum value (inclusive)
- `precision`: Decimal places (for `Float` and `Double`)

```json
{
    "price": {"type": "Float", "min": 0.01, "max": 9999.99, "precision": 2}
}
```

### For Date Types

- `min`: Start date in ISO format (`YYYY-MM-DD`)
- `max`: End date in ISO format (`YYYY-MM-DD`)

```json
{
    "foundedDate": {"type": "Date", "min": "1900-01-01", "max": "2025-12-31"}
}
```

### For Text Type

- `maxLength`: Maximum number of characters

```json
{
    "description": {"type": "Text", "maxLength": 500}
}
```

## Type Aliases

GQL-style uppercase type names are supported as aliases:

| Alias | Maps To |
|-------|---------|
| `STRING` | `String` |
| `INTEGER` | `Int` |
| `INT64` | `Int` |
| `UINT64` | `Int` |
| `FLOAT64` | `Float` |
| `BOOLEAN` | `Boolean` |
| `BOOL` | `Bool` |
| `DATE` | `Date` |
| `DATETIME` | `DateTime` |
| `ZONED DATETIME` | `DateTime` |

## Symmetric Edge Properties

Edge properties can be marked as `symmetric` to ensure edges in both directions (A→B and B→A) share the same value:

```json
{
    "edgeProperties": {
        "meetingDate": {"type": "Date", "symmetric": true},
        "sharedProject": {"enum": ["Alpha", "Beta", "Gamma"], "symmetric": true}
    }
}
```

When an edge A→B is created and a reverse edge B→A already exists, symmetric properties are copied from the existing
edge. This is useful for mutual relationships where both directions should have consistent values.

## Computed Node Properties

Properties that are calculated from the graph structure after generation:

```json
{
    "computedNodeProperties": {
        "connectionCount": "degree"
    }
}
```

| Type | Description |
|------|-------------|
| `degree` | Total unique connections (undirected degree - counts both incoming and outgoing edges) |

Computed properties are added to nodes after all edges are generated, ensuring accurate values based on the final graph
topology.

## Example Schemas

Ready-to-use example schemas are available in the [`schema-examples/`](https://github.com/lszeremeta/knows/blob/main/schema-examples/) directory:

### Simple (2-3 properties each)

| File | Description |
|------|-------------|
| [`simple_friendship_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/simple_friendship_schema.json) | Person/friendOf - name, age |
| [`simple_task_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/simple_task_schema.json) | Task/dependsOn - title, status |
| [`simple_webpage_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/simple_webpage_schema.json) | Page/linksTo - url, title |
| [`simple_message_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/simple_message_schema.json) | User/messaged - username, email |

### Real-world

| File | Description |
|------|-------------|
| [`default_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/default_schema.json) | Default Knows graph (Person/knows) |
| [`social_network_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/social_network_schema.json) | Social media users and followers |
| [`employee_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/employee_schema.json) | Employee collaboration network |
| [`ecommerce_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/ecommerce_schema.json) | E-commerce product relationships |
| [`knowledge_graph_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/knowledge_graph_schema.json) | Knowledge graph with concepts |
| [`citation_network_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/citation_network_schema.json) | Academic paper citations |
| [`transportation_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/transportation_schema.json) | Transit stations and routes |
| [`financial_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/financial_schema.json) | Bank accounts and transactions |
| [`infrastructure_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/infrastructure_schema.json) | IT services and dependencies |
| [`movie_database_schema.json`](https://github.com/lszeremeta/knows/blob/main/schema-examples/movie_database_schema.json) | Actor co-starring relationships |

Use them directly or as templates for your own schemas:

```shell
knows -n 50 -e 100 -S schema-examples/social_network_schema.json
```

## Usage Examples

### Generate graph with custom schema

```shell
knows -S my_schema.json
```

### Specify node and edge count

```shell
knows -n 100 -e 200 -S my_schema.json
```

### Export to different formats

```shell
# GraphML
knows -n 50 -e 75 -S my_schema.json -f graphml > graph.graphml

# Cypher (for Neo4j)
knows -n 50 -e 75 -S my_schema.json -f cypher > graph.cypher

# CSV
knows -n 50 -e 75 -S my_schema.json -f csv graph.csv

# JSON
knows -n 50 -e 75 -S my_schema.json -f json > graph.json
```

### With reproducible seed

```shell
knows -n 20 -e 30 -S my_schema.json -s 42
```

### Using Docker

```shell
docker run --rm -v "$(pwd)":/data lszeremeta/knows -S /data/my_schema.json -n 50 -e 75
```

## Notes

- When using `-S`/`--schema`, the `-np`, `-ep`, and `-ap` options are ignored
- Schema files must be valid JSON with `.json` extension
- All property definitions are validated before graph generation
- Invalid schemas will produce clear error messages
- The schema format is inspired by GQL (ISO/IEC 39075) but is not a full GQL implementation
