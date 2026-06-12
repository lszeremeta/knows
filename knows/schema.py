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
import re
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from faker import Faker
from faker.providers.date_time import ParseError
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


# Calendar approximations used to reduce ISO 8601 durations to a single
# scalar (seconds) so a value can be drawn from a [min, max] range. Months
# and years are not fixed-length, so this is intentionally approximate and
# documented as such for synthetic data generation.
_SECONDS_PER_MINUTE = 60
_SECONDS_PER_HOUR = 60 * _SECONDS_PER_MINUTE
_SECONDS_PER_DAY = 24 * _SECONDS_PER_HOUR
_SECONDS_PER_WEEK = 7 * _SECONDS_PER_DAY
_SECONDS_PER_MONTH = 30 * _SECONDS_PER_DAY
_SECONDS_PER_YEAR = 365 * _SECONDS_PER_DAY

# ISO 8601 duration: P[nY][nM][nW][nD][T[nH][nM][nS]] (integer components).
# The (?!$) lookahead after P rejects an empty "P", and the one after T
# rejects a dangling time designator (e.g. "PT") with no time component.
_DURATION_PATTERN = re.compile(
    r'^P(?!$)'
    r'(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?'
    r'(?:T(?!$)(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$'
)


def _duration_to_seconds(iso: str) -> int:
    """Convert an ISO 8601 duration string to an (approximate) seconds count.

    Uses fixed calendar approximations (1 year = 365 days, 1 month = 30 days,
    1 week = 7 days) so durations can be compared and sampled from a range.

    Args:
        iso: ISO 8601 duration string, e.g. "P1Y2M10DT2H30M".

    Returns:
        Total number of seconds.

    Raises:
        SchemaError: If the string is not a valid ISO 8601 duration.
    """
    match = _DURATION_PATTERN.match(iso)
    if not match:
        raise SchemaError(f"Invalid ISO 8601 duration: {iso!r}")
    years, months, weeks, days, hours, minutes, seconds = (
        int(g) if g else 0 for g in match.groups()
    )
    return (
        years * _SECONDS_PER_YEAR
        + months * _SECONDS_PER_MONTH
        + weeks * _SECONDS_PER_WEEK
        + days * _SECONDS_PER_DAY
        + hours * _SECONDS_PER_HOUR
        + minutes * _SECONDS_PER_MINUTE
        + seconds
    )


def _seconds_to_duration(total: int) -> str:
    """Format a seconds count as an ISO 8601 duration string.

    Decomposes the value using the same calendar approximations as
    :func:`_duration_to_seconds`, omitting zero components. A zero total
    is rendered as "PT0S".

    Args:
        total: Total number of seconds (non-negative).

    Returns:
        ISO 8601 duration string, e.g. "P1Y2M10DT2H30M".
    """
    years, total = divmod(total, _SECONDS_PER_YEAR)
    months, total = divmod(total, _SECONDS_PER_MONTH)
    days, total = divmod(total, _SECONDS_PER_DAY)
    hours, total = divmod(total, _SECONDS_PER_HOUR)
    minutes, seconds = divmod(total, _SECONDS_PER_MINUTE)

    date_part = "".join(
        f"{v}{u}" for v, u in ((years, 'Y'), (months, 'M'), (days, 'D')) if v
    )
    time_part = "".join(
        f"{v}{u}" for v, u in ((hours, 'H'), (minutes, 'M'), (seconds, 'S')) if v
    )
    if time_part:
        return f"P{date_part}T{time_part}"
    if date_part:
        return f"P{date_part}"
    return "PT0S"


def _normalize_duration_config(config: dict, prop_name: str) -> dict:
    """Validate Duration min/max once and precompute them as seconds.

    Args:
        config: Generator config, optionally with 'min'/'max' ISO 8601
            duration strings.
        prop_name: Property name, used in error messages.

    Returns:
        A copy of the config with 'min'/'max' replaced by seconds counts.

    Raises:
        SchemaError: If a bound is not a valid ISO 8601 duration string
            or min exceeds max.
    """
    normalized = dict(config)
    for key, default in (('min', 'PT0S'), ('max', 'P1Y')):
        value = normalized.get(key, default)
        if not isinstance(value, str):
            raise SchemaError(
                f"Property '{prop_name}': '{key}' must be an ISO 8601 "
                f"duration string, got {value!r}"
            )
        try:
            normalized[key] = _duration_to_seconds(value)
        except SchemaError as e:
            raise SchemaError(f"Property '{prop_name}': {e}") from None
    if normalized['min'] > normalized['max']:
        raise SchemaError(
            f"Property '{prop_name}': duration 'min' is greater than 'max'"
        )
    return normalized


def _normalize_date_config(config: dict, prop_name: str) -> dict:
    """Validate Date min/max once and precompute them as date objects.

    Args:
        config: Generator config, optionally with 'min'/'max' ISO dates.
        prop_name: Property name, used in error messages.

    Returns:
        A copy of the config with 'min'/'max' replaced by date objects.

    Raises:
        SchemaError: If a bound is not a valid ISO date (YYYY-MM-DD)
            or min is later than max.
    """
    normalized = dict(config)
    for key, default in (('min', '1970-01-01'), ('max', '2025-12-31')):
        value = normalized.get(key, default)
        try:
            normalized[key] = datetime.date.fromisoformat(value)
        except (TypeError, ValueError):
            raise SchemaError(
                f"Property '{prop_name}': '{key}' must be an ISO date "
                f"(YYYY-MM-DD), got {value!r}"
            ) from None
    if normalized['min'] > normalized['max']:
        raise SchemaError(
            f"Property '{prop_name}': date 'min' is later than 'max'"
        )
    return normalized


def _normalize_datetime_config(config: dict, prop_name: str) -> dict:
    """Validate DateTime min/max by trial-generating a value with Faker.

    Faker accepts several bound formats ('-30y', 'now', ISO dates,
    timestamps, ...), so the bounds are checked by attempting a generation
    on a throwaway Faker instance instead of matching a pattern.

    Args:
        config: Generator config, optionally with 'min'/'max' bounds.
        prop_name: Property name, used in error messages.

    Returns:
        The config, unchanged.

    Raises:
        SchemaError: If Faker cannot interpret one of the bounds.
    """
    try:
        Faker().date_time_between(
            start_date=config.get('min', '-30y'),
            end_date=config.get('max', 'now')
        )
    except (ParseError, ValueError, TypeError, OverflowError) as e:
        raise SchemaError(
            f"Property '{prop_name}': invalid DateTime bound: {e}"
        ) from None
    return config


def _make_numeric_normalizer(
    default_min: Union[int, float],
    default_max: Union[int, float],
    strict: bool = False
) -> Callable[[dict, str], dict]:
    """Build a config normalizer that validates numeric min/max bounds.

    Args:
        default_min: Default lower bound, matching the type's generator.
        default_max: Default upper bound, matching the type's generator.
        strict: If True, require min strictly below max (Faker's pyfloat
            rejects equal bounds).

    Returns:
        A normalizer raising SchemaError on non-numeric or reversed bounds.
    """
    def normalize(config: dict, prop_name: str) -> dict:
        lo = config.get('min', default_min)
        hi = config.get('max', default_max)
        for key, value in (('min', lo), ('max', hi)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SchemaError(
                    f"Property '{prop_name}': '{key}' must be a number, "
                    f"got {value!r}"
                )
        if lo > hi or (strict and lo == hi):
            raise SchemaError(
                f"Property '{prop_name}': 'min' ({lo}) must be "
                f"{'below' if strict else 'at most'} 'max' ({hi})"
            )
        return config

    return normalize


# Default ranges shared by the type generators below and the numeric
# config normalizers, so bounds are validated against the same defaults
# the generators fall back to.
_INT_DEFAULTS = (0, 10000)
_FLOAT_DEFAULTS = (0.0, 1000.0)
_YEAR_DEFAULTS = (1950, 2025)

# Per-type config validation applied once when a generator is created, so
# bad bounds fail fast with property context instead of mid-generation, and
# parsed bounds are reused instead of being re-parsed for every value.
_CONFIG_NORMALIZERS: Dict[str, Callable[[dict, str], dict]] = {
    'Duration': _normalize_duration_config,
    'Date': _normalize_date_config,
    'DateTime': _normalize_datetime_config,
    'Int': _make_numeric_normalizer(*_INT_DEFAULTS),
    'Integer': _make_numeric_normalizer(*_INT_DEFAULTS),
    'Float': _make_numeric_normalizer(*_FLOAT_DEFAULTS, strict=True),
    'Double': _make_numeric_normalizer(*_FLOAT_DEFAULTS, strict=True),
    'Year': _make_numeric_normalizer(*_YEAR_DEFAULTS),
}


def _normalize_config(type_name: str, config: dict, prop_name: str) -> dict:
    """Apply the type's config normalizer, if it has one."""
    normalizer = _CONFIG_NORMALIZERS.get(type_name)
    return normalizer(config, prop_name) if normalizer else config


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
        min=cfg.get('min', _INT_DEFAULTS[0]),
        max=cfg.get('max', _INT_DEFAULTS[1])
    ),
    'Integer': lambda f, cfg: f.random_int(
        min=cfg.get('min', _INT_DEFAULTS[0]),
        max=cfg.get('max', _INT_DEFAULTS[1])
    ),
    'Float': lambda f, cfg: round(
        f.pyfloat(
            min_value=cfg.get('min', _FLOAT_DEFAULTS[0]),
            max_value=cfg.get('max', _FLOAT_DEFAULTS[1])
        ),
        cfg.get('precision', 2)
    ),
    'Double': lambda f, cfg: round(
        f.pyfloat(
            min_value=cfg.get('min', _FLOAT_DEFAULTS[0]),
            max_value=cfg.get('max', _FLOAT_DEFAULTS[1])
        ),
        cfg.get('precision', 4)
    ),
    'Boolean': lambda f, cfg: f.boolean(),
    'Bool': lambda f, cfg: f.boolean(),

    # Date/Time types
    # Date and Duration receive bounds pre-parsed by their config
    # normalizers (date objects / seconds counts).
    'Date': lambda f, cfg: f.date_between(
        start_date=cfg.get('min', datetime.date(1970, 1, 1)),
        end_date=cfg.get('max', datetime.date(2025, 12, 31))
    ).isoformat(),
    'DateTime': lambda f, cfg: f.date_time_between(
        start_date=cfg.get('min', '-30y'),
        end_date=cfg.get('max', 'now')
    ).isoformat(),
    'Time': lambda f, cfg: f.time(),
    'Year': lambda f, cfg: f.random_int(
        min=cfg.get('min', _YEAR_DEFAULTS[0]),
        max=cfg.get('max', _YEAR_DEFAULTS[1])
    ),
    'Duration': lambda f, cfg: _seconds_to_duration(
        f.random_int(
            min=cfg.get('min', 0),
            max=cfg.get('max', _SECONDS_PER_YEAR)
        )
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
    'DURATION': 'Duration',
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
            # Type-conditional min/max constraint (e.g. Duration bounds
            # must be strings, numeric bounds must be numbers)
            if field_name in ("min", "max") and len(path) >= 3:
                return (
                    f"Property '{path[-2]}': '{field_name}' must be a "
                    f"{error.validator_value}, got {error.instance!r}"
                )
            return f"{field_name} must be a {error.validator_value}"
        return f"Schema must be a {error.validator_value}"

    if error.validator == "pattern":
        if path and path[-1] in ("min", "max") and len(path) >= 2:
            prop_name = path[-2]
            if str(error.validator_value).startswith("^P"):
                return (
                    f"Property '{prop_name}': '{path[-1]}' must be an "
                    f"ISO 8601 duration string (e.g. 'P1Y2M10DT2H30M'), "
                    f"got {error.instance!r}"
                )
            return (
                f"Property '{prop_name}': '{path[-1]}' must be an ISO date "
                f"(YYYY-MM-DD), got {error.instance!r}"
            )
        return error.message

    if error.validator == "minLength":
        field_name = path[-1] if path else "value"
        return f"{field_name} cannot be empty"

    if error.validator == "minimum":
        if path and len(path) >= 2:
            return (
                f"Property '{path[-2]}': '{path[-1]}' must be at least "
                f"{error.validator_value}, got {error.instance!r}"
            )
        return error.message

    if error.validator == "not":
        # The only 'not' rule rejects 'symmetric' on node properties
        if error.validator_value == {"required": ["symmetric"]} and path:
            return (
                f"Property '{path[-1]}': 'symmetric' is only supported "
                f"on edge properties"
            )
        return error.message

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


def _create_generator(
    definition: Union[str, dict],
    prop_name: str = 'property'
) -> Callable[[Faker], Any]:
    """Create a Faker generator function from a property definition.

    Args:
        definition: Property type definition.
        prop_name: Property name, used in validation error messages.

    Returns:
        A function that takes a Faker instance and returns a generated value.

    Raises:
        SchemaError: If the definition's constraints are invalid for its type.
    """
    if isinstance(definition, str):
        type_name = TYPE_ALIASES.get(definition.upper(), definition)
        base_gen = TYPE_GENERATORS[type_name]
        config = _normalize_config(type_name, {}, prop_name)
        return lambda f: base_gen(f, config)

    elif isinstance(definition, dict):
        if 'enum' in definition:
            values = tuple(definition['enum'])
            return lambda f: f.random_element(values)
        else:
            type_name = TYPE_ALIASES.get(definition['type'].upper(), definition['type'])
            base_gen = TYPE_GENERATORS[type_name]
            # Filter out non-generator config keys like 'type' and 'symmetric'
            config = {k: v for k, v in definition.items() if k not in ('type', 'symmetric')}
            config = _normalize_config(type_name, config, prop_name)
            return lambda f: base_gen(f, config)

    # Unreachable after schema validation; fail loudly rather than
    # silently generating filler data.
    raise SchemaError(
        f"Property '{prop_name}': invalid definition: {definition!r}"
    )


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
        node_generators[prop_name] = _create_generator(prop_def, prop_name)

    # Process edge properties
    for prop_name, prop_def in schema.get('edgeProperties', {}).items():
        edge_generators[prop_name] = _create_generator(prop_def, prop_name)

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
