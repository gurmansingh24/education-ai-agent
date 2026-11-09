from pathlib import Path

# Project directories
ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT / "agent"
PROMPT_DIR = AGENT_DIR / "prompts"
COURSE_DIR = ROOT / "course"
BUILD_DIR = ROOT / "build"
OUTPUT_DIR = ROOT / "output"

# Course configuration
TOPIC = "Structured Outputs"

CAPSTONE = (
    "A schema-validated pipeline with a bounded repair loop."
)

PYTHON_VERSION = "3.12"

LESSON_COUNT = 2

BREAKING_POINTS = [
    'Learners assume telling a model to "return JSON" guarantees usable structured output.',
    "Learners confuse valid JSON syntax with data that satisfies an application schema.",
    "Learners do not know how to turn validation failures into useful repair instructions.",
    "Learners may retry indefinitely or silently accept malformed output.",
]

CHECKPOINTS = [
    "Explain the difference between JSON parsing and schema validation.",
    "Define and use an explicit schema for model output.",
    "Display actionable validation errors when model output is invalid.",
    "Convert validation errors into a repair request.",
    "Retry with a fixed maximum number of repair attempts.",
    "Return either validated data or an explicit terminal failure.",
]