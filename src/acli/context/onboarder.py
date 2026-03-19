"""Brownfield codebase onboarding."""

from pathlib import Path
from typing import Any

from ..core.streaming import StreamingHandler
from .chunker import SKIP_DIRS, SOURCE_EXTENSIONS, KnowledgeChunker
from .store import ContextStore


class BrownfieldOnboarder:
    """Full codebase analysis and context population."""

    async def onboard(
        self, project_dir: Path, streaming: StreamingHandler,
    ) -> dict[str, Any]:
        """Run full onboarding sequence."""
        store = ContextStore(project_dir)
        store.initialize()

        await streaming.handle_context_update("onboarding", "Starting codebase analysis")

        tech_stack = self.detect_tech_stack(project_dir)
        store.store_tech_stack(tech_stack)
        await streaming.handle_context_update("tech_stack", str(tech_stack))

        conventions = self.detect_conventions(project_dir)
        store.store_conventions(conventions)

        architecture = self.map_architecture(project_dir)
        store.store_analysis(architecture)
        await streaming.handle_context_update(
            "analysis", f"{architecture.get('total_files', 0)} files mapped",
        )

        chunker = KnowledgeChunker()
        chunks = chunker.chunk_codebase(project_dir)
        await streaming.handle_context_update(
            "chunks", f"{len(chunks)} knowledge chunks created",
        )

        return {"tech_stack": tech_stack, "architecture": architecture, "chunks": len(chunks)}

    def detect_tech_stack(self, project_dir: Path) -> dict[str, Any]:
        """Detect technology stack from project files."""
        stack: dict[str, Any] = {}
        if (project_dir / "pyproject.toml").exists() or (project_dir / "setup.py").exists():
            stack["language"] = "Python"
        if (project_dir / "package.json").exists():
            stack["language"] = stack.get("language", "JavaScript")
            stack["runtime"] = "Node.js"
        if (project_dir / "Cargo.toml").exists():
            stack["language"] = "Rust"
        if (project_dir / "Dockerfile").exists():
            stack["containerization"] = "Docker"
        if (
            (project_dir / "docker-compose.yml").exists()
            or (project_dir / "docker-compose.yaml").exists()
        ):
            stack["orchestration"] = "Docker Compose"
        if (project_dir / "poetry.lock").exists():
            stack["package_manager"] = "Poetry"
        if (project_dir / "requirements.txt").exists():
            stack["package_manager"] = stack.get("package_manager", "pip")
        return stack

    def detect_conventions(self, project_dir: Path) -> dict[str, Any]:
        """Detect code conventions from existing files."""
        conventions: dict[str, Any] = {}
        py_files = list(project_dir.rglob("*.py"))
        py_files = [f for f in py_files if not any(s in f.parts for s in SKIP_DIRS)]
        if py_files:
            sample = py_files[0].read_text(errors="replace")
            conventions["has_type_hints"] = ": " in sample and " -> " in sample
            conventions["has_docstrings"] = '"""' in sample or "'''" in sample
            conventions["uses_async"] = "async " in sample
        return conventions

    def map_architecture(self, project_dir: Path) -> dict[str, Any]:
        """Map file structure and architecture."""
        total_files = 0
        total_loc = 0
        file_types: dict[str, int] = {}
        directories: list[str] = []

        for path in project_dir.rglob("*"):
            if any(s in path.parts for s in SKIP_DIRS):
                continue
            if path.is_dir():
                rel = str(path.relative_to(project_dir))
                if rel != ".":
                    directories.append(rel)
            elif path.is_file() and path.suffix in SOURCE_EXTENSIONS:
                total_files += 1
                total_loc += sum(1 for _ in open(path, errors="replace"))
                ext = path.suffix
                file_types[ext] = file_types.get(ext, 0) + 1

        return {
            "total_files": total_files,
            "total_loc": total_loc,
            "file_types": file_types,
            "directories": directories[:50],
        }
