"""
Prompt Router
=============

Classifies any user prompt into a WorkflowType with configuration.
"""

import re
from pathlib import Path

from .workflows import WorkflowConfig, WorkflowType

# Source file extensions considered "significant"
SOURCE_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx",
    ".swift", ".rs", ".go", ".java", ".kt",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb",
}

# Config files to exclude from "significant" count
CONFIG_FILES = {
    "package.json", "tsconfig.json", "pyproject.toml", "setup.py",
    "Cargo.toml", "go.mod", "Makefile", "Dockerfile",
    ".gitignore", ".eslintrc.json", "jest.config.js",
}

# Minimum source files to consider a project "brownfield"
MIN_SOURCE_FILES = 3

# Intent patterns
DEBUG_PATTERNS = re.compile(
    r"\b(fix|debug|broken|crash|error|bug|failing|issue|wrong|not working)\b",
    re.IGNORECASE,
)
REFACTOR_PATTERNS = re.compile(
    r"\b(refactor|migrate|convert|restructure|rewrite|modernize|upgrade)\b",
    re.IGNORECASE,
)
TASK_PATTERNS = re.compile(
    r"\b(add|implement|create|build|make|develop|integrate|setup|set up)\b",
    re.IGNORECASE,
)


class PromptRouter:
    """Classifies any user prompt into a WorkflowType with config."""

    def classify(self, prompt: str, project_dir: Path) -> WorkflowConfig:
        """
        Classify a prompt and project directory into a workflow config.

        Classification logic:
        1. Check project_dir for platform signals (.xcodeproj, etc.)
        2. Check for existing codebase (brownfield indicators)
        3. Parse prompt text for intent signals
        4. Return WorkflowConfig with agent sequence and model tier
        """
        # 1. Check for iOS project
        if self._has_ios_project(project_dir):
            return WorkflowConfig(
                workflow_type=WorkflowType.IOS_APP,
                requires_onboarding=True,
                agent_sequence=["analyst", "planner", "implementer", "validator"],
                model_tier="opus",
                platform="ios",
            )

        # 2. Check for CLI tool (Cargo.toml or Go binary indicators)
        if self._has_cli_indicators(project_dir):
            return WorkflowConfig(
                workflow_type=WorkflowType.CLI_TOOL,
                requires_onboarding=True,
                agent_sequence=["analyst", "planner", "implementer", "validator"],
                model_tier="sonnet",
                platform="cli",
            )

        # 3. Check for greenfield (app_spec.txt, no significant source)
        has_spec = (project_dir / "app_spec.txt").exists()
        source_count = self._count_source_files(project_dir)

        if has_spec and source_count <= MIN_SOURCE_FILES:
            return WorkflowConfig(
                workflow_type=WorkflowType.GREENFIELD_APP,
                requires_onboarding=False,
                agent_sequence=["analyst", "planner", "implementer", "validator"],
                model_tier="sonnet",
                platform=self._detect_platform(project_dir),
            )

        # 4. Brownfield scenarios — significant source files present
        if source_count > MIN_SOURCE_FILES:
            is_onboarded = self._is_onboarded(project_dir)

            # Check prompt intent
            if DEBUG_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.DEBUG,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "implementer", "validator"],
                    model_tier="opus",
                    platform=self._detect_platform(project_dir),
                )

            if REFACTOR_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.REFACTOR,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=["analyst", "planner", "implementer", "validator"],
                    model_tier="opus",
                    platform=self._detect_platform(project_dir),
                )

            if TASK_PATTERNS.search(prompt):
                return WorkflowConfig(
                    workflow_type=WorkflowType.BROWNFIELD_TASK,
                    requires_onboarding=not is_onboarded,
                    agent_sequence=[
                        "analyst", "planner", "implementer", "validator",
                    ],
                    model_tier="sonnet",
                    platform=self._detect_platform(project_dir),
                )

            # Has source files but no clear intent — needs onboarding
            if not is_onboarded:
                return WorkflowConfig(
                    workflow_type=WorkflowType.BROWNFIELD_ONBOARD,
                    requires_onboarding=True,
                    agent_sequence=["analyst", "context_manager"],
                    model_tier="opus",
                    platform=self._detect_platform(project_dir),
                )

            # Onboarded brownfield with generic prompt
            return WorkflowConfig(
                workflow_type=WorkflowType.BROWNFIELD_TASK,
                requires_onboarding=False,
                agent_sequence=["analyst", "planner", "implementer", "validator"],
                model_tier="sonnet",
                platform=self._detect_platform(project_dir),
            )

        # 5. Fallback — free task
        return WorkflowConfig(
            workflow_type=WorkflowType.FREE_TASK,
            requires_onboarding=False,
            agent_sequence=["implementer", "validator"],
            model_tier="sonnet",
            platform="generic",
        )

    def _has_ios_project(self, project_dir: Path) -> bool:
        """Check for iOS/Xcode project indicators."""
        for item in project_dir.iterdir():
            if item.suffix in (".xcodeproj", ".xcworkspace"):
                return True
        return False

    def _has_cli_indicators(self, project_dir: Path) -> bool:
        """Check for CLI tool indicators (Cargo.toml, Go binary)."""
        if (project_dir / "Cargo.toml").exists():
            return True
        if (project_dir / "go.mod").exists():
            # Check for main.go as CLI indicator
            if (project_dir / "main.go").exists() or (
                project_dir / "cmd"
            ).is_dir():
                return True
        return False

    def _count_source_files(self, project_dir: Path) -> int:
        """Count source files (non-config) in the project."""
        count = 0
        try:
            for path in project_dir.rglob("*"):
                if path.is_file() and path.name not in CONFIG_FILES:
                    if path.suffix in SOURCE_EXTENSIONS:
                        count += 1
                        if count > MIN_SOURCE_FILES:
                            return count
        except (PermissionError, OSError):
            pass
        return count

    def _is_onboarded(self, project_dir: Path) -> bool:
        """Check if the project has been onboarded (context exists)."""
        context_dir = project_dir / ".acli" / "context"
        analysis_file = context_dir / "codebase_analysis.json"
        return analysis_file.exists()

    def _detect_platform(self, project_dir: Path) -> str:
        """Detect the platform from project files."""
        if (project_dir / "package.json").exists():
            return "web"
        if (project_dir / "pyproject.toml").exists() or (
            project_dir / "setup.py"
        ).exists():
            return "cli"
        if (project_dir / "Cargo.toml").exists():
            return "cli"
        return "generic"
