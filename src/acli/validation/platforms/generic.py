"""Generic Validator — fallback for untyped platforms."""

import subprocess
from pathlib import Path
from typing import Any


class GenericValidator:
    """Fallback validator for untyped platforms."""

    async def validate(
        self,
        command: str,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Run a validation command and capture output."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "generic-validation.txt"

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
            f"---\n{output}"
        )

        return {
            "status": "PASS" if exit_code == 0 else "FAIL",
            "evidence_path": str(evidence_path),
            "details": output[:500],
        }
