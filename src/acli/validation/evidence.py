"""
Evidence Collector
==================

Captures, saves, and catalogs validation evidence.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvidenceCollector:
    """Captures, saves, and catalogs validation evidence."""

    def __init__(self, evidence_dir: Path) -> None:
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
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def save_command_output(
        self, name: str, command: str
    ) -> tuple[Path, int]:
        """
        Execute a command and save its output as evidence.

        Returns:
            Tuple of (evidence file path, exit code).
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = result.stdout + result.stderr
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            output = "TIMEOUT: Command exceeded 120s"
            exit_code = -1
        except Exception as e:
            output = f"ERROR: {e}"
            exit_code = -1

        path = self.evidence_dir / f"{name}.txt"
        path.write_text(
            f"Command: {command}\n"
            f"Exit Code: {exit_code}\n"
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
            f"---\n"
            f"{output}"
        )
        return path, exit_code

    def list_evidence(self) -> list[dict[str, Any]]:
        """List all evidence files in the directory."""
        evidence: list[dict[str, Any]] = []
        if not self.evidence_dir.exists():
            return evidence

        for path in sorted(self.evidence_dir.iterdir()):
            if path.is_file():
                evidence.append({
                    "name": path.stem,
                    "path": str(path),
                    "size": path.stat().st_size,
                    "type": path.suffix.lstrip("."),
                })
        return evidence

    def get_evidence(self, name: str) -> str | None:
        """Read evidence content by name."""
        for ext in [".txt", ".json"]:
            path = self.evidence_dir / f"{name}{ext}"
            if path.exists():
                return path.read_text()
        return None
