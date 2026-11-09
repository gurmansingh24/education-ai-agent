# Lesson 1: Parse It, Then Prove It Matches the Contract

## Checkpoints

After this lesson, you will be able to:

- Explain why asking a model for “JSON” does not guarantee usable structured output.
- Distinguish JSON parsing failures from schema-validation failures.
- Define an explicit application schema with Pydantic.
- Validate parsed JSON against that schema.
- Display field-level, actionable validation errors.
- Ensure downstream code receives only validated data.

## Section 1: Model Output Is Untrusted Input

A model response is external input. Even when a prompt says “return only JSON,” the response can still fail in several different ways.

The first failure mode is **prose instead of JSON**:

```text
Here is the extracted result:

{"title": "Replace filter", "priority": "high"}
```

The JSON object is present, but the complete response is not valid JSON because of the surrounding prose.

The second failure mode is **malformed JSON**:

```json
{"title": "Replace filter", "priority": "high"
```

This resembles JSON, but it is missing a closing brace. A JSON parser must reject it.

The third failure mode is **valid JSON with the wrong structure**:

```json
{
  "title": "Replace filter",
  "priority": "urgent",
  "tags": "maintenance",
  "confidence": 1.4
}
```

This text is valid JSON. However, it may still violate application rules:

- `"priority"` may not be one of the allowed values.
- `"tags"` may need to be an array rather than a string.
- `"confidence"` may need to be between `0` and `1`.

These failures have different causes and need different diagnostics. A parser cannot tell you that `"urgent"` is not an allowed priority because that is not a JSON syntax rule. Conversely, a schema validator cannot validate a response that was never successfully parsed as JSON.

Treating model output as untrusted input creates a useful boundary:

```text
raw model response
        |
        v
JSON parser
        |
        v
parsed Python value
        |
        v
schema validator
        |
        v
validated application object
```

Only the final object should enter application logic. Raw text and unvalidated dictionaries should remain at the boundary, where failures can be reported safely.

## Section 2: JSON Parsing Versus Schema Validation

JSON parsing checks **syntax**. It answers: “Can this sequence of characters be interpreted as a JSON value?”

Python’s standard library provides this operation:

```python
import json

value = json.loads(raw_response)
```

If the input is malformed, `json.loads` raises `json.JSONDecodeError`:

```python
try:
    value = json.loads(raw_response)
except json.JSONDecodeError as exc:
    print(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
```

Successful parsing does not mean the result is useful to your application. JSON allows several types of top-level values:

```json
42
```

```json
["high", "low"]
```

```json
{"priority": "urgent"}
```

Your application may require one object with specific fields, types, and constraints. That is the job of **schema validation**.

A schema can define rules such as:

- `title` is required and must be a non-empty string.
- `priority` is required and must be `"low"`, `"medium"`, or `"high"`.
- `tags` is required and must be a list of strings.
- `confidence` is required and must be between `0` and `1`.
- Unknown fields are rejected.

The two stages should remain separate:

```python
parsed = json.loads(raw_response)
validated = Extraction.model_validate(parsed)
```

The first line can fail with a JSON parsing exception. The second can fail with a Pydantic `ValidationError`.

This distinction matters operationally. A malformed response may require a repair request such as “return valid JSON only.” A structurally invalid response needs a more specific request such as “change `confidence` to a number between 0 and 1 and make `tags` an array of strings.”

Do not use a successful `json.loads` call as proof that the response is safe for downstream code. It proves only that the text obeys JSON syntax.

## Section 3: Designing an Explicit Output Contract

Pydantic lets you express the application contract as a Python model. Install Pydantic v2 in the Python 3.12 environment:

```text
pydantic>=2.0,<3.0
```

The following schema describes a small extraction result:

```python
# schema.py
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[
        StrictStr,
        Field(min_length=1, max_length=120),
    ]
    priority: Literal["low", "medium", "high"]
    tags: Annotated[
        list[StrictStr],
        Field(max_length=8),
    ]
    confidence: Annotated[
        float,
        Field(ge=0.0, le=1.0),
    ]
```

`BaseModel` supplies parsing and validation behavior. `Literal` restricts `priority` to a known set of values. `Field` adds constraints. `extra="forbid"` rejects fields that are not part of the contract instead of silently ignoring them.

`StrictStr` prevents values such as an integer from being accepted as a string through coercion. The `confidence` field accepts numeric values and enforces its range.

Use `model_validate` when you already have a Python object, usually from `json.loads`:

```python
from schema import Extraction

data = {
    "title": "Replace filter",
    "priority": "high",
    "tags": ["maintenance"],
    "confidence": 0.94,
}

extraction = Extraction.model_validate(data)
print(extraction)
```

On success, `extraction` is an `Extraction` instance rather than an arbitrary dictionary. You can access fields with attributes:

```python
print(extraction.title)
print(extraction.priority)
```

The schema is executable documentation. It gives the parser boundary a precise definition of what downstream code is allowed to receive.

## Section 4: Inspecting Validation Failures

Pydantic raises `ValidationError` when parsed data does not satisfy the model. The exception contains structured details for every failure.

For example:

```python
from pydantic import ValidationError

try:
    Extraction.model_validate({
        "title": "Replace filter",
        "priority": "urgent",
        "tags": "maintenance",
        "confidence": 1.4,
    })
except ValidationError as exc:
    for error in exc.errors():
        print(error)
```

Each error includes a location (`loc`), a human-readable message (`msg`), and an error category (`type`). The location may be a field name or a nested path such as `("items", 0, "name")`.

A compact formatter can turn these records into repair-oriented diagnostics:

```python
# diagnostics.py
from collections.abc import Iterable
from pydantic import ValidationError


def format_validation_errors(exc: ValidationError) -> list[str]:
    messages: list[str] = []

    for error in exc.errors():
        path = ".".join(str(part) for part in error["loc"]) or "<root>"
        message = error["msg"]
        messages.append(f"{path}: {message}")

    return messages
```

For the invalid example, the output will identify issues similar to:

```text
priority: Input should be 'low', 'medium' or 'high'
tags: Input should be a valid list
confidence: Input should be less than or equal to 1
```

The exact wording is supplied by the installed Pydantic version, so application code should rely on the structured error fields rather than matching message text exactly.

Parsing failures should use a parallel format:

```python
def format_json_error(exc: json.JSONDecodeError) -> list[str]:
    return [
        f"JSON syntax at line {exc.lineno}, column {exc.colno}: {exc.msg}"
    ]
```

These diagnostics are useful to people and to a later repair stage. They identify where the response failed and what kind of correction is needed, rather than merely printing “invalid output.”

## Section 5: Choosing a Safe Pipeline Boundary

The pipeline boundary should return either a validated schema instance or a failure containing diagnostics. It should never return a partially trusted dictionary.

A small result type makes that boundary explicit:

```python
# pipeline.py
import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from diagnostics import format_json_error, format_validation_errors
from schema import Extraction


@dataclass
class ValidationResult:
    value: Extraction | None
    errors: list[str]

    @property
    def ok(self) -> bool:
        return self.value is not None


def validate_response(raw_response: str) -> ValidationResult:
    try:
        parsed: Any = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        return ValidationResult(
            value=None,
            errors=format_json_error(exc),
        )

    try:
        value = Extraction.model_validate(parsed)
    except ValidationError as exc:
        return ValidationResult(
            value=None,
            errors=format_validation_errors(exc),
        )

    return ValidationResult(value=value, errors=[])
```

The function has a clear contract:

- JSON syntax failure returns `value=None` and parser diagnostics.
- Schema failure returns `value=None` and field diagnostics.
- Success returns an `Extraction` instance and no errors.

The `ok` property is convenient for the CLI, but the important safety property is that callers must explicitly handle the failure case before accessing validated data.

This boundary also makes later repair possible. A repair loop can call `validate_response` for every candidate response, use its errors to produce a repair request, and stop only when `value` is present. Validation remains authoritative; the model never decides whether its own output is acceptable.

## Build-Along: Create the Offline CLI Validator

This build-along takes less than 20 minutes. You will create the initial artifact that Lesson 2 extends.

### Step 1: Create the project

Create this structure:

```text
structured-output-demo/
├── requirements.txt
├── schema.py
├── diagnostics.py
├── pipeline.py
├── cli.py
└── fixtures/
    ├── valid.json
    ├── invalid_schema.json
    └── malformed.json
```

Create `requirements.txt`:

```text
pydantic>=2.0,<3.0
```

Create and activate a virtual environment, then install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

Expected result: the installation completes without an error, and `python --version` reports Python 3.12.x.

### Step 2: Add the schema

Create `schema.py` with the `Extraction` model from Section 3.

Create `fixtures/valid.json`:

```json
{
  "title": "Replace air filter",
  "priority": "high",
  "tags": ["maintenance", "hvac"],
  "confidence": 0.96
}
```

Run a quick import check:

```bash
python -c "from schema import Extraction; print('schema loaded')"
```

Expected output:

```text
schema loaded
```

### Step 3: Add diagnostics and the validation pipeline

Create `diagnostics.py` with `format_validation_errors` and `format_json_error`.

Create `pipeline.py` with `ValidationResult` and `validate_response`.

Add the two remaining fixtures.

`fixtures/invalid_schema.json`:

```json
{
  "title": "Replace air filter",
  "priority": "urgent",
  "tags": "maintenance",
  "confidence": 1.4
}
```

`fixtures/malformed.json`:

```text
{"title": "Replace air filter", "priority": "high"
```

Run this direct validation check:

```bash
python - <<'PY'
from pathlib import Path
from pipeline import validate_response

result = validate_response(Path("fixtures/invalid_schema.json").read_text())
print("ok:", result.ok)
print("\n".join(result.errors))
PY
```

Expected output includes:

```text
ok: False
priority: Input should be 'low', 'medium' or 'high'
tags: Input should be a valid list
confidence: Input should be less than or equal to 1
```

### Step 4: Add the CLI

Create `cli.py`:

```python
import argparse
from pathlib import Path

from pipeline import validate_response


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()

    raw_response = args.fixture.read_text(encoding="utf-8")
    result = validate_response(raw_response)

    if result.ok:
        print("PASS: response matches the schema")
        print(result.value.model_dump_json(indent=2))
        return 0

    print("FAIL: response was rejected")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Test a valid response:

```bash
python cli.py fixtures/valid.json
```

Expected output starts with:

```text
PASS: response matches the schema
```

Test the schema-invalid response:

```bash
python cli.py fixtures/invalid_schema.json
```

Expected output starts with:

```text
FAIL: response was rejected
```

and lists the invalid fields.

Test malformed JSON:

```bash
python cli.py fixtures/malformed.json
```

Expected output identifies a JSON syntax error rather than a missing or invalid field.

**Artifact carried into Lesson 2:** this project’s `schema.py`, `diagnostics.py`, `pipeline.py`, `cli.py`, and response fixtures form the initial offline validator. Lesson 2 will preserve this validation path and wrap it in a bounded repair loop.
