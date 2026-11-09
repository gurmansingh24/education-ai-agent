# Lesson 2: Repair Invalid Output Without Retrying Forever

## Checkpoints

After this lesson, you will be able to:

- Convert validation diagnostics into a targeted repair request.
- Separate model generation from parsing and validation.
- Use fixture-backed model responses for offline execution.
- Retry with a fixed maximum number of repair attempts.
- Log every attempt and its validation result.
- Return either validated data or an explicit terminal failure.

## Section 1: Validation Errors as Repair Instructions

A validation error is more useful when it becomes a specific correction instruction. The repair stage should receive enough context to understand both the candidate output and the reason it failed.

Suppose the candidate response is:

```json
{
  "title": "Replace air filter",
  "priority": "urgent",
  "tags": "maintenance",
  "confidence": 1.4
}
```

The validator might produce:

```text
priority: Input should be 'low', 'medium' or 'high'
tags: Input should be a valid list
confidence: Input should be less than or equal to 1
```

A generic request such as “try again” loses useful information. A targeted repair request can say:

```text
Repair the JSON response so it matches the application schema.

Original response:
{"title":"Replace air filter","priority":"urgent","tags":"maintenance","confidence":1.4}

Validation errors:
- priority: Input should be 'low', 'medium' or 'high'
- tags: Input should be a valid list
- confidence: Input should be less than or equal to 1

Return only the corrected JSON object. Do not include Markdown or explanatory prose.
```

This does not guarantee that the next response will be correct. It gives the model actionable information while leaving validation as the authority.

A repair request should include:

1. The original response, or a safely bounded representation of it.
2. The complete current diagnostics.
3. The output requirement, including “JSON only” if that is appropriate.
4. The fact that the response must match the application schema.

For malformed JSON, the request should include the parser location:

```text
JSON syntax at line 1, column 54: Expecting ',' delimiter
```

For nested data, preserve the path. A diagnostic such as `items.0.name` tells the repair stage which element and field need correction.

Keep the repair request deterministic in your application code. Do not rely on a model remembering an earlier response or silently infer which fields failed. Each repair attempt should be constructed from the current candidate and current validation result.

## Section 2: Separating Generation from Validation

The model adapter is responsible for obtaining response text. It is not responsible for deciding whether that text is valid.

Define a small adapter boundary:

```python
# model_adapter.py
from pathlib import Path


class FixtureModel:
    def __init__(self, response_paths: list[Path]) -> None:
        if not response_paths:
            raise ValueError("at least one response fixture is required")

        self._responses = [
            path.read_text(encoding="utf-8") for path in response_paths
        ]
        self._index = 0

    def initial_response(self) -> str:
        return self._next_response()

    def repair_response(self, repair_request: str) -> str:
        print("REPAIR REQUEST:")
        print(repair_request)
        return self._next_response()

    def _next_response(self) -> str:
        if self._index >= len(self._responses):
            raise RuntimeError("fixture model has no response left")

        response = self._responses[self._index]
        self._index += 1
        return response
```

This adapter simulates a model offline. The first fixture represents the initial generation. Each later fixture represents a response to a repair request. The adapter prints the request so the build remains observable, but it does not inspect or modify the request.

In production, the same boundary could call an LLM SDK. The rest of the pipeline should not need to know which provider is used. More importantly, the adapter should return raw text. It should not call `json.loads` or `Extraction.model_validate`.

Keeping responsibilities separate gives the pipeline a trustworthy ordering:

```text
model adapter -> raw text -> JSON parser -> Pydantic validator -> application
```

The adapter can fail because a provider is unavailable. The parser can fail because the text is malformed. Pydantic can fail because the structure is wrong. These failures should remain distinguishable in logs and terminal results.

Fixture-backed responses also make tests and demonstrations reproducible. You can demonstrate a successful repair and exhausted retries without network access, credentials, or nondeterministic model behavior.

## Section 3: Designing a Bounded Retry Policy

A repair loop needs a hard limit. Without one, an application can repeatedly send the same kind of repair request, increasing latency and cost while never producing valid data.

Use a parameter such as `max_repairs`:

- `max_repairs=0` means validate only the initial response.
- `max_repairs=1` permits one repair response after the initial response.
- `max_repairs=2` permits two repair responses.

The total number of candidate responses is therefore at most `1 + max_repairs`.

The loop should count attempts explicitly:

```python
for repair_number in range(max_repairs + 1):
    ...
```

On the first iteration, obtain the initial response. On later iterations, construct a repair request from the previous response and its errors, then ask the adapter for the next response.

Important rules:

- Validate every candidate, including the initial response.
- Stop immediately after a valid response.
- Do not request a repair after the limit is reached.
- Return the final diagnostics if all permitted candidates fail.
- Treat missing fixture responses as an adapter failure, not as a successful repair.

The limit should be controlled by application configuration, not by the model. A model response must never be able to request unlimited retries.

A bounded loop also gives a predictable operational budget. If a request can take up to three model calls, that fact can be reflected in timeout, cost, and user-interface expectations.

The terminal failure must be explicit. Returning `None` without context makes it difficult for callers to distinguish “no result” from “the pipeline rejected three candidates.” A result object should carry the final errors and the number of attempts.

## Section 4: Preserving Observability

A repair loop has several important events:

1. A candidate response was received.
2. JSON parsing either succeeded or failed.
3. Schema validation either succeeded or failed.
4. A repair request was generated.
5. The retry limit was reached, or validation succeeded.

Print or log these events with attempt numbers. For example:

```text
ATTEMPT 1/3
FAIL: schema validation
- priority: Input should be 'low', 'medium' or 'high'
- tags: Input should be a valid list

REPAIR 1/2
REPAIR REQUEST:
...

ATTEMPT 2/3
PASS: response matches the schema
```

Attempt numbering should be understandable to operators. One useful convention is to display the current candidate as `ATTEMPT 1/3`, where the total includes the initial response and all permitted repairs.

Do not log only the final error. The first candidate may fail because of malformed JSON, while the second may fail because of one incorrect field. Those details help diagnose prompt quality, model behavior, and fixture or adapter bugs.

At the same time, be careful with sensitive data. Real applications should apply redaction or access controls before logging raw responses and repair requests. The offline build uses small fixtures, so printing them is appropriate for visibility.

The validator remains the source of truth for status messages. The CLI should print `PASS` only after `validate_response` returns an `Extraction` instance. A model-generated statement such as “this is valid JSON” is not an observability event and must not affect control flow.

## Section 5: Defining Terminal Outcomes

The completed pipeline has two successful or unsuccessful terminal states.

On success, return a validated `Extraction` instance. Downstream code can safely use:

```python
result.value.title
result.value.priority
```

On failure, return an explicit object containing:

- `value=None`
- the final diagnostics
- the number of candidate attempts
- optionally, the last raw response for controlled debugging

A simple result type is:

```python
from dataclasses import dataclass
from schema import Extraction


@dataclass
class RepairResult:
    value: Extraction | None
    errors: list[str]
    attempts: int

    @property
    def ok(self) -> bool:
        return self.value is not None
```

The terminal failure should be visible and actionable:

```text
TERMINAL FAILURE after 3 attempts
- confidence: Input should be less than or equal to 1
```

The caller can then choose an appropriate policy, such as returning an error to the user, sending the item to a review queue, or recording it for later analysis. It should not receive an unvalidated dictionary as a fallback.

This outcome model also prevents an important ambiguity: “the model did not produce valid data within the configured budget” is different from “the application has valid data.” The distinction must remain present in both code and output.

The repair loop therefore has a strict contract:

```text
validated Extraction
        OR
explicit RepairResult failure
```

There is no third state in which malformed or schema-invalid data is accepted for convenience.

## Build-Along: Extend the Validator with an Offline Repair Loop

This build-along takes less than 20 minutes. It modifies the Lesson 1 project; do not create a replacement project.

### Step 1: Add response fixtures

Keep the Lesson 1 fixtures unchanged. Add these files:

`fixtures/repaired.json`:

```json
{
  "title": "Replace air filter",
  "priority": "high",
  "tags": ["maintenance"],
  "confidence": 0.91
}
```

`fixtures/still_invalid.json`:

```json
{
  "title": "Replace air filter",
  "priority": "urgent",
  "tags": "maintenance",
  "confidence": 1.4
}
```

The fixture format is unchanged: each file contains one model-like response, either valid JSON or malformed response text.

### Step 2: Create the fixture-backed adapter

Create `model_adapter.py` with the `FixtureModel` class from Section 2.

Check the adapter:

```bash
python - <<'PY'
from pathlib import Path
from model_adapter import FixtureModel

model = FixtureModel([
    Path("fixtures/invalid_schema.json"),
    Path("fixtures/repaired.json"),
])
print(model.initial_response().splitlines()[0])
print(model.repair_response("repair this").splitlines()[0])
PY
```

Expected output includes:

```text
{
REPAIR REQUEST:
repair this
{
```

The two responses are being read from fixtures without a network call.

### Step 3: Create the bounded repair loop

Create `repair_loop.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from model_adapter import FixtureModel
from pipeline import validate_response
from schema import Extraction


@dataclass
class RepairResult:
    value: Extraction | None
    errors: list[str]
    attempts: int

    @property
    def ok(self) -> bool:
        return self.value is not None


def build_repair_request(
    raw_response: str,
    errors: list[str],
) -> str:
    error_lines = "\n".join(f"- {error}" for error in errors)

    return (
        "Repair the response so it matches the application schema.\n\n"
        f"Original response:\n{raw_response}\n\n"
        f"Validation errors:\n{error_lines}\n\n"
        "Return only the corrected JSON object. "
        "Do not include Markdown or explanatory prose."
    )


def run_repair_loop(
    model: FixtureModel,
    max_repairs: int,
) -> RepairResult:
    if max_repairs < 0:
        raise ValueError("max_repairs must be non-negative")

    raw_response = model.initial_response()
    last_errors: list[str] = []

    for attempt_number in range(1, max_repairs + 2):
        print(f"ATTEMPT {attempt_number}/{max_repairs + 1}")

        validation = validate_response(raw_response)

        if validation.ok:
            print("PASS: response matches the schema")
            return RepairResult(
                value=validation.value,
                errors=[],
                attempts=attempt_number,
            )

        last_errors = validation.errors
        print("FAIL: response was rejected")
        for error in last_errors:
            print(f"- {error}")

        if attempt_number == max_repairs + 1:
            break

        repair_number = attempt_number
        print(f"REPAIR {repair_number}/{max_repairs}")
        request = build_repair_request(raw_response, last_errors)
        raw_response = model.repair_response(request)

    return RepairResult(
        value=None,
        errors=last_errors,
        attempts=max_repairs + 1,
    )
```

Run a direct successful-repair check:

```bash
python - <<'PY'
from pathlib import Path
from model_adapter import FixtureModel
from repair_loop import run_repair_loop

result = run_repair_loop(
    FixtureModel([
        Path("fixtures/invalid_schema.json"),
        Path("fixtures/repaired.json"),
    ]),
    max_repairs=1,
)
print(f"result.ok={result.ok}, attempts={result.attempts}")
PY
```

Expected output shows a failed first attempt, a repair request, then:

```text
PASS: response matches the schema
result.ok=True, attempts=2
```

### Step 4: Extend the CLI

Modify `cli.py` so it accepts one or more response fixtures and a repair limit:

```python
import argparse
from pathlib import Path

from model_adapter import FixtureModel
from repair_loop import run_repair_loop


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixtures", nargs="+", type=Path)
    parser.add_argument("--max-repairs", type=int, default=2)
    args = parser.parse_args()

    result = run_repair_loop(
        FixtureModel(args.fixtures),
        max_repairs=args.max_repairs,
    )

    if result.ok:
        print("FINAL RESULT:")
        print(result.value.model_dump_json(indent=2))
        return 0

    print(f"TERMINAL FAILURE after {result.attempts} attempts")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Test successful repair:

```bash
python cli.py fixtures/invalid_schema.json fixtures/repaired.json --max-repairs 1
```

Expected output includes:

```text
ATTEMPT 1/2
FAIL: response was rejected
REPAIR 1/1
ATTEMPT 2/2
PASS: response matches the schema
FINAL RESULT:
```

Test exhausted retries:

```bash
python cli.py fixtures/invalid_schema.json fixtures/still_invalid.json --max-repairs 1
```

Expected output ends with:

```text
TERMINAL FAILURE after 2 attempts
```

The final artifact satisfies the capstone: it reads offline model-like responses, parses JSON, validates against an explicit Pydantic schema, displays actionable errors, generates a repair request, retries only up to a fixed maximum, logs each attempt, and returns either validated data or an explicit terminal failure.
