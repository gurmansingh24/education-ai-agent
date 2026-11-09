# Education AI Agent

**AI-Powered Course Generation and Structured Output Validation**

A Python-based AI agent designed to generate educational course content and interactive coding exercises using the OpenAI API. The project demonstrates automated content generation, structured output validation, and error handling.

## Project Overview

This project explores how AI can be used to automate the development of educational materials.

The agent uses a multi-stage workflow to plan course content, generate lessons and coding exercises, and review the generated material.

The included course focuses on structured outputs and teaches developers how to build reliable AI pipelines.

## Technologies Used

- **Python 3.12** — Core programming language
- **OpenAI API** — AI-powered content generation
- **Pydantic 2.x** — Schema validation
- **JSON** — Structured data representation
- **Git and GitHub** — Version control

## Key Features

### 1. AI-Powered Course Generation

Uses AI to generate educational content through specialized stages:

- Course planning
- Lesson generation
- Coding exercise generation
- Content review

### 2. Structured Output Validation

Demonstrates techniques for validating AI-generated data against predefined schemas.

- Detects malformed JSON
- Identifies schema-validation errors
- Produces useful validation diagnostics

### 3. Bounded Repair Loop

The generated learning exercises demonstrate how to handle invalid model responses.

- Detect invalid outputs
- Apply constrained repair attempts
- Revalidate repaired responses
- Stop after a fixed retry budget

### 4. Offline Learning Exercises

Generated exercises use cached model responses so learners can complete them without an active API connection.

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

**1. Clone the repository**

```bash
git clone https://github.com/gurmansingh24/education-ai-agent.git
cd education-ai-agent
```

**2. Create a virtual environment**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

## Learning Outcomes

This project demonstrates experience with:

- Python software development
- AI-assisted content generation
- Prompt engineering
- JSON schema validation
- Error handling and debugging
- Automated validation workflows

## Author

Developed as an AI engineering take-home project for EducationPals.