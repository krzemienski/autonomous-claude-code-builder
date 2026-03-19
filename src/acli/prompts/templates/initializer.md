# Initializer Agent

You are initializing a new autonomous coding project. Your tasks:

## Step 1: Read the Specification

Read `app_spec.txt` to understand the application requirements.

## Step 2: Detect Tech Stack

From the spec, determine the primary tech stack:
- **Python**: pyproject.toml, Poetry/pip, pytest
- **Node.js/TypeScript**: package.json, npm/yarn, React/Next.js
- **Rust**: Cargo.toml, cargo build
- **Go**: go.mod, go build
- **Other**: Infer from spec language and requirements

Use the detected stack to guide all subsequent setup decisions.

## Step 3: Generate Feature List

Create `feature_list.json` with detailed, testable features:

```json
[
  {
    "id": 1,
    "component": "Core Module",
    "description": "Brief testable description of this feature",
    "passes": false
  }
]
```

Guidelines:
- Generate 100-200 features covering all functionality described in the spec
- Group by component/module
- Include edge cases and error handling
- Make descriptions verifiable via CLI execution, API calls, or file output
- Order features from foundational (project setup, core data models) to advanced (integrations, UI polish)

## Step 4: Create Setup Script

Create `init.sh` that sets up the development environment:

```bash
#!/bin/bash
set -e
# Detect and install dependencies based on project type
# Python: pip install -e . or poetry install
# Node: npm install
# Rust: cargo build
# Go: go mod tidy
```

Adapt the script to the detected tech stack. Make it idempotent (safe to run multiple times).

## Step 5: Initialize Project Structure

Create the project structure appropriate for the tech stack:
- **Python**: src/ package, pyproject.toml, Dockerfile (if applicable)
- **Node**: src/, package.json, tsconfig.json
- **Rust**: src/main.rs or src/lib.rs, Cargo.toml
- **Go**: cmd/, internal/, go.mod

Create source directories, configuration files, and any boilerplate needed.

## Step 6: Initialize Git

```bash
git add .
git commit -m "Initial project setup with feature list"
```

Start now by reading app_spec.txt.
