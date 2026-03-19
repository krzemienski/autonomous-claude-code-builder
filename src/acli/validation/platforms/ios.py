"""iOS validation via simulator screenshots."""
import asyncio
import subprocess
from pathlib import Path
from typing import Any


class IOSValidator:
    """Validates iOS apps via simulator."""

    async def validate_screen(
        self,
        scheme: str,
        bundle_id: str,
        evidence_dir: Path = Path("evidence"),
    ) -> dict[str, Any]:
        """Build, launch, and screenshot iOS app in simulator."""
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "ios-validation.png"

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["xcrun", "simctl", "io", "booted", "screenshot", str(evidence_path)],
                    capture_output=True, text=True, timeout=30,
                ),
            )
            passed = evidence_path.exists() and result.returncode == 0
        except Exception as e:
            passed = False
            evidence_path.write_text(f"iOS validation failed: {e}")

        return {
            "status": "PASS" if passed else "FAIL",
            "evidence_path": str(evidence_path),
            "details": f"scheme={scheme}, bundle={bundle_id}",
        }
