# Initializer Agent

You are initializing a new autonomous coding project. Your tasks:

## Step 1: Read the Specification

Read `app_spec.txt` to understand the application requirements.

## Step 2: Generate Feature List

Create `feature_list.json` with detailed test cases:

```json
[
  {
    "id": 1,
    "component": "Login Component",
    "description": "Email input field accepts valid email format",
    "passes": false
  },
  ...
]
```

Guidelines:
- Generate ~200 features covering all functionality
- Group by component
- Include edge cases and error handling
- Make descriptions testable via browser automation

## Step 3: Create Setup Script

Create `init.sh`:
```bash
#!/bin/bash
npm install
npm run dev &
```

## Step 4: Initialize Project Structure

Create necessary files:
- package.json with dependencies
- Source directories (src/, public/)
- Configuration files

## Step 5: Initialize Git

```bash
git init
git add .
git commit -m "Initial project setup"
```

Start now by reading app_spec.txt.
