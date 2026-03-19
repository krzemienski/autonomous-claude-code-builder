"""
Specification Validator
=======================

Validates spec completeness and scores quality.
"""

from dataclasses import dataclass

from .schemas import ClarificationQuestion, ProjectSpec


@dataclass
class ValidationRule:
    """A single validation rule."""
    name: str
    weight: float  # 0-1, contribution to score
    check: callable  # (ProjectSpec) -> (bool, str)


def check_has_features(spec: ProjectSpec) -> tuple[bool, str]:
    """Check spec has at least 2 features."""
    if len(spec.features) >= 2:
        return True, ""
    return False, "Spec should have at least 2 features"


def check_has_requirements(spec: ProjectSpec) -> tuple[bool, str]:
    """Check features have requirements."""
    for feat in spec.features:
        if len(feat.requirements) < 1:
            return False, f"Feature '{feat.name}' has no requirements"
    return True, ""


def check_has_acceptance_criteria(spec: ProjectSpec) -> tuple[bool, str]:
    """Check requirements have acceptance criteria."""
    for feat in spec.features:
        for req in feat.requirements:
            if len(req.acceptance_criteria) < 1:
                return False, f"Requirement '{req.description[:30]}...' has no acceptance criteria"
    return True, ""


def check_tech_stack_complete(spec: ProjectSpec) -> tuple[bool, str]:
    """Check tech stack is specified."""
    ts = spec.tech_stack
    if not ts.language:
        return False, "Programming language not specified"
    if not ts.framework:
        return False, "Framework not specified"
    return True, ""


def check_user_stories(spec: ProjectSpec) -> tuple[bool, str]:
    """Check features have user stories."""
    for feat in spec.features:
        if not feat.user_story or "want" not in feat.user_story.lower():
            return False, (
                f"Feature '{feat.name}' needs proper user story"
                " (As a... I want... so that...)"
            )
    return True, ""


def check_no_vague_terms(spec: ProjectSpec) -> tuple[bool, str]:
    """Check for vague terms that need clarification."""
    vague_terms = ["fast", "simple", "easy", "robust", "scalable", "good", "nice", "better"]

    text = spec.description.lower()
    for feat in spec.features:
        text += " " + feat.description.lower()

    found = [term for term in vague_terms if term in text]
    if found:
        return False, f"Vague terms need clarification: {found}"
    return True, ""


# Validation rules with weights
VALIDATION_RULES: list[ValidationRule] = [
    ValidationRule("has_features", 0.2, check_has_features),
    ValidationRule("has_requirements", 0.2, check_has_requirements),
    ValidationRule("has_acceptance_criteria", 0.2, check_has_acceptance_criteria),
    ValidationRule("tech_stack_complete", 0.15, check_tech_stack_complete),
    ValidationRule("user_stories", 0.15, check_user_stories),
    ValidationRule("no_vague_terms", 0.1, check_no_vague_terms),
]


def validate_spec(spec: ProjectSpec) -> tuple[float, list[str]]:
    """
    Validate specification and return completeness score.

    Returns:
        (score 0-100, list of issues)
    """
    score = 0.0
    issues = []

    for rule in VALIDATION_RULES:
        passed, message = rule.check(spec)
        if passed:
            score += rule.weight * 100
        else:
            issues.append(message)

    return round(score, 1), issues


def generate_clarifications(
    spec: ProjectSpec,
    issues: list[str],
) -> list[ClarificationQuestion]:
    """Generate clarification questions from validation issues."""
    questions = []

    # Map issues to clarification questions
    for issue in issues:
        if "vague terms" in issue.lower():
            questions.append(ClarificationQuestion(
                field="description",
                question=(
                    "Some terms need more specificity. "
                    "What does 'fast' mean in terms of "
                    "response time (e.g., <100ms, <500ms)?"
                ),
                suggestions=["<100ms", "<500ms", "<1s", "<2s"],
                required=False,
            ))

        if "programming language" in issue.lower():
            questions.append(ClarificationQuestion(
                field="tech_stack.language",
                question="Which programming language should be used?",
                suggestions=["TypeScript", "Python", "JavaScript", "Go", "Rust"],
                required=True,
            ))

        if "framework" in issue.lower():
            questions.append(ClarificationQuestion(
                field="tech_stack.framework",
                question="Which framework would you like to use?",
                suggestions=["React", "Next.js", "Vue", "FastAPI", "Express"],
                required=True,
            ))

        if "user story" in issue.lower():
            questions.append(ClarificationQuestion(
                field="features.user_story",
                question="Who is the target user and what problem are they solving?",
                suggestions=[],
                required=True,
            ))

        if "acceptance criteria" in issue.lower():
            questions.append(ClarificationQuestion(
                field="requirements.acceptance_criteria",
                question="What testable conditions indicate this feature is complete?",
                suggestions=[],
                required=True,
            ))

    return questions


def get_completeness_threshold() -> float:
    """Get minimum score for spec to be considered complete."""
    return 85.0


def is_spec_complete(score: float) -> bool:
    """Check if spec meets completeness threshold."""
    return score >= get_completeness_threshold()
