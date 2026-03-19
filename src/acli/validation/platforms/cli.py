"""CLI platform validator — validates command-line tools via real subprocess."""

import subprocess
from pathlib import Path
from typing import Any


class CLIValidator:
    """Validates CLI commands by running them for real."""

    async def validate_command(
        self,
        command: str,
        expected_exit: int,
        expected_output: str,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Run a real command and validate exit code + output pattern."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "cli-output.txt"

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60,
        )
        output = f"$ {command}\n\n{result.stdout}"
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
        output += f"\n--- EXIT CODE: {result.returncode} ---\n"
        evidence_path.write_text(output)

        exit_ok = result.returncode == expected_exit
        output_ok = expected_output in result.stdout

        return {
            "status": "PASS" if (exit_ok and output_ok) else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"exit={result.returncode} (expected {expected_exit}), "
            f"output_match={'yes' if output_ok else 'no'}",
        }
