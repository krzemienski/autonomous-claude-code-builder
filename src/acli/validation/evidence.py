"""Evidence collector — captures real command output and artifacts."""

import json
import subprocess
from pathlib import Path
from typing import Any


class EvidenceCollector:
    """Captures and stores validation evidence from real system execution."""

    def __init__(self, evidence_dir: Path) -> None:
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def save_text(self, name: str, content: str) -> Path:
        """Save text evidence."""
        path = self.evidence_dir / f"{name}.txt"
        path.write_text(content)
        return path

    def save_json(self, name: str, data: dict[str, Any]) -> Path:
        """Save JSON evidence."""
        path = self.evidence_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def save_command_output(self, name: str, command: str) -> tuple[Path, int]:
        """Run REAL command and capture output as evidence."""
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = f"$ {command}\n\n{result.stdout}"
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
        output += f"\n--- EXIT CODE: {result.returncode} ---\n"

        path = self.evidence_dir / f"{name}.txt"
        path.write_text(output)
        return path, result.returncode

    def list_evidence(self) -> list[dict[str, Any]]:
        """List all evidence files."""
        return [
            {"name": f.stem, "path": str(f), "size": f.stat().st_size}
            for f in sorted(self.evidence_dir.iterdir())
            if f.is_file()
        ]

    def get_evidence(self, name: str) -> str | None:
        """Read evidence file content."""
        for ext in (".txt", ".json"):
            path = self.evidence_dir / f"{name}{ext}"
            if path.exists():
                return path.read_text()
        return None
