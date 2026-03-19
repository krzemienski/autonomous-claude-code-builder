"""
Mock Detection Hook
===================

Pre-tool-use hook that blocks creation of mock/stub/test code.
Scans Write and Edit tool inputs for mock patterns.
"""

import re
from pathlib import PurePosixPath
from typing import Any

# Regex patterns that indicate mock/test code
MOCK_PATTERNS: list[str] = [
    r"mock\.",
    r"Mock\(",
    r"unittest\.mock",
    r"from unittest import mock",
    r"jest\.mock",
    r"jest\.fn",
    r"sinon\.",
    r"nock\(",
    r"@Mock",
    r"Mockito\.",
    r"@patch",
    r"\.stub\(",
    r"\.fake\(",
    r"monkeypatch",
    r"in.memory.*database",
    r":memory:",
    r"mongomock",
    r"TEST_MODE",
    r"test_mode",
    r"TESTING\s*=\s*[Tt]rue",
]

# File path patterns that indicate test files
TEST_PATH_PATTERNS: list[str] = [
    r"\.test\.\w+$",
    r"\.spec\.\w+$",
    r"_test\.\w+$",
    r"^test_\w+\.\w+$",
    r"Tests\.swift$",
    r"__tests__/",
]


def scan_content_for_mocks(content: str) -> list[str]:
    """Scan content and return list of detected mock pattern descriptions."""
    found: list[str] = []
    for pattern in MOCK_PATTERNS:
        if re.search(pattern, content):
            found.append(pattern)
    return found


def scan_file_path_for_test(path: str) -> bool:
    """Check if file path matches test file patterns."""
    filename = PurePosixPath(path).name
    full_path = path

    for pattern in TEST_PATH_PATTERNS:
        if re.search(pattern, filename) or re.search(pattern, full_path):
            return True
    return False


async def mock_detection_hook(
    input_data: dict[str, Any],
    tool_use_id: str | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """
    Pre-tool-use hook that blocks creation of mock/stub/test code.

    Designed for Write and Edit tools. Scans file path and content
    for mock patterns. Returns block decision if pattern found.
    """
    # Check file path
    file_path = input_data.get("file_path", "") or input_data.get("path", "")
    if file_path and scan_file_path_for_test(file_path):
        return {
            "decision": "block",
            "reason": (
                f"MOCK DETECTED: File path '{file_path}' matches test file pattern. "
                "Fix the REAL system instead."
            ),
        }

    # Check content
    content = input_data.get("content", "") or input_data.get("new_string", "")
    if content:
        patterns = scan_content_for_mocks(content)
        if patterns:
            return {
                "decision": "block",
                "reason": (
                    f"MOCK DETECTED: Content contains mock patterns: {patterns}. "
                    "Fix the REAL system instead."
                ),
            }

    return {"decision": "allow"}
