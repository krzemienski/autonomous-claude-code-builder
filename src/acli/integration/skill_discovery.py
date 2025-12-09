"""
Skill Discovery
===============

Discovers and loads skills from ~/.claude/skills/ directory.
Provides skill suggestions based on project context.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    """A discovered Claude Code skill."""
    name: str
    path: Path
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "capabilities": self.capabilities,
            "triggers": self.triggers,
        }


def parse_skill_md(path: Path) -> Skill | None:
    """
    Parse SKILL.md file to extract skill metadata.

    Looks for YAML frontmatter and markdown content.
    """
    skill_file = path / "SKILL.md"
    if not skill_file.exists():
        return None

    content = skill_file.read_text()

    # Extract YAML frontmatter
    name = path.name
    description = ""
    capabilities = []
    triggers = []

    # Look for frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)

        # Parse simple YAML
        for line in frontmatter.split("\n"):
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("description:"):
                description = line.split(":", 1)[1].strip().strip('"\'')

    # Look for capabilities section
    caps_match = re.search(r'##\s*Capabilities\s*\n((?:[-*]\s+.+\n?)+)', content)
    if caps_match:
        for line in caps_match.group(1).split("\n"):
            line = line.strip()
            if line.startswith(("-", "*")):
                cap = line.lstrip("-* ").strip()
                if cap:
                    capabilities.append(cap)

    # Look for triggers/keywords
    triggers_match = re.search(r'##\s*(?:Triggers|Keywords)\s*\n((?:[-*]\s+.+\n?)+)', content)
    if triggers_match:
        for line in triggers_match.group(1).split("\n"):
            line = line.strip()
            if line.startswith(("-", "*")):
                trigger = line.lstrip("-* ").strip().strip('"\'')
                if trigger:
                    triggers.append(trigger)

    return Skill(
        name=name,
        path=path,
        description=description,
        capabilities=capabilities,
        triggers=triggers,
    )


def discover_skills(
    skills_dir: Path | None = None,
    include_project: bool = True,
) -> list[Skill]:
    """
    Discover available skills.

    Searches:
    - ~/.claude/skills/ (user skills)
    - .claude/skills/ (project skills, if include_project=True)
    """
    skills = []

    # User skills
    user_skills_dir = skills_dir or (Path.home() / ".claude" / "skills")
    if user_skills_dir.exists():
        for path in user_skills_dir.iterdir():
            if path.is_dir():
                skill = parse_skill_md(path)
                if skill:
                    skills.append(skill)

    # Project skills
    if include_project:
        project_skills_dir = Path.cwd() / ".claude" / "skills"
        if project_skills_dir.exists():
            for path in project_skills_dir.iterdir():
                if path.is_dir():
                    skill = parse_skill_md(path)
                    if skill:
                        skills.append(skill)

    return skills


def suggest_skills(
    context: str,
    skills: list[Skill] | None = None,
) -> list[Skill]:
    """
    Suggest relevant skills based on context.

    Args:
        context: Description of current task/project
        skills: Available skills (discovered if None)

    Returns:
        List of relevant skills, sorted by relevance
    """
    if skills is None:
        skills = discover_skills()

    if not skills:
        return []

    context_lower = context.lower()
    scored_skills = []

    for skill in skills:
        score = 0

        # Check triggers
        for trigger in skill.triggers:
            if trigger.lower() in context_lower:
                score += 10

        # Check capabilities
        for cap in skill.capabilities:
            cap_words = cap.lower().split()
            for word in cap_words:
                if len(word) > 3 and word in context_lower:
                    score += 2

        # Check description
        desc_words = skill.description.lower().split()
        for word in desc_words:
            if len(word) > 3 and word in context_lower:
                score += 1

        if score > 0:
            scored_skills.append((score, skill))

    # Sort by score descending
    scored_skills.sort(key=lambda x: x[0], reverse=True)

    return [skill for _, skill in scored_skills]


def get_skill_content(skill: Skill) -> str:
    """Get full content of a skill's SKILL.md."""
    skill_file = skill.path / "SKILL.md"
    if skill_file.exists():
        return skill_file.read_text()
    return ""


def list_skills_summary() -> list[dict[str, str]]:
    """Get summary list of all available skills."""
    skills = discover_skills()
    return [
        {
            "name": s.name,
            "description": s.description or "No description",
            "path": str(s.path),
        }
        for s in skills
    ]
