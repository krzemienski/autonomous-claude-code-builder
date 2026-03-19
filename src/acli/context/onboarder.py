"""Brownfield project onboarder for analyzing existing codebases.

Orchestrates tech stack detection, convention scanning, architecture
mapping, and context store population. Emits streaming events for
real-time progress feedback in the TUI.
"""

from pathlib import Path
from typing import Any

from ..core.streaming import StreamingHandler
from .chunker import KnowledgeChunker
from .store import ContextStore

# Mapping of marker files to tech stack indicators
_TECH_MARKERS: dict[str, dict[str, str]] = {
    "package.json": {"language": "JavaScript/TypeScript", "runtime": "Node.js"},
    "pyproject.toml": {"language": "Python"},
    "setup.py": {"language": "Python"},
    "Cargo.toml": {"language": "Rust"},
    "go.mod": {"language": "Go"},
    "pom.xml": {"language": "Java", "build": "Maven"},
    "build.gradle": {"language": "Java/Kotlin", "build": "Gradle"},
    "Gemfile": {"language": "Ruby"},
    "composer.json": {"language": "PHP"},
    "mix.exs": {"language": "Elixir"},
    "pubspec.yaml": {"language": "Dart/Flutter"},
}

# Mapping of config files to convention tools
_CONVENTION_MARKERS: dict[str, str] = {
    ".eslintrc": "eslint",
    ".eslintrc.js": "eslint",
    ".eslintrc.json": "eslint",
    ".eslintrc.yml": "eslint",
    "eslint.config.js": "eslint",
    "eslint.config.mjs": "eslint",
    ".prettierrc": "prettier",
    ".prettierrc.json": "prettier",
    "prettier.config.js": "prettier",
    "ruff.toml": "ruff",
    ".flake8": "flake8",
    ".pylintrc": "pylint",
    "mypy.ini": "mypy",
    ".mypy.ini": "mypy",
    "tsconfig.json": "typescript",
    "biome.json": "biome",
    ".editorconfig": "editorconfig",
    ".stylelintrc": "stylelint",
    "rustfmt.toml": "rustfmt",
    ".clippy.toml": "clippy",
}


class BrownfieldOnboarder:
    """Analyzes existing codebases to build project context.

    Runs a multi-step onboarding pipeline: file discovery, tech stack
    detection, architecture mapping, convention detection, and knowledge
    chunking. Results are persisted via ContextStore.
    """

    async def onboard(
        self,
        project_dir: Path,
        streaming: StreamingHandler,
    ) -> dict[str, Any]:
        """Run the full onboarding pipeline.

        Args:
            project_dir: Root directory of the project to analyze.
            streaming: Handler for emitting progress events.

        Returns:
            Combined analysis results dictionary.
        """
        store = ContextStore(project_dir)
        store.initialize()

        await streaming.handle_phase_start("tech_stack", "Tech Stack Detection")
        tech_stack = self.detect_tech_stack(project_dir)
        store.store_tech_stack(tech_stack)
        await streaming.handle_phase_end("tech_stack", "completed")

        await streaming.handle_phase_start("architecture", "Architecture Mapping")
        architecture = self.map_architecture(project_dir)
        await streaming.handle_phase_end("architecture", "completed")

        await streaming.handle_phase_start("conventions", "Convention Detection")
        conventions = self.detect_conventions(project_dir)
        store.store_conventions(conventions)
        await streaming.handle_phase_end("conventions", "completed")

        analysis: dict[str, Any] = {
            "tech_stack": tech_stack,
            "architecture": architecture,
            "conventions": conventions,
        }
        store.store_analysis(analysis)

        await streaming.handle_phase_start("chunking", "Knowledge Chunking")
        chunker = KnowledgeChunker()
        chunks = chunker.chunk_codebase(project_dir)
        analysis["chunk_count"] = len(chunks)
        await streaming.handle_phase_end("chunking", "completed")

        await streaming.handle_context_update("onboarding", "complete")
        return analysis

    def detect_tech_stack(self, project_dir: Path) -> dict[str, Any]:
        """Detect the project's technology stack from marker files.

        Args:
            project_dir: Root directory to scan.

        Returns:
            Dictionary with detected languages, frameworks, databases, etc.
        """
        result: dict[str, Any] = {"languages": [], "tools": {}}
        seen_languages: set[str] = set()

        for marker_file, info in _TECH_MARKERS.items():
            if (project_dir / marker_file).exists():
                lang = info.get("language", "")
                if lang and lang not in seen_languages:
                    result["languages"].append(lang)
                    seen_languages.add(lang)
                for k, v in info.items():
                    if k != "language":
                        result["tools"][k] = v

        # Detect frameworks from package.json
        pkg_json = project_dir / "package.json"
        if pkg_json.exists():
            try:
                import json
                pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                frameworks = (
                    "react", "vue", "angular", "svelte",
                    "next", "nuxt", "express", "fastify",
                )
                for fw in frameworks:
                    if fw in deps or f"@{fw}/core" in deps:
                        result["tools"]["framework"] = fw
                        break
            except (OSError, ValueError):
                pass  # Skip unreadable package.json

        return result

    def detect_conventions(self, project_dir: Path) -> dict[str, Any]:
        """Detect coding conventions from config files.

        Args:
            project_dir: Root directory to scan.

        Returns:
            Dictionary mapping tool categories to detected tool names.
        """
        found: dict[str, list[str]] = {"linters": [], "formatters": [], "type_checkers": []}

        for config_file, tool_name in _CONVENTION_MARKERS.items():
            if (project_dir / config_file).exists():
                if tool_name in ("eslint", "flake8", "pylint", "clippy", "biome", "stylelint"):
                    if tool_name not in found["linters"]:
                        found["linters"].append(tool_name)
                elif tool_name in ("prettier", "ruff", "rustfmt", "editorconfig"):
                    if tool_name not in found["formatters"]:
                        found["formatters"].append(tool_name)
                elif tool_name in ("typescript", "mypy"):
                    if tool_name not in found["type_checkers"]:
                        found["type_checkers"].append(tool_name)

        return {k: v for k, v in found.items() if v}

    def map_architecture(self, project_dir: Path) -> dict[str, Any]:
        """Map the project's directory architecture.

        Args:
            project_dir: Root directory to scan.

        Returns:
            Dictionary with directory file counts, total files,
            and identified source layout.
        """
        skip = {".git", "node_modules", "__pycache__", ".acli", ".venv", "venv"}
        dir_counts: dict[str, int] = {}
        total_files = 0

        for item in project_dir.rglob("*"):
            if any(part in skip for part in item.parts):
                continue
            if item.is_file():
                total_files += 1
                parent = str(item.parent.relative_to(project_dir))
                dir_counts[parent] = dir_counts.get(parent, 0) + 1

        # Identify src layout
        src_layout = "flat"
        for d in ("src", "lib", "app", "pkg"):
            if (project_dir / d).is_dir():
                src_layout = d
                break

        return {
            "total_files": total_files,
            "src_layout": src_layout,
            "directories": dict(sorted(dir_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
        }
