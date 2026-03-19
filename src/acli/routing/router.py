"""Prompt router: classifies user prompts into workflow types."""

import re
from pathlib import Path

from .workflows import WorkflowConfig, WorkflowType

# Source file extensions to check
SOURCE_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx",
    ".swift", ".rs", ".go", ".java", ".kt", ".rb", ".cs",
}

# Agent sequences per workflow type
_AGENT_SEQUENCES: dict[WorkflowType, list[str]] = {
    WorkflowType.GREENFIELD_APP: ["analyst", "planner", "implementer", "validator"],
    WorkflowType.BROWNFIELD_ONBOARD: ["analyst", "planner"],
    WorkflowType.BROWNFIELD_TASK: ["planner", "implementer", "validator"],
    WorkflowType.REFACTOR: ["analyst", "planner", "implementer", "validator"],
    WorkflowType.DEBUG: ["analyst", "implementer", "validator"],
    WorkflowType.CLI_TOOL: ["analyst", "planner", "implementer", "validator"],
    WorkflowType.IOS_APP: ["analyst", "planner", "implementer", "validator"],
    WorkflowType.FREE_TASK: ["implementer", "validator"],
}

# Workflow types that use opus model tier (analyst/planner-heavy)
_OPUS_WORKFLOWS = {
    WorkflowType.GREENFIELD_APP,
    WorkflowType.BROWNFIELD_ONBOARD,
    WorkflowType.REFACTOR,
    WorkflowType.CLI_TOOL,
    WorkflowType.IOS_APP,
}

# Patterns for debug classification
_DEBUG_PATTERNS = re.compile(
    r"\b(fix|debug|broken|crash|error|bug|issue|fail|traceback|exception)\b",
    re.IGNORECASE,
)

# Patterns for refactor classification
_REFACTOR_PATTERNS = re.compile(
    r"\b(refactor|migrate|convert|restructure|reorganize|rewrite|modernize)\b",
    re.IGNORECASE,
)


def _count_source_files(project_dir: Path, max_depth: int = 3) -> int:
    """Count source files up to max_depth levels deep."""
    count = 0
    for ext in SOURCE_EXTENSIONS:
        for path in project_dir.rglob(f"*{ext}"):
            # Enforce max depth relative to project_dir
            try:
                relative = path.relative_to(project_dir)
            except ValueError:
                continue
            if len(relative.parts) <= max_depth:
                count += 1
    return count


def _detect_platform(project_dir: Path, workflow_type: WorkflowType) -> str:
    """Detect the project platform from filesystem signals."""
    if workflow_type == WorkflowType.IOS_APP:
        return "ios"
    if workflow_type == WorkflowType.CLI_TOOL:
        return "cli"
    if (project_dir / "package.json").exists():
        return "web"
    if (project_dir / "requirements.txt").exists():
        try:
            content = (project_dir / "requirements.txt").read_text()
            if re.search(r"\b(django|fastapi|flask|starlette)\b", content, re.IGNORECASE):
                return "api"
        except OSError:
            pass  # requirements.txt unreadable; skip framework detection
    return "generic"


def _has_onboarding_context(project_dir: Path) -> bool:
    """Check whether the project has already been onboarded."""
    return (project_dir / ".acli" / "context" / "codebase_analysis.json").exists()


class PromptRouter:
    """Classifies any user prompt into a WorkflowType with config.

    Classification rules (checked in order):
    1. .xcodeproj or .xcworkspace present -> IOS_APP
    2. Cargo.toml present -> CLI_TOOL
    3. app_spec.txt present AND <4 source files -> GREENFIELD_APP
    4. Has significant source files (>3):
       a. If already onboarded (.acli/context/codebase_analysis.json):
          - prompt has fix/debug/broken -> DEBUG
          - prompt has refactor/migrate/convert -> REFACTOR
          - else -> BROWNFIELD_TASK
       b. If NOT onboarded -> BROWNFIELD_ONBOARD (requires_onboarding=True)
    5. None of the above -> FREE_TASK
    """

    def classify(self, prompt: str, project_dir: Path) -> WorkflowConfig:
        """Classify a prompt and project directory into a workflow config."""
        workflow_type = self._determine_workflow(prompt, project_dir)
        requires_onboarding = self._needs_onboarding(workflow_type, project_dir)
        platform = _detect_platform(project_dir, workflow_type)
        model_tier = "opus" if workflow_type in _OPUS_WORKFLOWS else "sonnet"
        agent_sequence = list(_AGENT_SEQUENCES.get(workflow_type, []))

        return WorkflowConfig(
            workflow_type=workflow_type,
            requires_onboarding=requires_onboarding,
            agent_sequence=agent_sequence,
            model_tier=model_tier,
            platform=platform,
        )

    def _determine_workflow(self, prompt: str, project_dir: Path) -> WorkflowType:
        """Apply classification rules in priority order."""
        # Rule 1: iOS project markers
        if self._has_ios_markers(project_dir):
            return WorkflowType.IOS_APP

        # Rule 2: Cargo.toml -> CLI tool
        if (project_dir / "Cargo.toml").exists():
            return WorkflowType.CLI_TOOL

        # Rule 3: app_spec.txt with few source files -> greenfield
        if (project_dir / "app_spec.txt").exists():
            source_count = _count_source_files(project_dir)
            if source_count < 4:
                return WorkflowType.GREENFIELD_APP

        # Rule 4: Significant source files present
        source_count = _count_source_files(project_dir)
        if source_count > 3:
            if _has_onboarding_context(project_dir):
                # 4a: Already onboarded — classify by prompt intent
                if _DEBUG_PATTERNS.search(prompt):
                    return WorkflowType.DEBUG
                if _REFACTOR_PATTERNS.search(prompt):
                    return WorkflowType.REFACTOR
                return WorkflowType.BROWNFIELD_TASK
            # 4b: Not yet onboarded
            return WorkflowType.BROWNFIELD_ONBOARD

        # Rule 5: Fallback
        return WorkflowType.FREE_TASK

    def _needs_onboarding(
        self, workflow_type: WorkflowType, project_dir: Path
    ) -> bool:
        """Determine whether onboarding is required."""
        if workflow_type == WorkflowType.BROWNFIELD_ONBOARD:
            return True
        if workflow_type == WorkflowType.BROWNFIELD_TASK:
            # First-time brownfield task also needs onboarding
            return not _has_onboarding_context(project_dir)
        return False

    @staticmethod
    def _has_ios_markers(project_dir: Path) -> bool:
        """Check for .xcodeproj or .xcworkspace directories."""
        for child in project_dir.iterdir():
            if child.is_dir() and (
                child.suffix == ".xcodeproj" or child.suffix == ".xcworkspace"
            ):
                return True
        return False
