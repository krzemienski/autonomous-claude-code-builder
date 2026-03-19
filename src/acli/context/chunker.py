"""Codebase knowledge chunking for retrieval."""

from pathlib import Path
from typing import Any

SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".swift", ".rs", ".go", ".java"}
SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", ".acli"}


class KnowledgeChunker:
    """Chunks codebase into retrievable segments."""

    def chunk_codebase(
        self, project_dir: Path, max_chunk_size: int = 4000,
    ) -> list[dict[str, Any]]:
        """Segment all source files into chunks."""
        chunks: list[dict[str, Any]] = []
        for path in sorted(project_dir.rglob("*")):
            if not path.is_file() or path.suffix not in SOURCE_EXTENSIONS:
                continue
            if any(skip in path.parts for skip in SKIP_DIRS):
                continue
            content = path.read_text(errors="replace")
            rel_path = str(path.relative_to(project_dir))
            if len(content) <= max_chunk_size:
                chunks.append({"path": rel_path, "content": content, "chunk_index": 0})
            else:
                lines = content.splitlines(keepends=True)
                current_chunk: list[str] = []
                current_size = 0
                chunk_idx = 0
                for line in lines:
                    current_chunk.append(line)
                    current_size += len(line)
                    if current_size >= max_chunk_size:
                        chunks.append({
                            "path": rel_path,
                            "content": "".join(current_chunk),
                            "chunk_index": chunk_idx,
                        })
                        current_chunk = []
                        current_size = 0
                        chunk_idx += 1
                if current_chunk:
                    chunks.append({
                        "path": rel_path,
                        "content": "".join(current_chunk),
                        "chunk_index": chunk_idx,
                    })
        return chunks

    def get_relevant_chunks(self, query: str, top_k: int = 3) -> list[str]:
        """Simple keyword-based chunk retrieval (no embeddings)."""
        # Placeholder — returns empty until embeddings or BM25 added
        return []
