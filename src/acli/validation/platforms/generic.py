"""Generic fallback validator."""
import asyncio
import subprocess
from pathlib import Path
from typing import Any


class GenericValidator:
    """Fallback validator for untyped platforms."""

    async def validate(
        self,
        command: str,
        evidence_dir: Path = Path("evidence"),
    ) -> dict[str, Any]:
        """Run any command and check exit code."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "generic-validation.txt"

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=60,
            ),
        )

        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        evidence_path.write_text(output)

        return {
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"exit={result.returncode}, command={command[:50]}",
        }
