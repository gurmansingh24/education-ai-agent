# Education AI Agent

### AI-Powered Educational Course Generator

A Python-based AI agent that uses the OpenAI API to generate structured educational content, programming lessons, and interactive coding exercises.

Developed as an AI engineering take-home project for EducationPals.

## Project Overview

The Education AI Agent automates the creation of educational courses through a multi-stage AI workflow.

The project includes separate prompts for course planning, lesson writing, coding exercise generation, and content review.

The included example is a two-lesson course on building reliable structured-output pipelines.

## Technologies Used

- Python 3.12
- OpenAI API
- Pydantic 2.x
- JSON
- Git and GitHub

## Key Features

**AI-Powered Course Generation**
- Generates educational course plans and lesson content.
- Uses specialized prompts for different content-generation stages.
- Supports the creation of coding exercises.

**Structured Output Validation**
- Demonstrates JSON parsing and schema validation.
- Distinguishes malformed JSON from schema-invalid data.
- Provides useful validation diagnostics.

**Bounded Repair Pipeline**
- Uses validation errors to guide repair attempts.
- Revalidates repaired responses.
- Stops after a fixed number of attempts.

**Offline Coding Exercises**
- Includes cached model responses for testing.
- Allows learners to complete exercises without an API key.

## Example Generated Course

**Structured Outputs — A Two-Lesson Developer Course**

The example course teaches developers to build reliable AI pipelines.

**Lesson 1: Parse It, Then Prove It Matches the Contract**

Learners build a CLI validator that detects malformed JSON and schema-validation errors.

**Lesson 2: Repair, Revalidate, and Stop**

Learners extend the validator into a bounded repair pipeline that checks repaired outputs and enforces a retry limit.

## Project Structure

```text
education-ai-agent/
├── agent/
│   ├── config.py
│   ├── generate.py
│   └── prompts/
├── build/
│   ├── lesson-1/
│   └── lesson-2/
├── course/
│   ├── lesson-1.md
│   └── lesson-2.md
├── requirements.txt
├── README.md
└── writeup.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/gurmansingh24/education-ai-agent.git
cd education-ai-agent
```

Create a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Project

The repository contains an AI course generator in `agent/generate.py` and offline learning exercises in the `build/` directory.

The exact execution commands for these components should be checked against their implementations before running them.

## Skills Demonstrated

- Python development
- AI application development
- Prompt engineering
- API integration
- Structured data validation
- Error handling
- Automated content generation

## Author

Developed as part of the EducationPals AI Engineering take-home assignment.

## Running the AI Agent

The AI agent uses the OpenAI API to generate educational courses through a four-stage pipeline.

**1. Set your OpenAI API key**

On macOS or Linux:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Never commit your real API key to GitHub.

**2. Run the course generator**

From the project root:

```bash
python agent/generate.py
```

**3. Generated files**

After successful execution, the agent creates:

- `output/course-plan.md` — Generated course plan
- `course/generated-course.md` — Generated lesson content
- `output/generated-build.md` — Generated coding exercises
- `build/lesson-2/` — Extracted coding files
- `output/review.md` — AI-generated review

**Note:** Running the generator requires an OpenAI API key and may incur API usage charges. The included offline coding exercises do not require an API key.