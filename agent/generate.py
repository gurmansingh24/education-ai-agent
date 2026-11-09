import os
import re
from pathlib import Path

from openai import OpenAI

from config import (
    ROOT,
    PROMPT_DIR,
    COURSE_DIR,
    BUILD_DIR,
    OUTPUT_DIR,
    TOPIC,
    CAPSTONE,
    BREAKING_POINTS,
    CHECKPOINTS,
)

MODEL = "gpt-5.6-luna"


def read_prompt(filename: str) -> str:
    """Load one of the agent prompt files."""
    path = PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")


def save_text(path: Path, content: str) -> None:
    """Save generated content and create parent folders if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def extract_build_files(build_text: str) -> None:
    """Extract generated fenced code blocks into build/lesson-2."""

    pattern = re.compile(
        r"(?m)^([A-Za-z0-9_./-]+\.(?:py|json|txt))\s*\n"
        r"```(?:python|json|text)?\s*\n"
        r"(.*?)"
        r"```",
        re.DOTALL,
    )

    matches = pattern.findall(build_text)

    if not matches:
        print("      ! No build files could be extracted automatically")
        return

    destination = BUILD_DIR / "lesson-2"
    destination.mkdir(parents=True, exist_ok=True)

    for filename, content in matches:
        relative_path = Path(filename)

        # The generated tree may prefix files with a demo directory.
        if len(relative_path.parts) > 1:
            relative_path = Path(*relative_path.parts[1:])

        output_path = destination / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content.rstrip() + "\n", encoding="utf-8")

        print(f"      ✓ Wrote {output_path.relative_to(ROOT)}")

def ask_model(client: OpenAI, instructions: str, user_input: str) -> str:
    """Run one stage of the generation pipeline."""
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_input,
    )

    return response.output_text


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Set it before running the course generator."
        )

    client = OpenAI()

    COURSE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Stage 1: Plan backwards from the capstone.
    print("[1/4] Planning course...")

    planner_prompt = read_prompt("planner.txt")

    planning_context = f"""
Topic: {TOPIC}

Capstone:
{CAPSTONE}

Breaking points:
{chr(10).join(f"- {point}" for point in BREAKING_POINTS)}

Required checkpoints:
{chr(10).join(f"- {checkpoint}" for checkpoint in CHECKPOINTS)}
"""

    plan = ask_model(
        client,
        planner_prompt,
        planning_context,
    )

    save_text(OUTPUT_DIR / "course-plan.md", plan)

    print("      ✓ Course plan generated")

    # Stage 2: Generate the lesson content from the approved plan.
    print("[2/4] Generating lessons...")

    course_prompt = read_prompt("course_writer.txt")

    course_input = f"""
Use the following approved course plan.

--- COURSE PLAN ---

{plan}

--- END COURSE PLAN ---
"""

    course = ask_model(
        client,
        course_prompt,
        course_input,
    )

    save_text(COURSE_DIR / "generated-course.md", course)

    print("      ✓ Course generated")

    # Stage 3: Generate build-along code and fixtures.
    print("[3/4] Generating build-alongs...")

    build_prompt = read_prompt("build_writer.txt")

    build_input = f"""
Required capstone:
{CAPSTONE}

Approved course plan:

--- COURSE PLAN ---
{plan}
--- END COURSE PLAN ---

Generated course:

--- COURSE ---
{course}
--- END COURSE ---
"""

    build = ask_model(
        client,
        build_prompt,
        build_input,
    )

    save_text(OUTPUT_DIR / "generated-build.md", build)

    print("      ✓ Build-alongs generated")
    print("      Extracting runnable build files...")
    extract_build_files(build)

    # Stage 4: Have a separate reviewer inspect the result.
    print("[4/4] Reviewing generated course...")

    reviewer_prompt = read_prompt("reviewer.txt")

    review_input = f"""
Required capstone:
{CAPSTONE}

Course plan:

--- COURSE PLAN ---
{plan}
--- END COURSE PLAN ---

Course:

--- COURSE ---
{course}
--- END COURSE ---

Generated build:

--- BUILD ---
{build}
--- END BUILD ---
"""

    review = ask_model(
        client,
        reviewer_prompt,
        review_input,
    )

    save_text(OUTPUT_DIR / "review.md", review)

    print("      ✓ Review generated")

    print()
    print("Generation complete.")
    print("Created:")
    print("  output/course-plan.md")
    print("  course/generated-course.md")
    print("  output/generated-build.md")
    print("  output/review.md")


if __name__ == "__main__":
    main()