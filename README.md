# Structured Outputs

A ~90-minute, two-lesson course for developers whose AI pipelines break when a model returns prose or malformed data instead of the expected JSON.

## Capstone

The learner finishes with a schema-validated structured-output pipeline with a bounded repair loop. The final CLI distinguishes malformed JSON from schema-invalid JSON, reports useful validation errors, repairs invalid responses using cached model outputs, revalidates every repair, and stops after a fixed repair budget.

## Breaking Points

1. Treating valid JSON as equivalent to valid application data.
2. Losing the distinction between JSON parsing failures and schema-validation failures.
3. Trusting a model's repaired response without validating it again.
4. Building a repair loop without a bounded retry policy.

## Checkpoints

### Lesson 1 — Parse It, Then Prove It Matches the Contract

By the end of Lesson 1, the learner can:

- Define a strict application schema.
- Parse cached model responses.
- Distinguish JSON syntax errors from schema-validation errors.
- Print actionable validation diagnostics.

Build artifact: an offline CLI validator.

### Lesson 2 — Repair, Revalidate, and Stop

By the end of Lesson 2, the learner can:

- Turn validation errors into a constrained repair request.
- Feed cached repair responses through the same validator.
- Revalidate every attempted repair.
- Stop after a bounded number of repair attempts.

Build artifact: Lesson 1's validator extended into a bounded repair pipeline.

## Requirements

- Python 3.12
- Pydantic 2.x
- No API key is required to run the learner build-alongs.
- Build-alongs replay cached fixture/model responses and run offline.

## Setup

From the project root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt