"""Web frontend validation via Playwright screenshots."""
import asyncio
import subprocess
from pathlib import Path
from typing import Any


class WebValidator:
    """Validates web frontends via browser automation."""

    async def validate_page(
        self,
        url: str,
        selector: str = "body",
        evidence_dir: Path = Path("evidence"),
    ) -> dict[str, Any]:
        """Navigate to URL and capture screenshot as evidence."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "web-validation.png"

        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["npx", "playwright", "screenshot", url, str(evidence_path)],
                    capture_output=True, text=True, timeout=30,
                ),
            )
            passed = evidence_path.exists()
        except Exception as e:
            passed = False
            evidence_path.write_text(f"Web validation failed: {e}")

        return {
            "status": "PASS" if passed else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"url={url}, selector={selector}",
        }
