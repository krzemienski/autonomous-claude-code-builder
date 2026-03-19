"""
Skill Engine
=============

Auto-detects and loads relevant skills for each agent type and task context.
"""

from pathlib import Path


class SkillEngine:
    """
    Auto-detects and loads relevant skills for each agent type and task context.

    Scans available skills directories and matches against:
    - Agent type (validator -> functional-validation)
    - Project platform (iOS -> ios-validation-runner)
    - Task type (planning -> create-validation-plan)
    - Technology keywords (ElevenLabs -> elevenlabs skill)
    """

    AGENT_SKILL_MAP: dict[str, list[str]] = {
        "validator": ["functional-validation"],
        "planner": ["create-validation-plan", "create-plans"],
        "implementer": ["python-agent-sdk"],
        "analyst": [],
        "router": [],
        "context_manager": [],
        "reporter": [],
    }

    PLATFORM_SKILL_MAP: dict[str, list[str]] = {
        "ios": ["ios-validation-runner"],
        "web": [],
        "cli": [],
        "api": [],
    }

    KEYWORD_SKILL_MAP: dict[str, list[str]] = {
        "elevenlabs": ["elevenlabs"],
        "prompt": ["optimize-prompt", "prompt-engineering-expert"],
        "agent": ["python-agent-sdk"],
        "claude": ["claude-api"],
    }

    def __init__(self, skills_dirs: list[Path] | None = None) -> None:
        self._skills_dirs = skills_dirs or self._default_dirs()
        self._discovered: list[str] = []

    def _default_dirs(self) -> list[Path]:
        """Get default skill directories."""
        dirs: list[Path] = []
        home_skills = Path.home() / ".claude" / "skills"
        if home_skills.exists():
            dirs.append(home_skills)
        local_skills = Path(".claude") / "skills"
        if local_skills.exists():
            dirs.append(local_skills)
        return dirs

    def discover_skills(self) -> list[str]:
        """Discover all available skills from configured directories."""
        skills: list[str] = []
        for skills_dir in self._skills_dirs:
            if not skills_dir.exists():
                continue
            for item in skills_dir.iterdir():
                if item.is_dir() and (item / "SKILL.md").exists():
                    skills.append(item.name)
        self._discovered = skills
        return skills

    def get_skills_for_agent(
        self,
        agent_type: str,
        platform: str = "",
        task_context: str = "",
    ) -> list[str]:
        """
        Get relevant skills for an agent type, platform, and task context.

        Args:
            agent_type: The agent type (e.g., 'validator', 'planner').
            platform: The target platform (e.g., 'ios', 'web').
            task_context: The task description for keyword matching.

        Returns:
            List of skill names relevant to this agent + context.
        """
        skills: list[str] = []

        # 1. Agent-type base skills
        base_skills = self.AGENT_SKILL_MAP.get(agent_type, [])
        skills.extend(base_skills)

        # 2. Platform-specific skills
        if platform:
            platform_skills = self.PLATFORM_SKILL_MAP.get(platform, [])
            for s in platform_skills:
                if s not in skills:
                    skills.append(s)

        # 3. Keyword detection from task context
        if task_context:
            context_lower = task_context.lower()
            for keyword, keyword_skills in self.KEYWORD_SKILL_MAP.items():
                if keyword in context_lower:
                    for s in keyword_skills:
                        if s not in skills:
                            skills.append(s)

        return skills

    def load_skill_content(self, skill_name: str) -> str | None:
        """Load the SKILL.md content for a named skill."""
        for skills_dir in self._skills_dirs:
            skill_path = skills_dir / skill_name / "SKILL.md"
            if skill_path.exists():
                try:
                    return skill_path.read_text()
                except OSError:
                    pass
        return None

    def get_combined_skill_prompt(self, skill_names: list[str]) -> str:
        """Combine multiple skill contents into a single prompt section."""
        parts: list[str] = []
        for name in skill_names:
            content = self.load_skill_content(name)
            if content:
                parts.append(f"## Skill: {name}\n\n{content}")
        return "\n\n---\n\n".join(parts) if parts else ""
