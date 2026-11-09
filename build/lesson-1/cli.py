import argparse
import json
from pathlib import Path

from pipeline import validate_response


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse and schema-validate cached model responses."
    )
    parser.add_argument(
        "fixtures",
        nargs="+",
        help="One or more cached response files to validate",
    )
    args = parser.parse_args()

    for fixture_name in args.fixtures:
        path = Path(fixture_name)

        print(f"\nCHECKING: {path.name}")

        raw_response = path.read_text(encoding="utf-8")
        result = validate_response(raw_response)

        if result.ok:
            print("PASS: response matches the schema")
            print("VALIDATED RESULT:")
            print(json.dumps(result.value.model_dump(), indent=2))
        else:
            print(f"FAIL: {result.failure_kind}")
            for error in result.errors:
                print(f"- {error}")


if __name__ == "__main__":
    main()