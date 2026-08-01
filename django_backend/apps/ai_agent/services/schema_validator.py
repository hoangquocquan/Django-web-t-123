"""Small strict JSON-schema subset used for agent plans and tool arguments."""

from __future__ import annotations


class SchemaValidationError(ValueError):
    """Raised when structured agent data violates its declared contract."""


class StrictSchemaValidator:
    """Validate the object, array and scalar constraints needed by local tools."""

    TYPE_MAP = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
    }

    def validate(self, value, schema, path="$"):
        """Raise a readable error at the first invalid path."""
        expected = schema.get("type")
        if expected:
            expected_type = self.TYPE_MAP.get(expected)
            if expected_type is None:
                raise SchemaValidationError(f"{path}: unsupported schema type '{expected}'.")
            if expected in {"integer", "number"} and isinstance(value, bool):
                raise SchemaValidationError(f"{path}: expected {expected}.")
            if not isinstance(value, expected_type):
                raise SchemaValidationError(f"{path}: expected {expected}.")

        if isinstance(value, dict):
            required = schema.get("required", [])
            missing = [field for field in required if field not in value]
            if missing:
                raise SchemaValidationError(f"{path}: missing fields {', '.join(missing)}.")
            properties = schema.get("properties", {})
            if schema.get("additionalProperties") is False:
                unknown = [field for field in value if field not in properties]
                if unknown:
                    raise SchemaValidationError(f"{path}: unknown fields {', '.join(unknown)}.")
            for field, item in value.items():
                if field in properties:
                    self.validate(item, properties[field], f"{path}.{field}")

        if isinstance(value, list) and "items" in schema:
            for index, item in enumerate(value):
                self.validate(item, schema["items"], f"{path}[{index}]")

        if isinstance(value, str) and len(value) < schema.get("minLength", 0):
            raise SchemaValidationError(f"{path}: string is too short.")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                raise SchemaValidationError(f"{path}: value is below minimum.")
            if "maximum" in schema and value > schema["maximum"]:
                raise SchemaValidationError(f"{path}: value exceeds maximum.")
        return value
