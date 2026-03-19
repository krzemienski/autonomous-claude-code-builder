"""
Specification Enhancement Engine
================================

Uses Claude API with structured outputs to transform
plain English descriptions into structured specifications.
"""

import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from .schemas import (
    ProjectSpec,
    TechStack,
    EnhancementResult,
)
from .validator import validate_spec, generate_clarifications


# System prompt for spec extraction
EXTRACTION_SYSTEM_PROMPT = """You are an expert software architect. Extract structured specifications from user descriptions.

Rules:
1. Identify all features mentioned or implied
2. Generate specific, testable acceptance criteria
3. Mark [AMBIGUOUS] for unclear terms
4. Infer reasonable defaults for tech stack if not specified
5. Create proper user stories (As a [WHO], I want [WHAT] so that [WHY])
6. Estimate effort based on complexity

Output must match the JSON schema exactly."""


EXTRACTION_USER_TEMPLATE = """Convert this project description into a structured specification:

---
{description}
---

Extract:
1. Project name and description
2. Tech stack (language, framework, database, etc.)
3. Features with requirements and acceptance criteria
4. Non-functional constraints (performance, security, etc.)

Be thorough - generate at least 3 acceptance criteria per requirement."""


async def call_claude_api(
    system_prompt: str,
    user_prompt: str,
    response_schema: dict[str, Any],
    model: str = "claude-sonnet-4-6",
) -> dict[str, Any]:
    """
    Call Claude API with structured output.

    Uses the beta structured outputs endpoint for guaranteed schema compliance.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "structured-outputs-2025-11-13",
        "content-type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": 8192,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "output_format": {
            "type": "json_schema",
            "schema": response_schema,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()

        data = response.json()
        content = data["content"][0]["text"]
        return json.loads(content)


def get_project_spec_schema() -> dict[str, Any]:
    """Get JSON schema for ProjectSpec."""
    return ProjectSpec.model_json_schema()


async def enhance_spec(
    description: str,
    model: str = "claude-sonnet-4-6",
) -> EnhancementResult:
    """
    Enhance plain-text description into structured specification.

    Args:
        description: Plain English project description
        model: Claude model to use

    Returns:
        EnhancementResult with spec, score, and clarifications
    """
    # Call Claude API with structured output
    user_prompt = EXTRACTION_USER_TEMPLATE.format(description=description)
    schema = get_project_spec_schema()

    try:
        result = await call_claude_api(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=schema,
            model=model,
        )

        # Parse into Pydantic model
        spec = ProjectSpec.model_validate(result)

    except ValidationError:
        # Fallback: create minimal spec
        spec = ProjectSpec(
            name="Untitled Project",
            description=description[:500],
            tech_stack=TechStack(language="TypeScript", framework="React"),
            features=[],
        )

    # Validate and score
    score, issues = validate_spec(spec)
    clarifications = generate_clarifications(spec, issues)

    # Detect ambiguities in original text
    ambiguities = detect_ambiguities(description)

    return EnhancementResult(
        spec=spec,
        completeness_score=score,
        clarifications_needed=clarifications,
        ambiguities=ambiguities,
        warnings=issues,
    )


def detect_ambiguities(text: str) -> list[str]:
    """Detect ambiguous terms in text."""
    vague_patterns = {
        "fast": "What response time is acceptable?",
        "simple": "What level of complexity is acceptable?",
        "easy to use": "What UX patterns should be followed?",
        "scalable": "What scale is expected (users, data)?",
        "secure": "What security requirements apply?",
        "robust": "What error handling is needed?",
        "modern": "Which specific technologies?",
    }

    ambiguities = []
    text_lower = text.lower()

    for term, question in vague_patterns.items():
        if term in text_lower:
            ambiguities.append(f"'{term}' - {question}")

    return ambiguities


async def refine_spec_with_answers(
    spec: ProjectSpec,
    answers: dict[str, str],
    model: str = "claude-sonnet-4-6",
) -> EnhancementResult:
    """
    Refine specification with clarification answers.

    Args:
        spec: Current specification
        answers: Dict mapping question fields to answers
        model: Claude model

    Returns:
        Updated EnhancementResult
    """
    # Build refinement prompt
    prompt = f"""Refine this specification with the additional information provided.

Current Spec:
{spec.model_dump_json(indent=2)}

Additional Information:
{json.dumps(answers, indent=2)}

Update the specification to incorporate this information.
Keep all existing details, only add/modify based on new answers."""

    try:
        result = await call_claude_api(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_schema=get_project_spec_schema(),
            model=model,
        )

        refined_spec = ProjectSpec.model_validate(result)

    except Exception:
        # Keep original spec on error
        refined_spec = spec

    score, issues = validate_spec(refined_spec)
    clarifications = generate_clarifications(refined_spec, issues)

    return EnhancementResult(
        spec=refined_spec,
        completeness_score=score,
        clarifications_needed=clarifications,
        ambiguities=[],
        warnings=issues,
    )
