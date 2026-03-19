"""Skill engine — discovers and maps skills to agents."""

from pathlib import Path

# Maps agent types to their default skills
AGENT_SKILL_MAP: dict[str, list[str]] = {
    "validator": ["functional-validation"],
    "planner": ["create-validation-plan", "create-plans"],
    "implementer": ["python-agent-sdk"],
    "reporter": [],
    "analyst": [],
    "context_manager": [],
    "router": [],
}

# Maps platforms to additional skills
PLATFORM_SKILL_MAP: dict[str, list[str]] = {
    "ios": ["ios-swift-expert", "xc-mcp"],
    "web": ["frontend-development", "e2e-testing"],
    "cli": ["python-patterns"],
    "generic": [],
}

# Maps keywords in task context to skills
KEYWORD_SKILL_MAP: dict[str, str] = {
    "elevenlabs": "elevenlabs-api",
    "tts": "elevenlabs-api",
    "playwright": "e2e-testing",
    "supabase": "supabase",
    "stripe": "payment-integration",
    "auth": "better-auth",
    "database": "databases",
    "docker": "devops",
    "expo": "expo-development",
    "react native": "react-native-expert",
    "react": "frontend-development",
    "next.js": "web-frameworks",
    "nextjs": "web-frameworks",
    "django": "django-patterns",
    "fastapi": "python-fastapi-backend-testing",
    "swift": "ios-swift-expert",
    "swiftui": "swiftui-patterns",
}


class SkillEngine:
    """Discovers and maps skills to agents based on type, platform, and context."""

    def __init__(self, skills_dir: Path | None = None) -> None:
        self.skills_dir = skills_dir or (Path.home() / ".claude" / "skills")

    def discover_skills(self) -> list[str]:
        """Scan skills directory for available SKILL.md files."""
        if not self.skills_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )

    def get_skills_for_agent(
        self,
        agent_type: str,
        platform: str = "",
        task_context: str = "",
    ) -> list[str]:
        """Get relevant skills for an agent type, platform, and task context."""
        skills: list[str] = []

        # Agent-type defaults
        skills.extend(AGENT_SKILL_MAP.get(agent_type, []))

        # Platform-specific
        if platform:
            skills.extend(PLATFORM_SKILL_MAP.get(platform, []))

        # Keyword detection from task context
        if task_context:
            context_lower = task_context.lower()
            for keyword, skill in KEYWORD_SKILL_MAP.items():
                if keyword in context_lower and skill not in skills:
                    skills.append(skill)

        return skills

    def load_skill_content(self, skill_name: str) -> str:
        """Read SKILL.md content for a given skill."""
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            return ""
        return skill_path.read_text()

    def get_combined_skill_prompt(self, skill_names: list[str]) -> str:
        """Concatenate skill content for system prompt injection."""
        parts: list[str] = []
        for name in skill_names:
            content = self.load_skill_content(name)
            if content:
                parts.append(f"<skill name=\"{name}\">\n{content}\n</skill>")
        return "\n\n".join(parts)
