"""
Brownfield Onboarder
====================

Full codebase analysis and context population for brownfield projects.
"""

from pathlib import Path
from typing import Any

from ..core.streaming import StreamingHandler
from .chunker import KnowledgeChunker
from .store import ContextStore

# Common framework indicators
FRAMEWORK_INDICATORS: dict[str, dict[str, str]] = {
    "package.json": {"framework": "Node.js"},
    "pyproject.toml": {"language": "Python"},
    "setup.py": {"language": "Python"},
    "Cargo.toml": {"language": "Rust"},
    "go.mod": {"language": "Go"},
    "Gemfile": {"language": "Ruby"},
    "pom.xml": {"language": "Java"},
    "build.gradle": {"language": "Java/Kotlin"},
}


class BrownfieldOnboarder:
    """
    Full codebase analysis and context population for brownfield projects.

    Executes:
    1. File tree discovery
    2. Tech stack detection
    3. Architecture mapping
    4. Convention detection
    5. Context store population
    6. Knowledge chunking
    """

    async def onboard(
        self,
        project_dir: Path,
        streaming: StreamingHandler,
    ) -> dict[str, Any]:
        """
        Run full onboarding for a brownfield project.

        Args:
            project_dir: Project root directory.
            streaming: Streaming handler for progress events.

        Returns:
            Dict with onboarding results.
        """
        store = ContextStore(project_dir)
        store.initialize()

        await streaming.handle_context_update("onboarding", "Starting codebase analysis")

        # 1. Tech stack detection
        tech_stack = self.detect_tech_stack(project_dir)
        store.store_tech_stack(tech_stack)
        await streaming.handle_context_update("tech_stack", str(tech_stack))

        # 2. Architecture mapping
        architecture = self.map_architecture(project_dir)
        store.store_analysis(architecture)
        await streaming.handle_context_update("architecture", str(architecture))

        # 3. Convention detection
        conventions = self.detect_conventions(project_dir)
        store.store_conventions(conventions)
        await streaming.handle_context_update("conventions", str(conventions))

        # 4. Knowledge chunking
        chunker = KnowledgeChunker()
        chunks = chunker.chunk_codebase(project_dir)
        await streaming.handle_context_update(
            "chunking", f"Created {len(chunks)} knowledge chunks"
        )

        return {
            "tech_stack": tech_stack,
            "architecture": architecture,
            "conventions": conventions,
            "chunk_count": len(chunks),
        }

    def detect_tech_stack(self, project_dir: Path) -> dict[str, Any]:
        """Detect the technology stack from project files."""
        stack: dict[str, Any] = {}

        for filename, indicators in FRAMEWORK_INDICATORS.items():
            if (project_dir / filename).exists():
                stack.update(indicators)

        # Detect specific frameworks from file contents
        if (project_dir / "package.json").exists():
            try:
                import json
                data = json.loads((project_dir / "package.json").read_text())
                deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
                if "react" in deps:
                    stack["framework"] = "React"
                elif "vue" in deps:
                    stack["framework"] = "Vue"
                elif "next" in deps:
                    stack["framework"] = "Next.js"
                elif "express" in deps:
                    stack["framework"] = "Express"
                stack["language"] = "TypeScript" if "typescript" in deps else "JavaScript"
            except (OSError, json.JSONDecodeError):
                pass

        # Count source files by extension
        ext_counts: dict[str, int] = {}
        try:
            for path in project_dir.rglob("*"):
                if path.is_file() and path.suffix:
                    ext = path.suffix
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
        except (PermissionError, OSError):
            pass

        if ext_counts:
            stack["file_types"] = dict(
                sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            )

        return stack

    def detect_conventions(self, project_dir: Path) -> dict[str, Any]:
        """Detect code conventions from the project."""
        conventions: dict[str, Any] = {}

        # Check for linting config
        if (project_dir / ".eslintrc.json").exists() or (
            project_dir / ".eslintrc.js"
        ).exists():
            conventions["linter"] = "ESLint"
        if (project_dir / "pyproject.toml").exists():
            try:
                content = (project_dir / "pyproject.toml").read_text()
                if "ruff" in content:
                    conventions["linter"] = "Ruff"
                if "mypy" in content:
                    conventions["type_checker"] = "mypy"
            except OSError:
                pass

        # Check for formatting config
        if (project_dir / ".prettierrc").exists():
            conventions["formatter"] = "Prettier"

        # Check for test framework
        if (project_dir / "jest.config.js").exists():
            conventions["test_framework"] = "Jest"
        if (project_dir / "pytest.ini").exists() or (
            project_dir / "conftest.py"
        ).exists():
            conventions["test_framework"] = "pytest"

        return conventions

    def map_architecture(self, project_dir: Path) -> dict[str, Any]:
        """Map the project architecture."""
        architecture: dict[str, Any] = {}

        # Count files and directories
        file_count = 0
        dir_count = 0
        total_loc = 0

        source_exts = {".py", ".ts", ".js", ".tsx", ".jsx", ".swift", ".rs", ".go"}
        try:
            for path in project_dir.rglob("*"):
                if any(
                    part.startswith(".") or part == "node_modules"
                    for part in path.relative_to(project_dir).parts
                ):
                    continue
                if path.is_file():
                    file_count += 1
                    if path.suffix in source_exts:
                        try:
                            total_loc += len(path.read_text(errors="replace").split("\n"))
                        except OSError:
                            pass
                elif path.is_dir():
                    dir_count += 1
        except (PermissionError, OSError):
            pass

        architecture["files"] = file_count
        architecture["directories"] = dir_count
        architecture["total_loc"] = total_loc

        # Detect top-level structure
        top_dirs = [
            d.name for d in project_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        architecture["top_level_dirs"] = top_dirs[:20]

        return architecture
