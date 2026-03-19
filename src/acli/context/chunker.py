"""Knowledge chunker for splitting codebases into searchable segments.

Walks the project directory tree, reads source files, and splits them
into manageable chunks with file and line metadata. Supports simple
keyword-based retrieval without requiring a vector database.
"""

from collections.abc import Iterator
from pathlib import Path

# Directories to skip during chunking
_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "__pycache__", ".acli",
    ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
    "dist", "build", ".next", ".nuxt",
})

# File extensions considered as source code / text
_SOURCE_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go",
    ".java", ".kt", ".rb", ".php", ".c", ".cpp", ".h",
    ".cs", ".swift", ".vue", ".svelte", ".html", ".css",
    ".scss", ".less", ".sql", ".sh", ".bash", ".zsh",
    ".yaml", ".yml", ".toml", ".json", ".md", ".txt",
    ".cfg", ".ini", ".env", ".xml", ".graphql",
})


class KnowledgeChunker:
    """Splits a codebase into searchable text chunks.

    Walks the project tree, reads text-based source files, and
    produces chunks with file path and line range metadata.
    """

    def chunk_codebase(
        self,
        project_dir: Path,
        max_chunk_size: int = 4000,
    ) -> list[dict[str, str | int]]:
        """Walk project and split source files into chunks.

        Args:
            project_dir: Root directory to scan.
            max_chunk_size: Maximum characters per chunk.

        Returns:
            List of chunk dicts, each containing 'file', 'content',
            'start_line', and 'end_line'.
        """
        chunks: list[dict[str, str | int]] = []

        for file_path in self._iter_source_files(project_dir):
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError):
                continue

            rel_path = str(file_path.relative_to(project_dir))
            lines = text.splitlines(keepends=True)
            file_chunks = self._split_lines(lines, max_chunk_size, rel_path)
            chunks.extend(file_chunks)

        return chunks

    def get_relevant_chunks(
        self,
        query: str,
        chunks: list[dict[str, str | int]] | None = None,
        top_k: int = 3,
    ) -> list[str]:
        """Find chunks most relevant to a query via keyword matching.

        Args:
            query: Search query string.
            chunks: Pre-computed chunk list. If None, returns empty.
            top_k: Number of top results to return.

        Returns:
            List of chunk content strings ranked by keyword overlap.
        """
        if not chunks:
            return []

        query_terms = set(query.lower().split())
        scored: list[tuple[int, str]] = []

        for chunk in chunks:
            content = str(chunk["content"]).lower()
            score = sum(1 for term in query_terms if term in content)
            if score > 0:
                scored.append((score, str(chunk["content"])))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for _, content in scored[:top_k]]

    def _iter_source_files(self, project_dir: Path) -> Iterator[Path]:
        """Yield source file paths, skipping ignored directories.

        Args:
            project_dir: Root directory to scan.

        Yields:
            Path objects for each source file found.
        """
        for item in project_dir.iterdir():
            if item.is_dir():
                if item.name in _SKIP_DIRS:
                    continue
                yield from self._iter_source_files(item)
            elif item.is_file() and item.suffix in _SOURCE_EXTENSIONS:
                yield item

    def _split_lines(
        self,
        lines: list[str],
        max_size: int,
        rel_path: str,
    ) -> list[dict[str, str | int]]:
        """Split file lines into chunks respecting the size limit.

        Args:
            lines: All lines from the file (with line endings).
            max_size: Maximum characters per chunk.
            rel_path: Relative file path for metadata.

        Returns:
            List of chunk dicts with file, content, start_line, end_line.
        """
        chunks: list[dict[str, str | int]] = []
        current_lines: list[str] = []
        current_size = 0
        start_line = 1

        for i, line in enumerate(lines, start=1):
            if current_size + len(line) > max_size and current_lines:
                chunks.append({
                    "file": rel_path,
                    "content": "".join(current_lines),
                    "start_line": start_line,
                    "end_line": i - 1,
                })
                current_lines = []
                current_size = 0
                start_line = i

            current_lines.append(line)
            current_size += len(line)

        if current_lines:
            chunks.append({
                "file": rel_path,
                "content": "".join(current_lines),
                "start_line": start_line,
                "end_line": start_line + len(current_lines) - 1,
            })

        return chunks
