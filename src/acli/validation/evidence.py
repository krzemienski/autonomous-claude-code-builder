"""Evidence collection for validation gates."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class EvidenceCollector:
    """Captures, saves, and catalogs validation evidence."""

    def __init__(self, evidence_dir: Path) -> None:
        """Initialize evidence collector with target directory."""
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def save_text(self, name: str, content: str) -> Path:
        """Save text evidence to a file."""
        path = self.evidence_dir / f"{name}.txt"
        path.write_text(content)
        return path

    def save_json(self, name: str, data: dict[str, Any]) -> Path:
        """Save JSON evidence to a file."""
        path = self.evidence_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2))
        return path

    def save_command_output(self, name: str, command: str) -> tuple[Path, int]:
        """Run a real shell command and save output as evidence. Returns (path, exit_code)."""
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
        path = self.save_text(name, output)
        return path, result.returncode

    def list_evidence(self) -> list[dict[str, Any]]:
        """List all evidence files with metadata."""
        if not self.evidence_dir.exists():
            return []
        entries = []
        for f in sorted(self.evidence_dir.iterdir()):
            if f.is_file():
                entries.append({
                    "name": f.stem,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=UTC
                    ).isoformat(),
                })
        return entries

    def get_evidence(self, name: str) -> str | None:
        """Read evidence content by name."""
        for ext in [".txt", ".json"]:
            path = self.evidence_dir / f"{name}{ext}"
            if path.exists():
                return path.read_text()
        return None
