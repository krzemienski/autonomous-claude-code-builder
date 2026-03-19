"""CLI validation via real binary/module execution."""
import asyncio
import subprocess
from pathlib import Path
from typing import Any


class CLIValidator:
    """Validates CLI tools via binary/module execution."""

    async def validate_command(
        self,
        command: str,
        expected_exit: int,
        expected_output: str | None,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Run command and validate exit code + optional output match."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "cli-validation.txt"

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=60,
            ),
        )

        output = result.stdout + (f"\nSTDERR: {result.stderr}" if result.stderr else "")
        evidence_path.write_text(output)

        passed = result.returncode == expected_exit
        if passed and expected_output:
            passed = expected_output in result.stdout

        return {
            "status": "PASS" if passed else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"exit={result.returncode}, expected={expected_exit}",
        }
