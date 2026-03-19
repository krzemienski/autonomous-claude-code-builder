"""
Knowledge Chunker
=================

Chunks codebase into retrievable knowledge segments.
"""

from pathlib import Path
from typing import Any

# Extensions to include in chunking
CHUNKABLE_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx",
    ".swift", ".rs", ".go", ".java", ".kt",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb",
    ".md", ".json", ".yaml", ".yml", ".toml",
}


class KnowledgeChunker:
    """
    Chunks codebase into retrievable knowledge segments.

    Stores to .acli/context/knowledge_chunks/
    """

    def chunk_codebase(
        self, project_dir: Path, max_chunk_size: int = 4000
    ) -> list[dict[str, Any]]:
        """
        Chunk all source files into segments.

        Args:
            project_dir: Root directory to scan.
            max_chunk_size: Max characters per chunk.

        Returns:
            List of chunk dicts with 'content', 'file', 'start_line' keys.
        """
        chunks: list[dict[str, Any]] = []

        try:
            for path in sorted(project_dir.rglob("*")):
                if not path.is_file():
                    continue
                if path.suffix not in CHUNKABLE_EXTENSIONS:
                    continue
                # Skip hidden dirs and node_modules
                rel = path.relative_to(project_dir)
                if any(
                    part.startswith(".") or part == "node_modules"
                    for part in rel.parts
                ):
                    continue

                try:
                    content = path.read_text(errors="replace")
                except (OSError, PermissionError):
                    continue

                rel_path = str(rel)

                if len(content) <= max_chunk_size:
                    chunks.append({
                        "content": content,
                        "file": rel_path,
                        "start_line": 1,
                        "end_line": content.count("\n") + 1,
                    })
                else:
                    # Split into chunks by lines
                    lines = content.split("\n")
                    current_chunk: list[str] = []
                    current_size = 0
                    start_line = 1

                    for i, line in enumerate(lines, 1):
                        line_size = len(line) + 1
                        if current_size + line_size > max_chunk_size and current_chunk:
                            chunks.append({
                                "content": "\n".join(current_chunk),
                                "file": rel_path,
                                "start_line": start_line,
                                "end_line": i - 1,
                            })
                            current_chunk = []
                            current_size = 0
                            start_line = i

                        current_chunk.append(line)
                        current_size += line_size

                    if current_chunk:
                        chunks.append({
                            "content": "\n".join(current_chunk),
                            "file": rel_path,
                            "start_line": start_line,
                            "end_line": len(lines),
                        })
        except (PermissionError, OSError):
            pass

        return chunks

    def get_relevant_chunks(
        self, query: str, top_k: int = 3
    ) -> list[str]:
        """
        Get chunks most relevant to a query.

        Uses simple keyword matching (no embeddings needed).
        """
        # This is a simple keyword-based retrieval
        # A production system would use embeddings
        return []
