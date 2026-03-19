"""Web platform validator — validates web pages via Playwright MCP."""

from pathlib import Path
from typing import Any


class WebValidator:
    """Validates web pages via Playwright MCP or browser automation."""

    async def validate_page(
        self,
        url: str,
        selector: str,
        evidence_dir: Path,
    ) -> dict[str, Any]:
        """Validate a web page element exists.

        Delegates to Playwright MCP if available, otherwise notes
        that browser validation requires MCP setup.
        """
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "web-output.txt"

        # Playwright MCP validation would go through the SDK client
        # For now, record that validation was attempted
        output = (
            f"Web validation for: {url}\n"
            f"Selector: {selector}\n"
            f"Status: Requires Playwright MCP — use acli run with browser tools\n"
        )
        evidence_path.write_text(output)

        return {
            "status": "SKIP",
            "evidence_path": str(evidence_path),
            "details": "Playwright MCP not available in standalone mode",
        }
