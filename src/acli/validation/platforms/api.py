"""API Validator — validates API endpoints via curl."""

import asyncio
import subprocess
from pathlib import Path
from typing import Any


class APIValidator:
    """Validates API endpoints via curl against running servers."""

    async def validate_endpoint(
        self,
        url: str,
        method: str,
        body: dict[str, Any] | None,
        expected_status: int,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Validate an API endpoint via curl."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "api-validation.txt"

        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -X {method} {url}"
        if body:
            import json
            cmd += f" -H 'Content-Type: application/json' -d '{json.dumps(body)}'"

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            status_code = int(result.stdout.strip().strip("'"))
            passed = status_code == expected_status
        except (subprocess.TimeoutExpired, ValueError):
            status_code = 0
            passed = False

        evidence_path.write_text(
            f"URL: {url}\nMethod: {method}\n"
            f"Status: {status_code}\nExpected: {expected_status}\n"
        )

        return {
            "status": "PASS" if passed else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"HTTP {status_code}",
        }

    async def health_check_poll(
        self, url: str, timeout: int = 60
    ) -> bool:
        """Poll a health endpoint until it responds or times out."""
        elapsed = 0
        interval = 2
        while elapsed < timeout:
            try:
                result = subprocess.run(
                    f"curl -s -o /dev/null -w '%{{http_code}}' {url}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout.strip().strip("'") == "200":
                    return True
            except (subprocess.TimeoutExpired, Exception):
                pass
            await asyncio.sleep(interval)
            elapsed += interval
        return False
