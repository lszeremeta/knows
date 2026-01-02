"""GQL-inspired schema support for property graph generation.

This module provides functionality to load and validate JSON schema files
that define custom node and edge types. GQL-inspired (ISO/IEC 39075).

Example schema file:
{
    "nodeLabel": "Employee",
    "edgeLabel": "collaborates",
    "nodeProperties": {
        "name": "String",
        "department": {"enum": ["HR", "Engineering", "Sales"]},
        "salary": {"type": "Int", "min": 30000, "max": 200000},
        "hireDate": "Date"
    },
    "edgeProperties": {
        "projectCount": {"type": "Int", "min": 1, "max": 100},
        "since": {"type": "Date", "symmetric": true}
    },
    "computedNodeProperties": {
        "connectionCount": "degree"
    }
}
"""

import datetime
import json
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from faker import Faker
import jsonschema
from jsonschema import ValidationError


class SchemaError(Exception):
    """Raised when schema validation fails."""
    pass


def _load_json_schema() -> dict:
    """Load the JSON Schema for validating Knows graph schemas."""
    schema_file = resources.files(__package__).joinpath("schema.json")
    return json.loads(schema_file.read_text(encoding="utf-8"))


# Lazy-loaded JSON Schema
_KNOWS_JSON_SCHEMA: Optional[dict] = None


def _get_json_schema() -> dict:
    """Get the JSON Schema, loading it on first access."""
    global _KNOWS_JSON_SCHEMA
    if _KNOWS_JSON_SCHEMA is None:
        _KNOWS_JSON_SCHEMA = _load_json_schema()
    return _KNOWS_JSON_SCHEMA


# Type definitions mapping GQL-like types to Faker generators
TYPE_GENERATORS: Dict[str, Callable[[Faker, dict], Any]] = {
    # String types
    'String': lambda f, cfg: f.word(),
    'Name': lambda f, cfg: f.name(),
    'FirstName': lambda f, cfg: f.first_name(),
    'LastName': lambda f, cfg: f.last_name(),
    'FullName': lambda f, cfg: f.name(),
    'Email': lambda f, cfg: f.email(),
    'Phone': lambda f, cfg: f.phone_number(),
    'Address': lambda f, cfg: f.address(),
    'City': lambda f, cfg: f.city(),
    'Country': lambda f, cfg: f.country(),
    'Company': lambda f, cfg: f.company(),
    'Job': lambda f, cfg: f.job(),
    'Text': lambda f, cfg: f.text(max_nb_chars=cfg.get('maxLength', 200)),
    'Sentence': lambda f, cfg: f.sentence(),
    'Paragraph': lambda f, cfg: f.paragraph(),
    'Url': lambda f, cfg: f.url(),
    'Color': lambda f, cfg: f.color_name(),
    'Uuid': lambda f, cfg: str(f.uuid4()),

    # Numeric types
    'Int': lambda f, cfg: f.random_int(
        min=cfg.get('min', 0),
        max=cfg.get('max', 10000)
    ),
    'Integer': lambda f, cfg: f.random_int(
        min=cfg.get('min', 0),
        max=cfg.get('max', 10000)
    ),
    'Float': lambda f, cfg: round(
        f.pyfloat(
            min_value=cfg.get('min', 0.0),
            max_value=cfg.get('max', 1000.0)
        ),
        cfg.get('precision', 2)
    ),
    'Double': lambda f, cfg: round(
        f.pyfloat(
            min_value=cfg.get('min', 0.0),
            max_value=cfg.get('max', 1000.0)
        ),
        cfg.get('precision', 4)
    ),
    'Boolean': lambda f, cfg: f.boolean(),
    'Bool': lambda f, cfg: f.boolean(),

    # Date/Time types
    'Date': lambda f, cfg: f.date_between(
        start_date=datetime.date.fromisoformat(cfg.get('min', '1970-01-01')),
        end_date=datetime.date.fromisoformat(cfg.get('max', '2025-12-31'))
    ).isoformat(),
    'DateTime': lambda f, cfg: f.date_time_between(
        start_date=cfg.get('min', '-30y'),
        end_date=cfg.get('max', 'now')
    ).isoformat(),
    'Time': lambda f, cfg: f.time(),
    'Year': lambda f, cfg: f.random_int(
        min=cfg.get('min', 1950),
        max=cfg.get('max', 2025)
    ),
}

# Aliases for common types (GQL uses uppercase)
TYPE_ALIASES: Dict[str, str] = {
    'STRING': 'String',
    'INTEGER': 'Int',
    'INT64': 'Int',
    'UINT64': 'Int',
    'FLOAT64': 'Float',
    'BOOLEAN': 'Boolean',
    'BOOL': 'Bool',
    'DATE': 'Date',
    'DATETIME': 'DateTime',
    'ZONED DATETIME': 'DateTime',
}

# Supported computed node property types
COMPUTED_PROPERTY_TYPES: Dict[str, str] = {
    'degree': 'degree',  # Total unique connections (undirected degree)
}


def load_schema(path: Union[str, Path]) -> dict:
    """Load and validate a JSON schema file.

    Args:
        path: Path to the JSON schema file.

    Returns:
        Validated schema dictionary.

    Raises:
        SchemaError: If the schema file is invalid or cannot be loaded.
    """
    path = Path(path)

    if not path.exists():
        raise SchemaError(f"Schema file not found: {path}")

    if not path.suffix.lower() == '.json':
        raise SchemaError(f"Schema file must be JSON format: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaError(f"Invalid JSON in schema file: {e}")

    _validate_schema(schema)
    return schema


def _validate_schema(schema: dict) -> None:
    """Validate schema structure and types using JSON Schema.

    Args:
        schema: Schema dictionary to validate.

    Raises:
        SchemaError: If schema is invalid.
    """
    if not isinstance(schema, dict):
        raise SchemaError("Schema must be a JSON object")

    try:
        jsonschema.validate(instance=schema, schema=_get_json_schema())
    except ValidationError as e:
        raise SchemaError(_format_validation_error(e)) from None


def _format_validation_error(error: ValidationError) -> str:
    """Format jsonschema ValidationError into a user-friendly message.

    Args:
        error: The jsonschema ValidationError.

    Returns:
        A user-friendly error message.
    """
    path = list(error.absolute_path)

    # Handle specific validation scenarios
    if error.validator == "type":
        if path:
            field_name = path[-1] if isinstance(path[-1], str) else ".".join(str(p) for p in path)
            # Check if this is a computed property type error
            if len(path) >= 2 and path[-2] == "computedNodeProperties":
                return f"Computed property '{field_name}' must be a string type"
            return f"{field_name} must be a {error.validator_value}"
        return f"Schema must be a {error.validator_value}"

    if error.validator == "minLength":
        field_name = path[-1] if path else "value"
        return f"{field_name} cannot be empty"

    if error.validator == "enum":
        if path:
            # Check if this is a property type error
            if len(path) >= 2 and path[-2] in ("nodeProperties", "edgeProperties"):
                prop_name = path[-1]
                return (
                    f"Unknown type '{error.instance}' for property '{prop_name}'. "
                    f"Available types: {', '.join(sorted(TYPE_GENERATORS.keys()))}"
                )
            if len(path) >= 2 and path[-2] == "computedNodeProperties":
                prop_name = path[-1]
                return (
                    f"Unknown computed property type '{error.instance}' for '{prop_name}'. "
                    f"Available types: {', '.join(sorted(COMPUTED_PROPERTY_TYPES.keys()))}"
                )
            # Handle type field in complex definition
            if path and path[-1] == "type":
                return (
                    f"Unknown type '{error.instance}'. "
                    f"Available types: {', '.join(sorted(TYPE_GENERATORS.keys()))}"
                )
        return f"'{error.instance}' is not one of {error.validator_value}"

    if error.validator == "minItems":
        if path and len(path) >= 2:
            prop_name = path[-2]
            return f"Property '{prop_name}' enum must be a non-empty array"
        return "enum must be a non-empty array"

    if error.validator == "additionalProperties":
        if path:
            return f"Unknown property in schema at '{'.'.join(str(p) for p in path)}'"
        return f"Additional properties are not allowed: {error.message}"

    if error.validator == "oneOf":
        if path and len(path) >= 2 and path[-2] in ("nodeProperties", "edgeProperties"):
            prop_name = path[-1]
            # Check if it's missing type/enum
            if isinstance(error.instance, dict):
                if "type" not in error.instance and "enum" not in error.instance:
                    return f"Property '{prop_name}' must have 'type' or 'enum' field"
            return f"Invalid definition for property '{prop_name}'"
        return "Invalid property definition"

    if error.validator == "required":
        missing = error.validator_value[0] if error.validator_value else "field"
        if path and len(path) >= 2:
            prop_name = path[-1]
            return f"Property '{prop_name}' must have '{missing}' field"
        return f"Missing required field: {missing}"

    # Default: return the original message
    return error.message


def _create_generator(definition: Union[str, dict]) -> Callable[[Faker], Any]:
    """Create a Faker generator function from a property definition.

    Args:
        definition: Property type definition.

    Returns:
        A function that takes a Faker instance and returns a generated value.
    """
    if isinstance(definition, str):
        type_name = TYPE_ALIASES.get(definition.upper(), definition)
        base_gen = TYPE_GENERATORS[type_name]
        return lambda f: base_gen(f, {})

    elif isinstance(definition, dict):
        if 'enum' in definition:
            values = tuple(definition['enum'])
            return lambda f: f.random_element(values)
        else:
            type_name = TYPE_ALIASES.get(definition['type'].upper(), definition['type'])
            base_gen = TYPE_GENERATORS[type_name]
            # Filter out non-generator config keys like 'type' and 'symmetric'
            config = {k: v for k, v in definition.items() if k not in ('type', 'symmetric')}
            return lambda f: base_gen(f, config)

    # Fallback (shouldn't reach here after validation)
    return lambda f: f.word()


def schema_to_generators(schema: dict) -> Tuple[
    Dict[str, Callable[[Faker], Any]],
    Dict[str, Callable[[Faker], Any]],
    str,
    str
]:
    """Convert a schema to property generators.

    Args:
        schema: Validated schema dictionary.

    Returns:
        Tuple of (node_generators, edge_generators, node_label, edge_label).
    """
    node_generators: Dict[str, Callable[[Faker], Any]] = {}
    edge_generators: Dict[str, Callable[[Faker], Any]] = {}

    # Process node properties
    for prop_name, prop_def in schema.get('nodeProperties', {}).items():
        node_generators[prop_name] = _create_generator(prop_def)

    # Process edge properties
    for prop_name, prop_def in schema.get('edgeProperties', {}).items():
        edge_generators[prop_name] = _create_generator(prop_def)

    # Get labels (with defaults)
    node_label = schema.get('nodeLabel', 'Node')
    edge_label = schema.get('edgeLabel', 'edge')

    return node_generators, edge_generators, node_label, edge_label


def get_schema_properties(schema: dict) -> Tuple[List[str], List[str]]:
    """Extract property names from schema.

    Args:
        schema: Validated schema dictionary.

    Returns:
        Tuple of (node_property_names, edge_property_names).
    """
    node_props = list(schema.get('nodeProperties', {}).keys())
    edge_props = list(schema.get('edgeProperties', {}).keys())
    return node_props, edge_props


def get_symmetric_edge_properties(schema: dict) -> frozenset:
    """Extract edge properties marked as symmetric.

    Symmetric properties will have the same value for edges connecting
    the same nodes in both directions (A->B and B->A).

    Args:
        schema: Validated schema dictionary.

    Returns:
        Frozenset of symmetric edge property names.
    """
    symmetric_props = set()
    for prop_name, prop_def in schema.get('edgeProperties', {}).items():
        if isinstance(prop_def, dict) and prop_def.get('symmetric', False):
            symmetric_props.add(prop_name)
    return frozenset(symmetric_props)


def get_computed_node_properties(schema: dict) -> Dict[str, str]:
    """Extract computed node properties from schema.

    Args:
        schema: Validated schema dictionary.

    Returns:
        Dictionary mapping property names to their computation type.
    """
    return dict(schema.get('computedNodeProperties', {}))
