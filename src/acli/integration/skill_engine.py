"""
Skill Engine — Auto-detects and loads relevant skills for each agent type.

Scans available skills directories and matches against agent type,
project platform, and task context keywords.
"""

from pathlib import Path


class SkillEngine:
    """Auto-detects and loads relevant skills for agents."""

    # Skills mapped to agent types
    AGENT_SKILL_MAP: dict[str, list[str]] = {
        "validator": ["functional-validation"],
        "planner": ["create-validation-plan", "create-plans"],
        "implementer": ["python-agent-sdk"],
        "analyst": [],
        "reporter": [],
        "router": [],
        "context_manager": [],
    }

    # Skills mapped to platforms
    PLATFORM_SKILL_MAP: dict[str, list[str]] = {
        "ios": ["ios-validation-runner", "ios-swift-development"],
        "web": ["e2e-testing", "web-testing"],
        "api": ["api-design"],
        "cli": ["functional-validation"],
    }

    # Skills mapped to keywords found in task context
    KEYWORD_SKILL_MAP: dict[str, list[str]] = {
        "elevenlabs": ["elevenlabs-api"],
        "prompt": ["optimize-prompt", "prompt-engineering-expert"],
        "security": ["security-review"],
        "database": ["databases", "postgres-patterns"],
        "docker": ["docker-patterns"],
        "react": ["react-best-practices"],
        "django": ["django-patterns"],
        "fastapi": ["backend-development"],
    }

    def __init__(self, skills_dirs: list[Path] | None = None) -> None:
        """Initialize with optional skills directory paths."""
        if skills_dirs is None:
            self.skills_dirs = [
                Path.home() / ".claude" / "skills",
            ]
        else:
            self.skills_dirs = skills_dirs

    def discover_skills(self) -> list[str]:
        """Scan skills directories and return available skill names."""
        available: list[str] = []
        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                continue
            for entry in skills_dir.iterdir():
                if entry.is_dir() and (entry / "SKILL.md").exists():
                    available.append(entry.name)
        return sorted(set(available))

    def get_skills_for_agent(
        self,
        agent_type: str,
        platform: str = "",
        task_context: str = "",
    ) -> list[str]:
        """Get relevant skills for an agent based on type, platform, and context."""
        skills: list[str] = []

        # 1. Agent-type skills
        agent_skills = self.AGENT_SKILL_MAP.get(agent_type, [])
        skills.extend(agent_skills)

        # 2. Platform-specific skills
        if platform:
            platform_skills = self.PLATFORM_SKILL_MAP.get(platform.lower(), [])
            skills.extend(platform_skills)

        # 3. Keyword detection from task context
        if task_context:
            context_lower = task_context.lower()
            for keyword, keyword_skills in self.KEYWORD_SKILL_MAP.items():
                if keyword in context_lower:
                    skills.extend(keyword_skills)

        return sorted(set(skills))

    def load_skill_content(self, skill_name: str) -> str | None:
        """Load SKILL.md content for a given skill name."""
        for skills_dir in self.skills_dirs:
            skill_path = skills_dir / skill_name / "SKILL.md"
            if skill_path.exists():
                return skill_path.read_text()
        return None

    def get_combined_skill_prompt(self, skill_names: list[str]) -> str:
        """Load and combine multiple skill contents into a single prompt."""
        sections: list[str] = []
        for name in skill_names:
            content = self.load_skill_content(name)
            if content:
                sections.append(f"## Skill: {name}\n\n{content}")
        return "\n\n---\n\n".join(sections) if sections else ""
