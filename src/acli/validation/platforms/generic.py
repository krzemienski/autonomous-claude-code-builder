"""Generic validator — runs any command via subprocess."""

import subprocess
from pathlib import Path
from typing import Any


class GenericValidator:
    """Fallback validator that runs any shell command."""

    async def validate(
        self,
        command: str,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Run any command and capture output as evidence."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "generic-output.txt"

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60,
        )
        output = f"$ {command}\n\n{result.stdout}"
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
        output += f"\n--- EXIT CODE: {result.returncode} ---\n"
        evidence_path.write_text(output)

        return {
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"exit={result.returncode}",
        }
