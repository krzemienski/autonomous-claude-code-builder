"""API platform validator — validates HTTP endpoints via real curl."""

import subprocess
import time
from pathlib import Path
from typing import Any


class APIValidator:
    """Validates API endpoints by making real HTTP requests."""

    async def validate_endpoint(
        self,
        url: str,
        method: str,
        body: str | None,
        expected_status: int,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Run real curl command against an endpoint."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "api-output.txt"

        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -X {method} {url}"
        if body:
            cmd += f" -H 'Content-Type: application/json' -d '{body}'"

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30,
        )
        status_code = result.stdout.strip()
        output = f"$ {cmd}\nHTTP Status: {status_code}\n"
        if result.stderr:
            output += f"STDERR: {result.stderr}\n"
        evidence_path.write_text(output)

        return {
            "status": "PASS" if status_code == str(expected_status) else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"HTTP {status_code} (expected {expected_status})",
        }

    async def health_check_poll(
        self, url: str, timeout: int = 30, interval: int = 2,
    ) -> dict[str, Any]:
        """Poll a health endpoint until it responds 200 or timeout."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    f"curl -s -o /dev/null -w '%{{http_code}}' {url}",
                    shell=True, capture_output=True, text=True, timeout=5,
                )
                if result.stdout.strip() == "200":
                    return {"status": "PASS", "details": "Health check passed"}
            except subprocess.TimeoutExpired:
                pass
            time.sleep(interval)
        return {"status": "FAIL", "details": f"Health check timed out after {timeout}s"}
