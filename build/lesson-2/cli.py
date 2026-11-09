import argparse
from pathlib import Path

from model_adapter import FixtureModel
from repair_loop import run_repair_loop


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate fixture-backed model responses with bounded repair."
    )
    parser.add_argument(
        "fixtures",
        nargs="+",
        type=Path,
        help=(
            "Initial response followed by one fixture for each permitted repair"
        ),
    )
    parser.add_argument(
        "--max-repairs",
        type=int,
        default=2,
        help="Maximum number of repair responses to request",
    )
    args = parser.parse_args()

    try:
        result = run_repair_loop(
            FixtureModel(args.fixtures),
            max_repairs=args.max_repairs,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"FAIL: pipeline could not run: {exc}")
        return 2

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
