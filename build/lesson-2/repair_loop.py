from dataclasses import dataclass

from model_adapter import FixtureModel
from pipeline import ValidationResult, validate_response
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
    validation: ValidationResult,
) -> str:
    error_lines = "\n".join(
        f"- {error}" for error in validation.errors
    )

    if validation.failure_kind == "json":
        failure_description = "The response was not valid JSON."
    else:
        failure_description = (
            "The JSON was valid, but it did not match the application schema."
        )

    return (
        "Repair the response so it matches the application schema.\n\n"
        f"{failure_description}\n\n"
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

    total_attempts = max_repairs + 1
    raw_response = model.initial_response()
    last_errors: list[str] = []

    for attempt_number in range(1, total_attempts + 1):
        print(f"ATTEMPT {attempt_number}/{total_attempts}")

        validation = validate_response(raw_response)

        if validation.ok:
            print("PASS: response matches the schema")
            return RepairResult(
                value=validation.value,
                errors=[],
                attempts=attempt_number,
            )

        last_errors = validation.errors

        if validation.failure_kind == "json":
            print("FAIL: JSON parsing failed")
        else:
            print("FAIL: schema validation failed")

        for error in last_errors:
            print(f"- {error}")

        if attempt_number == total_attempts:
            break

        repair_number = attempt_number
        print(f"REPAIR {repair_number}/{max_repairs}")

        request = build_repair_request(raw_response, validation)
        raw_response = model.repair_response(request)

    return RepairResult(
        value=None,
        errors=last_errors,
        attempts=total_attempts,
    )
