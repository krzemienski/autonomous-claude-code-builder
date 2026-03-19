"""API validation via curl against running servers."""
import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Any


class APIValidator:
    """Validates API endpoints via real HTTP requests."""

    async def validate_endpoint(
        self,
        url: str,
        method: str = "GET",
        body: dict[str, Any] | None = None,
        expected_status: int = 200,
        evidence_dir: Path = Path("evidence"),
    ) -> dict[str, Any]:
        """Hit a real endpoint and validate response status."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "api-validation.json"

        cmd = f'curl -s -o /dev/null -w "%{{http_code}}" -X {method} {url}'
        if body:
            cmd = (
                f'curl -s -w "\\n%{{http_code}}" -X {method} '
                f'-H "Content-Type: application/json" '
                f"-d '{json.dumps(body)}' {url}"
            )

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
            ),
        )

        status_code = result.stdout.strip().split("\\n")[-1] if result.stdout else "0"
        evidence_path.write_text(json.dumps({
            "url": url, "method": method, "status_code": status_code,
            "stdout": result.stdout, "stderr": result.stderr,
        }, indent=2))

        passed = status_code == str(expected_status)
        return {
            "status": "PASS" if passed else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"status={status_code}, expected={expected_status}",
        }

    async def health_check_poll(self, url: str, timeout: int = 60) -> bool:
        """Poll a health endpoint until it returns 200 or timeout."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                result = subprocess.run(
                    f'curl -s -o /dev/null -w "%{{http_code}}" {url}',
                    shell=True, capture_output=True, text=True, timeout=5,
                )
                if result.stdout.strip() == "200":
                    return True
            except (subprocess.TimeoutExpired, OSError):
                pass
            await asyncio.sleep(2)
        return False
