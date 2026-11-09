import json

from pydantic import ValidationError


def format_validation_errors(exc: ValidationError) -> list[str]:
    """Turn Pydantic errors into readable field-level diagnostics."""
    messages: list[str] = []

    for error in exc.errors():
        path = ".".join(str(part) for part in error["loc"]) or "<root>"
        messages.append(f"{path}: {error['msg']}")

    return messages


def format_json_error(exc: json.JSONDecodeError) -> list[str]:
    """Turn a JSON parser error into a readable diagnostic."""
    return [
        f"JSON syntax at line {exc.lineno}, column {exc.colno}: {exc.msg}"
    ]
