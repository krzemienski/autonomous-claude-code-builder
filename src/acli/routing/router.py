"""Prompt classification into workflow types."""

import re
from pathlib import Path

from .workflows import WorkflowConfig, WorkflowType

# Source file extensions that indicate a real codebase
SOURCE_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx", ".swift", ".rs", ".go", ".java", ".kt", ".rb",
}

# Intent patterns for classification
DEBUG_PATTERNS = re.compile(
    r"\b(fix|debug|broken|crash|error|bug|fail|issue)\b", re.IGNORECASE,
)
REFACTOR_PATTERNS = re.compile(
    r"\b(refactor|migrate|convert|upgrade|modernize|rewrite)\b", re.IGNORECASE,
)
ADD_PATTERNS = re.compile(
    r"\b(add|implement|create|build|make|develop|set up|integrate)\b", re.IGNORECASE,
)

_SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", ".acli"}


class PromptRouter:
    """Classifies any user prompt into a WorkflowType with config."""

    def classify(self, prompt: str, project_dir: Path) -> WorkflowConfig:
        """Classify prompt + project state into workflow config."""
        has_xcodeproj = self._has_ios_project(project_dir)
        has_cargo = (project_dir / "Cargo.toml").exists()
        has_spec = (project_dir / "app_spec.txt").exists()
        source_count = self._count_source_files(project_dir)
        is_onboarded = (
            project_dir / ".acli" / "context" / "codebase_analysis.json"
        ).exists()

        # Priority 1: iOS project
        if has_xcodeproj:
            return WorkflowConfig(
                workflow_type=WorkflowType.IOS_APP,
                requires_onboarding=not is_onboarded and source_count > 3,
                agent_sequence=["analyst", "planner", "implementer", "validator"],
                model_tier="sonnet",
                platform="ios",
            )

        # Priority 2: CLI/Rust project
        if has_cargo:
            return WorkflowConfig(
                workflow_type=WorkflowType.CLI_TOOL,
                requires_onboarding=not is_onboarded and source_count > 3,
                agent_sequence=["planner", "implementer", "validator"],
                model_tier="sonnet",
                platform="cli",
            )

        # Priority 3: Greenfield (spec present, no significant source)
        if has_spec and source_count <= 3:
            return WorkflowConfig(
                workflow_type=WorkflowType.GREENFIELD_APP,
                requires_onboarding=False,
                agent_sequence=["planner", "implementer", "validator", "reporter"],
                model_tier="sonnet",
                platform="generic",
            )

        # Priority 4-6: Brownfield variants (significant source files)
        if source_count > 3:
            if DEBUG_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.DEBUG,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "planner", "implementer", "validator"],
                    model_tier="opus",
                    platform="generic",
                )

            if REFACTOR_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.REFACTOR,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "planner", "implementer", "validator"],
                    model_tier="opus",
                    platform="generic",
                )

            if ADD_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.BROWNFIELD_TASK,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "planner", "implementer", "validator"],
                    model_tier="sonnet",
                    platform="generic",
                )

            # Source files but no clear intent → needs onboarding
            return WorkflowConfig(
                workflow_type=WorkflowType.BROWNFIELD_ONBOARD,
                requires_onboarding=True,
                agent_sequence=["analyst", "planner"],
                model_tier="opus",
                platform="generic",
            )

        # Default: free task
        return WorkflowConfig(
            workflow_type=WorkflowType.FREE_TASK,
            requires_onboarding=False,
            agent_sequence=["planner", "implementer"],
            model_tier="sonnet",
            platform="generic",
        )

    def _has_ios_project(self, project_dir: Path) -> bool:
        """Check for iOS project indicators."""
        try:
            for item in project_dir.iterdir():
                if item.suffix in (".xcodeproj", ".xcworkspace"):
                    return True
        except PermissionError:
            pass
        return False

    def _count_source_files(self, project_dir: Path, max_depth: int = 4) -> int:
        """Count non-config source files recursively."""
        count = 0
        try:
            for path in project_dir.rglob("*"):
                if not path.is_file() or path.suffix not in SOURCE_EXTENSIONS:
                    continue
                if any(p.startswith(".") or p in _SKIP_DIRS for p in path.parts):
                    continue
                count += 1
                if count > 10:  # Early exit — clearly a codebase
                    return count
        except PermissionError:
            pass
        return count
