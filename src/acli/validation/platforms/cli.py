"""CLI Validator — validates CLI tools via execution."""

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
        """
        Run a command and validate its output.

        Args:
            command: Shell command to execute.
            expected_exit: Expected exit code (usually 0).
            expected_output: Optional substring expected in stdout.
            evidence_dir: Directory to save evidence files.

        Returns:
            Dict with status, evidence_path, and details.
        """
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "cli-validation.txt"

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
            output = "TIMEOUT"
            exit_code = -1
        except Exception as e:
            output = str(e)
            exit_code = -1

        evidence_path.write_text(
            f"Command: {command}\n"
            f"Exit Code: {exit_code}\n"
            f"Expected Exit: {expected_exit}\n"
            f"---\n{output}"
        )

        passed = exit_code == expected_exit
        if passed and expected_output:
            passed = expected_output in output

        return {
            "status": "PASS" if passed else "FAIL",
            "evidence_path": str(evidence_path),
            "details": output[:500],
            "exit_code": exit_code,
        }
