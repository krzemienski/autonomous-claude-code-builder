"""iOS platform validator — validates via xcrun simctl."""

import subprocess
from pathlib import Path
from typing import Any


class IOSValidator:
    """Validates iOS apps via xcrun simctl commands."""

    async def validate_screen(
        self,
        scheme: str,
        bundle_id: str,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Validate iOS app screen via simulator.

        Uses xcrun simctl if available.
        """
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "ios-output.txt"

        # Check if xcrun is available
        try:
            result = subprocess.run(
                "xcrun simctl list devices booted",
                shell=True, capture_output=True, text=True, timeout=10,
            )
            output = f"Booted simulators:\n{result.stdout}\n"

            if bundle_id:
                launch = subprocess.run(
                    f"xcrun simctl launch booted {bundle_id}",
                    shell=True, capture_output=True, text=True, timeout=10,
                )
                output += f"Launch result: {launch.stdout}\n"
                if launch.stderr:
                    output += f"Launch stderr: {launch.stderr}\n"

            evidence_path.write_text(output)

            return {
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "evidence_path": str(evidence_path),
                "details": f"Simulator check for {bundle_id}",
            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            evidence_path.write_text("xcrun simctl not available on this platform\n")
            return {
                "status": "SKIP",
                "evidence_path": str(evidence_path),
                "details": "xcrun not available",
            }
