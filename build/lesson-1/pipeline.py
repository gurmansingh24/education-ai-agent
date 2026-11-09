import json
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import ValidationError

from diagnostics import format_json_error, format_validation_errors
from schema import Extraction


FailureKind = Literal["json", "schema"]


@dataclass
class ValidationResult:
    value: Extraction | None
    errors: list[str]
    failure_kind: FailureKind | None = None

    @property
    def ok(self) -> bool:
        return self.value is not None


def validate_response(raw_response: str) -> ValidationResult:
    """Parse JSON first, then validate the parsed value against the schema."""
    try:
        parsed: Any = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        return ValidationResult(
            value=None,
            errors=format_json_error(exc),
            failure_kind="json",
        )

    try:
        value = Extraction.model_validate(parsed)
    except ValidationError as exc:
        return ValidationResult(
            value=None,
            errors=format_validation_errors(exc),
            failure_kind="schema",
        )

    return ValidationResult(
        value=value,
        errors=[],
    )
