"""Tests for GQL-inspired schema support."""

import json
import pytest

from knows.schema import (
    load_schema,
    schema_to_generators,
    get_schema_properties,
    get_symmetric_edge_properties,
    get_computed_node_properties,
    SchemaError,
    TYPE_GENERATORS,
    TYPE_ALIASES,
    COMPUTED_PROPERTY_TYPES,
)
from knows.graph import Graph


# --- Fixtures ---

@pytest.fixture
def simple_schema():
    """A simple valid schema."""
    return {
        "nodeLabel": "Employee",
        "edgeLabel": "collaborates",
        "nodeProperties": {
            "name": "String",
            "age": "Int"
        },
        "edgeProperties": {
            "since": "Date"
        }
    }


@pytest.fixture
def complex_schema():
    """A more complex schema with various types and constraints."""
    return {
        "nodeLabel": "Product",
        "edgeLabel": "relatedTo",
        "nodeProperties": {
            "name": "String",
            "price": {"type": "Float", "min": 0.01, "max": 9999.99},
            "category": {"enum": ["Electronics", "Clothing", "Food", "Books"]},
            "inStock": "Boolean",
            "manufacturedDate": "Date",
            "rating": {"type": "Int", "min": 1, "max": 5}
        },
        "edgeProperties": {
            "similarity": {"type": "Float", "min": 0.0, "max": 1.0},
            "relationshipType": {"enum": ["similar", "complement", "substitute"]}
        }
    }


@pytest.fixture
def symmetric_schema():
    """Schema with symmetric edge properties."""
    return {
        "nodeLabel": "Person",
        "edgeLabel": "knows",
        "nodeProperties": {
            "name": "Name"
        },
        "edgeProperties": {
            "strength": {"type": "Int", "min": 1, "max": 100},
            "meetingCity": {"type": "City", "symmetric": True},
            "meetingDate": {"type": "Date", "symmetric": True}
        }
    }


@pytest.fixture
def computed_schema():
    """Schema with computed node properties."""
    return {
        "nodeLabel": "User",
        "edgeLabel": "follows",
        "nodeProperties": {
            "username": "String"
        },
        "edgeProperties": {
            "followedAt": "Date"
        },
        "computedNodeProperties": {
            "connectionCount": "degree"
        }
    }


@pytest.fixture
def schema_file(tmp_path, simple_schema):
    """Create a temporary schema file."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(simple_schema))
    return schema_path


# --- Schema Loading Tests ---

def test_load_schema_valid_file(schema_file):
    """Test loading a valid schema file."""
    schema = load_schema(schema_file)
    assert schema['nodeLabel'] == 'Employee'
    assert schema['edgeLabel'] == 'collaborates'


def test_load_schema_file_not_found():
    """Test error when schema file doesn't exist."""
    with pytest.raises(SchemaError, match="Schema file not found"):
        load_schema("/nonexistent/path/schema.json")


def test_load_schema_invalid_extension(tmp_path):
    """Test error when file has wrong extension."""
    invalid_file = tmp_path / "schema.txt"
    invalid_file.write_text("{}")
    with pytest.raises(SchemaError, match="must be JSON format"):
        load_schema(invalid_file)


def test_load_schema_invalid_json(tmp_path):
    """Test error when file contains invalid JSON."""
    invalid_file = tmp_path / "schema.json"
    invalid_file.write_text("{ invalid json }")
    with pytest.raises(SchemaError, match="Invalid JSON"):
        load_schema(invalid_file)


def test_load_schema_not_object(tmp_path):
    """Test error when schema is not a JSON object."""
    invalid_file = tmp_path / "schema.json"
    invalid_file.write_text('["array", "not", "object"]')
    with pytest.raises(SchemaError, match="must be a JSON object"):
        load_schema(invalid_file)


# --- Schema Validation Tests ---

def test_validate_empty_node_label(tmp_path):
    """Test error when nodeLabel is empty."""
    invalid_schema = {"nodeLabel": ""}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(invalid_schema))
    with pytest.raises(SchemaError, match="nodeLabel cannot be empty"):
        load_schema(schema_path)


def test_validate_invalid_node_label_type(tmp_path):
    """Test error when nodeLabel is not a string."""
    invalid_schema = {"nodeLabel": 123}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(invalid_schema))
    with pytest.raises(SchemaError, match="nodeLabel must be a string"):
        load_schema(schema_path)


def test_validate_unknown_property_type(tmp_path):
    """Test error when property type is unknown."""
    invalid_schema = {
        "nodeProperties": {
            "field": "UnknownType"
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(invalid_schema))
    with pytest.raises(SchemaError, match="Unknown type 'UnknownType'"):
        load_schema(schema_path)


def test_validate_missing_type_and_enum(tmp_path):
    """Test error when property has neither type nor enum."""
    invalid_schema = {
        "nodeProperties": {
            "field": {"min": 0, "max": 100}
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(invalid_schema))
    with pytest.raises(SchemaError, match="must have 'type' or 'enum' field"):
        load_schema(schema_path)


def test_validate_empty_enum(tmp_path):
    """Test error when enum is empty."""
    invalid_schema = {
        "nodeProperties": {
            "field": {"enum": []}
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(invalid_schema))
    with pytest.raises(SchemaError, match="enum must be a non-empty array"):
        load_schema(schema_path)


# --- Generator Creation Tests ---

def test_schema_to_generators_simple(simple_schema):
    """Test converting simple schema to generators."""
    node_gens, edge_gens, node_label, edge_label = schema_to_generators(simple_schema)
    
    assert node_label == 'Employee'
    assert edge_label == 'collaborates'
    assert 'name' in node_gens
    assert 'age' in node_gens
    assert 'since' in edge_gens


def test_schema_to_generators_complex(complex_schema):
    """Test converting complex schema to generators."""
    node_gens, edge_gens, node_label, edge_label = schema_to_generators(complex_schema)
    
    assert node_label == 'Product'
    assert edge_label == 'relatedTo'
    assert len(node_gens) == 6
    assert len(edge_gens) == 2


def test_schema_to_generators_defaults():
    """Test default labels when not specified."""
    schema = {"nodeProperties": {"x": "Int"}}
    _, _, node_label, edge_label = schema_to_generators(schema)
    
    assert node_label == 'Node'
    assert edge_label == 'edge'


def test_get_schema_properties(complex_schema):
    """Test extracting property names from schema."""
    node_props, edge_props = get_schema_properties(complex_schema)
    
    assert set(node_props) == {'name', 'price', 'category', 'inStock', 'manufacturedDate', 'rating'}
    assert set(edge_props) == {'similarity', 'relationshipType'}


# --- Type Generator Tests ---

def test_type_generators_exist():
    """Test that all documented types have generators."""
    expected_types = [
        'String', 'Name', 'FirstName', 'LastName', 'Email', 'Phone',
        'Address', 'City', 'Country', 'Company', 'Job',
        'Int', 'Integer', 'Float', 'Double', 'Boolean', 'Bool',
        'Date', 'DateTime', 'Time', 'Year', 'Duration'
    ]
    for t in expected_types:
        assert t in TYPE_GENERATORS, f"Missing type generator: {t}"


def test_enum_generator():
    """Test enum value generation."""
    from faker import Faker
    from knows.schema import _create_generator
    
    gen = _create_generator({"enum": ["A", "B", "C"]})
    faker = Faker()
    faker.seed_instance(42)
    
    values = [gen(faker) for _ in range(100)]
    assert all(v in ["A", "B", "C"] for v in values)
    # Should have some variety
    assert len(set(values)) > 1


def test_int_generator_with_constraints():
    """Test Int generator respects min/max constraints."""
    from faker import Faker
    from knows.schema import _create_generator
    
    gen = _create_generator({"type": "Int", "min": 10, "max": 20})
    faker = Faker()
    faker.seed_instance(42)
    
    values = [gen(faker) for _ in range(100)]
    assert all(10 <= v <= 20 for v in values)


def test_float_generator_with_constraints():
    """Test Float generator respects min/max constraints."""
    from faker import Faker
    from knows.schema import _create_generator
    
    gen = _create_generator({"type": "Float", "min": 0.0, "max": 1.0})
    faker = Faker()
    faker.seed_instance(42)
    
    values = [gen(faker) for _ in range(100)]
    assert all(0.0 <= v <= 1.0 for v in values)


# --- Duration Type Tests ---

@pytest.mark.parametrize("iso", [
    "PT0S",
    "P1Y",
    "P1M",
    "P7D",
    "PT30M",
    "P1Y2M10DT2H30M",
    "P1M15DT6H30M",
])
def test_duration_seconds_roundtrip(iso):
    """ISO 8601 durations survive a seconds round-trip unchanged."""
    from knows.schema import _duration_to_seconds, _seconds_to_duration

    seconds = _duration_to_seconds(iso)
    assert _seconds_to_duration(seconds) == iso


def test_duration_zero_renders_pt0s():
    """A zero-second duration renders as PT0S."""
    from knows.schema import _seconds_to_duration

    assert _seconds_to_duration(0) == "PT0S"


@pytest.mark.parametrize("bad", ["", "P", "1Y", "PT", "P1H", "garbage"])
def test_duration_invalid_raises(bad):
    """Invalid ISO 8601 duration strings raise SchemaError."""
    from knows.schema import _duration_to_seconds, SchemaError

    with pytest.raises(SchemaError):
        _duration_to_seconds(bad)


def test_duration_generator_default_range():
    """Duration generator stays within the default PT0S..P1Y range."""
    from faker import Faker
    from knows.schema import _create_generator, _duration_to_seconds

    gen = _create_generator("Duration")
    faker = Faker()
    faker.seed_instance(42)

    upper = _duration_to_seconds("P1Y")
    values = [gen(faker) for _ in range(100)]
    for v in values:
        assert 0 <= _duration_to_seconds(v) <= upper


def test_duration_generator_with_constraints():
    """Duration generator respects explicit min/max constraints."""
    from faker import Faker
    from knows.schema import _create_generator, _duration_to_seconds

    gen = _create_generator({"type": "Duration", "min": "PT1H", "max": "P5D"})
    faker = Faker()
    faker.seed_instance(42)

    lower = _duration_to_seconds("PT1H")
    upper = _duration_to_seconds("P5D")
    values = [gen(faker) for _ in range(100)]
    for v in values:
        assert lower <= _duration_to_seconds(v) <= upper


def test_duration_uppercase_alias_resolves():
    """The DURATION alias resolves to the Duration generator."""
    from faker import Faker
    from knows.schema import _create_generator, _duration_to_seconds

    gen = _create_generator({"type": "DURATION", "min": "P1M", "max": "P6M"})
    faker = Faker()
    faker.seed_instance(42)

    value = gen(faker)
    lower = _duration_to_seconds("P1M")
    upper = _duration_to_seconds("P6M")
    assert lower <= _duration_to_seconds(value) <= upper


def test_duration_weeks_parse_but_render_as_days():
    """Weeks are accepted in bounds but rendered as days (P2W -> P14D)."""
    from knows.schema import _duration_to_seconds, _seconds_to_duration

    seconds = _duration_to_seconds("P2W")
    assert seconds == 14 * 24 * 3600
    assert _seconds_to_duration(seconds) == "P14D"


def test_duration_min_greater_than_max_raises():
    """A min bound above the max bound fails at generator creation."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="uptime"):
        _create_generator(
            {"type": "Duration", "min": "P2Y", "max": "P1Y"}, "uptime"
        )


def test_duration_non_string_bound_raises():
    """A non-string Duration bound fails at generator creation."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="uptime"):
        _create_generator({"type": "Duration", "min": 100}, "uptime")


def test_duration_invalid_bound_raises_at_creation():
    """An unparseable Duration bound fails at generator creation, not use."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="uptime"):
        _create_generator({"type": "Duration", "min": "banana"}, "uptime")


def test_date_min_later_than_max_raises():
    """A Date min bound after the max bound fails at generator creation."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="hired"):
        _create_generator(
            {"type": "Date", "min": "2025-01-01", "max": "2020-01-01"}, "hired"
        )


def test_date_invalid_bound_raises_at_creation():
    """A non-ISO Date bound fails at generator creation, not use."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="hired"):
        _create_generator({"type": "Date", "min": 100}, "hired")


@pytest.mark.parametrize("props,message", [
    ({"uptime": {"type": "Duration", "min": "banana"}}, "ISO 8601 duration"),
    ({"uptime": {"type": "Duration", "min": 100}}, "must be a string"),
    ({"hired": {"type": "Date", "min": 100}}, "must be a string"),
    ({"hired": {"type": "Date", "min": "01-01-2020"}}, "ISO date"),
    ({"age": {"type": "Int", "min": "ten"}}, "must be a number"),
    ({"desc": {"type": "Text", "maxLength": 3}}, "at least 5"),
])
def test_load_schema_rejects_bad_bounds(tmp_path, props, message):
    """Type-incompatible min/max bounds are rejected when loading a schema."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps({"nodeProperties": props}))

    with pytest.raises(SchemaError, match=message):
        load_schema(schema_path)


# --- Numeric and DateTime Bound Tests ---

@pytest.mark.parametrize("definition", [
    {"type": "Int", "min": 20, "max": 10},
    {"type": "Int", "min": 20000},
    {"type": "Year", "min": 2030, "max": 2020},
    {"type": "Float", "min": 5.0, "max": 1.0},
])
def test_numeric_min_greater_than_max_raises(definition):
    """Reversed numeric bounds fail at generator creation."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="prop"):
        _create_generator(definition, "prop")


def test_float_equal_bounds_raise():
    """Equal Float bounds fail at creation (Faker requires min < max)."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="score"):
        _create_generator({"type": "Float", "min": 1.0, "max": 1.0}, "score")


def test_int_equal_bounds_allowed():
    """Equal Int bounds are valid and produce the constant value."""
    from faker import Faker
    from knows.schema import _create_generator

    gen = _create_generator({"type": "Int", "min": 5, "max": 5}, "rating")
    faker = Faker()
    faker.seed_instance(42)
    assert gen(faker) == 5


def test_numeric_non_number_bound_raises():
    """A non-numeric bound on a numeric type fails at generator creation."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="age"):
        _create_generator({"type": "Int", "min": "ten"}, "age")


def test_datetime_invalid_bound_raises_at_creation():
    """An unparseable DateTime bound fails at generator creation, not use."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="ts"):
        _create_generator({"type": "DateTime", "min": "banana"}, "ts")


def test_datetime_faker_style_bounds_accepted():
    """Faker-style DateTime bounds like '-30y' and 'now' keep working."""
    from faker import Faker
    from knows.schema import _create_generator

    gen = _create_generator({"type": "DateTime", "min": "-1y", "max": "now"}, "ts")
    faker = Faker()
    faker.seed_instance(42)
    assert isinstance(gen(faker), str)


def test_invalid_definition_type_raises():
    """A definition that is neither string nor dict fails loudly."""
    from knows.schema import _create_generator, SchemaError

    with pytest.raises(SchemaError, match="prop"):
        _create_generator(123, "prop")


@pytest.mark.parametrize("definition", [
    {"type": "Name", "symmetric": True},
    {"enum": ["a", "b"], "symmetric": True},
])
def test_symmetric_rejected_on_node_properties(tmp_path, definition):
    """'symmetric' is only valid on edge properties, not node properties."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps({"nodeProperties": {"name": definition}}))

    with pytest.raises(SchemaError, match="edge properties"):
        load_schema(schema_path)


# --- Graph Integration Tests ---

def test_graph_with_schema(tmp_path, simple_schema):
    """Test graph generation with schema."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(simple_schema))
    
    schema = load_schema(schema_path)
    graph = Graph(5, 4, schema=schema, seed=42)
    graph.generate()
    
    # Check nodes
    assert len(graph.graph.nodes) == 5
    for _, props in graph.graph.nodes(data=True):
        assert props['label'] == 'Employee'
        assert 'name' in props
        assert 'age' in props
        assert isinstance(props['age'], int)
    
    # Check edges
    assert len(graph.graph.edges) == 4
    for _, _, props in graph.graph.edges(data=True):
        assert props['label'] == 'collaborates'
        assert 'since' in props


def test_graph_with_complex_schema(tmp_path, complex_schema):
    """Test graph generation with complex schema."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(complex_schema))
    
    schema = load_schema(schema_path)
    graph = Graph(10, 15, schema=schema, seed=123)
    graph.generate()
    
    for _, props in graph.graph.nodes(data=True):
        assert props['label'] == 'Product'
        assert props['category'] in ["Electronics", "Clothing", "Food", "Books"]
        assert 0.01 <= props['price'] <= 9999.99
        assert 1 <= props['rating'] <= 5
        assert isinstance(props['inStock'], bool)
    
    for _, _, props in graph.graph.edges(data=True):
        assert props['label'] == 'relatedTo'
        assert props['relationshipType'] in ["similar", "complement", "substitute"]
        assert 0.0 <= props['similarity'] <= 1.0


def test_graph_schema_overrides_props(tmp_path, simple_schema):
    """Test that schema overrides -np/-ep options."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(simple_schema))
    
    schema = load_schema(schema_path)
    # These should be ignored when schema is provided
    graph = Graph(
        3, 2,
        node_props=['firstName', 'lastName'],  # Should be ignored
        edge_props=['strength'],  # Should be ignored
        schema=schema
    )
    graph.generate()
    
    for _, props in graph.graph.nodes(data=True):
        # Schema properties, not default ones
        assert 'name' in props
        assert 'age' in props
        assert 'firstName' not in props
        assert 'lastName' not in props


def test_graph_reproducibility_with_schema(tmp_path, simple_schema):
    """Test that schema-based graphs are reproducible with seed."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(simple_schema))
    
    schema = load_schema(schema_path)
    
    graph1 = Graph(5, 4, schema=schema, seed=42)
    graph1.generate()
    
    graph2 = Graph(5, 4, schema=schema, seed=42)
    graph2.generate()
    
    nodes1 = list(graph1.graph.nodes(data=True))
    nodes2 = list(graph2.graph.nodes(data=True))
    assert nodes1 == nodes2


# --- Type Alias Tests ---

def test_type_aliases_uppercase():
    """Test that uppercase type aliases work."""
    from knows.schema import TYPE_ALIASES
    
    assert TYPE_ALIASES.get('STRING') == 'String'
    assert TYPE_ALIASES.get('INTEGER') == 'Int'
    assert TYPE_ALIASES.get('BOOLEAN') == 'Boolean'
    assert TYPE_ALIASES.get('DATE') == 'Date'
    assert TYPE_ALIASES.get('DURATION') == 'Duration'


def test_type_aliases_in_schema(tmp_path):
    """Test uppercase types in schema."""
    schema = {
        "nodeProperties": {
            "id": "INTEGER",
            "name": "STRING",
            "active": "BOOLEAN"
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    
    loaded = load_schema(schema_path)
    node_gens, _, _, _ = schema_to_generators(loaded)
    
    assert 'id' in node_gens
    assert 'name' in node_gens
    assert 'active' in node_gens


# --- Edge Cases ---

def test_empty_schema(tmp_path):
    """Test schema with no properties defined."""
    schema = {}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    
    loaded = load_schema(schema_path)
    node_gens, edge_gens, node_label, edge_label = schema_to_generators(loaded)
    
    assert len(node_gens) == 0
    assert len(edge_gens) == 0
    assert node_label == 'Node'
    assert edge_label == 'edge'


def test_schema_only_labels(tmp_path):
    """Test schema with only labels, no properties."""
    schema = {
        "nodeLabel": "CustomNode",
        "edgeLabel": "customEdge"
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    loaded = load_schema(schema_path)
    graph = Graph(3, 2, schema=loaded)
    graph.generate()

    for _, props in graph.graph.nodes(data=True):
        assert props['label'] == 'CustomNode'
        # Only label, no other properties
        assert len(props) == 1

    for _, _, props in graph.graph.edges(data=True):
        assert props['label'] == 'customEdge'
        assert len(props) == 1


# --- Symmetric Edge Properties Tests ---

def test_get_symmetric_edge_properties(symmetric_schema):
    """Test extracting symmetric edge properties from schema."""
    symmetric_props = get_symmetric_edge_properties(symmetric_schema)

    assert isinstance(symmetric_props, frozenset)
    assert 'meetingCity' in symmetric_props
    assert 'meetingDate' in symmetric_props
    assert 'strength' not in symmetric_props  # Not marked as symmetric


def test_get_symmetric_edge_properties_empty():
    """Test symmetric properties extraction with no symmetric props."""
    schema = {
        "edgeProperties": {
            "weight": {"type": "Int", "min": 1, "max": 100}
        }
    }
    symmetric_props = get_symmetric_edge_properties(schema)
    assert len(symmetric_props) == 0


def test_get_symmetric_edge_properties_simple_types():
    """Test that simple type strings are not symmetric."""
    schema = {
        "edgeProperties": {
            "date": "Date",
            "city": "City"
        }
    }
    symmetric_props = get_symmetric_edge_properties(schema)
    assert len(symmetric_props) == 0


def test_symmetric_edge_properties_in_graph(tmp_path, symmetric_schema):
    """Test that symmetric edge properties share values in both directions."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(symmetric_schema))

    schema = load_schema(schema_path)
    # Create graph with enough edges to likely get bidirectional pairs
    graph = Graph(5, 15, schema=schema, seed=42)
    graph.generate()

    # Find bidirectional edges and check symmetric properties
    edges = list(graph.graph.edges(data=True))
    for u, v, props in edges:
        if graph.graph.has_edge(v, u):
            reverse_props = graph.graph[v][u]
            # Symmetric properties should match
            assert props['meetingCity'] == reverse_props['meetingCity']
            assert props['meetingDate'] == reverse_props['meetingDate']
            # Non-symmetric properties can differ
            # (strength is not symmetric, so it may differ)


def test_symmetric_with_enum(tmp_path):
    """Test symmetric property with enum type."""
    schema = {
        "nodeLabel": "Person",
        "edgeLabel": "met",
        "nodeProperties": {"name": "Name"},
        "edgeProperties": {
            "location": {"enum": ["office", "cafe", "online"], "symmetric": True}
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    loaded = load_schema(schema_path)
    symmetric_props = get_symmetric_edge_properties(loaded)
    assert 'location' in symmetric_props


# --- Computed Node Properties Tests ---

def test_get_computed_node_properties(computed_schema):
    """Test extracting computed node properties from schema."""
    computed_props = get_computed_node_properties(computed_schema)

    assert isinstance(computed_props, dict)
    assert 'connectionCount' in computed_props
    assert computed_props['connectionCount'] == 'degree'


def test_get_computed_node_properties_empty():
    """Test computed properties extraction with no computed props."""
    schema = {"nodeProperties": {"name": "Name"}}
    computed_props = get_computed_node_properties(schema)
    assert len(computed_props) == 0


def test_computed_property_types_exist():
    """Test that degree is a valid computed property type."""
    assert 'degree' in COMPUTED_PROPERTY_TYPES


def test_validate_invalid_computed_property_type(tmp_path):
    """Test error when computed property type is invalid."""
    schema = {
        "computedNodeProperties": {
            "invalid": "unknownType"
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    with pytest.raises(SchemaError, match="Unknown computed property type"):
        load_schema(schema_path)


def test_validate_computed_property_not_string(tmp_path):
    """Test error when computed property type is not a string."""
    schema = {
        "computedNodeProperties": {
            "count": {"type": "degree"}
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    with pytest.raises(SchemaError, match="must be a string type"):
        load_schema(schema_path)


def test_computed_degree_in_graph(tmp_path, computed_schema):
    """Test that degree computed property is calculated correctly."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(computed_schema))

    schema = load_schema(schema_path)
    graph = Graph(5, 8, schema=schema, seed=42)
    graph.generate()

    # Verify each node has connectionCount matching its actual degree
    undirected = graph.graph.to_undirected()
    for node_id, props in graph.graph.nodes(data=True):
        expected_degree = undirected.degree(node_id)
        assert props['connectionCount'] == expected_degree


def test_computed_degree_with_no_edges(tmp_path, computed_schema):
    """Test degree is 0 for nodes with no edges."""
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(computed_schema))

    schema = load_schema(schema_path)
    graph = Graph(5, 0, schema=schema, seed=42)
    graph.generate()

    for _, props in graph.graph.nodes(data=True):
        assert props['connectionCount'] == 0


def test_multiple_computed_properties(tmp_path):
    """Test schema with multiple computed properties (all degree for now)."""
    schema = {
        "nodeLabel": "Node",
        "edgeLabel": "connects",
        "computedNodeProperties": {
            "friendCount": "degree",
            "connections": "degree"
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    loaded = load_schema(schema_path)
    graph = Graph(4, 5, schema=loaded, seed=42)
    graph.generate()

    for _, props in graph.graph.nodes(data=True):
        assert 'friendCount' in props
        assert 'connections' in props
        # Both should have the same value since they're both degree
        assert props['friendCount'] == props['connections']


# --- Combined Features Tests ---

def test_schema_with_all_features(tmp_path):
    """Test schema combining symmetric and computed properties."""
    schema = {
        "nodeLabel": "Person",
        "edgeLabel": "knows",
        "nodeProperties": {
            "name": "Name",
            "email": "Email"
        },
        "edgeProperties": {
            "strength": {"type": "Int", "min": 1, "max": 100},
            "lastMet": {"type": "Date", "symmetric": True},
            "sharedInterests": {"type": "Int", "min": 0, "max": 20, "symmetric": True}
        },
        "computedNodeProperties": {
            "friendCount": "degree"
        }
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))

    loaded = load_schema(schema_path)
    graph = Graph(6, 12, schema=loaded, seed=42)
    graph.generate()

    # Check symmetric properties
    symmetric_props = get_symmetric_edge_properties(loaded)
    assert 'lastMet' in symmetric_props
    assert 'sharedInterests' in symmetric_props

    # Check computed properties
    computed_props = get_computed_node_properties(loaded)
    assert 'friendCount' in computed_props

    # Verify friendCount matches degree
    undirected = graph.graph.to_undirected()
    for node_id, props in graph.graph.nodes(data=True):
        assert props['friendCount'] == undirected.degree(node_id)


def test_symmetric_property_generator_ignores_symmetric_key():
    """Test that symmetric key is ignored in generator config."""
    from faker import Faker
    from knows.schema import _create_generator

    # Generator should work the same with or without symmetric
    gen_with = _create_generator({"type": "Int", "min": 10, "max": 20, "symmetric": True})
    gen_without = _create_generator({"type": "Int", "min": 10, "max": 20})

    faker = Faker()
    faker.seed_instance(42)
    val_with = gen_with(faker)

    faker.seed_instance(42)
    val_without = gen_without(faker)

    # Both should generate same value with same seed
    assert val_with == val_without
    assert 10 <= val_with <= 20


# --- Schema Consistency Tests ---

def test_schema_consistency_validation():
    """Test that TYPE_GENERATORS covers all types in JSON Schema."""
    from knows.schema import _get_json_schema

    schema = _get_json_schema()
    schema_types = set(schema['$defs']['typeName']['enum'])

    # All schema types should have a generator or alias
    for type_name in schema_types:
        assert type_name in TYPE_GENERATORS or type_name in TYPE_ALIASES, \
            f"Type '{type_name}' from JSON Schema has no generator"


def test_all_generators_in_schema():
    """Test that all TYPE_GENERATORS are listed in JSON Schema."""
    from knows.schema import _get_json_schema

    schema = _get_json_schema()
    schema_types = set(schema['$defs']['typeName']['enum'])

    # All generators should be in schema (canonical types)
    for type_name in TYPE_GENERATORS.keys():
        assert type_name in schema_types, \
            f"Generator type '{type_name}' not in JSON Schema"


def test_duration_pattern_matches_json_schema():
    """The duration regex in schema.json stays in sync with the Python one."""
    from knows.schema import _get_json_schema, _DURATION_PATTERN

    schema = _get_json_schema()
    json_pattern = schema['$defs']['durationString']['pattern']
    assert json_pattern == _DURATION_PATTERN.pattern


def test_computed_types_consistency():
    """Test that COMPUTED_PROPERTY_TYPES matches JSON Schema."""
    from knows.schema import _get_json_schema

    schema = _get_json_schema()
    schema_computed = set(
        schema['properties']['computedNodeProperties']['additionalProperties']['enum']
    )

    assert schema_computed == set(COMPUTED_PROPERTY_TYPES.keys()), \
        "COMPUTED_PROPERTY_TYPES does not match JSON Schema"
