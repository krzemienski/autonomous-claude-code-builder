"""
Mock Detector Hook
===================

Pre-tool-use hook that blocks creation of mock/stub/test code.
Enforces the Iron Rule: no mocks, no test files, no stubs.
"""

import re
from typing import Any

# Content patterns that indicate mock/test code
MOCK_PATTERNS = [
    re.compile(r"mock\.", re.IGNORECASE),
    re.compile(r"Mock\("),
    re.compile(r"unittest\.mock"),
    re.compile(r"from unittest import mock"),
    re.compile(r"jest\.mock"),
    re.compile(r"jest\.fn"),
    re.compile(r"sinon\."),
    re.compile(r"nock\("),
    re.compile(r"@Mock"),
    re.compile(r"Mockito\."),
    re.compile(r"@patch"),
    re.compile(r"\.stub\("),
    re.compile(r"\.fake\("),
    re.compile(r"monkeypatch"),
    re.compile(r"in.memory.*database", re.IGNORECASE),
    re.compile(r":memory:"),
    re.compile(r"mongomock"),
    re.compile(r"TEST_MODE"),
    re.compile(r"test_mode"),
    re.compile(r"TESTING\s*=\s*[Tt]rue"),
]

# File path patterns that indicate test files
TEST_FILE_PATTERNS = [
    re.compile(r"\.test\.\w+$"),
    re.compile(r"\.spec\.\w+$"),
    re.compile(r"_test\.\w+$"),
    re.compile(r"^test_\w+\.\w+$"),
    re.compile(r"Tests\.\w+$"),
]


def scan_content_for_mocks(content: str) -> list[str]:
    """
    Scan content and return list of detected mock patterns.

    Args:
        content: Source code content to scan.

    Returns:
        List of pattern descriptions that matched.
    """
    found: list[str] = []
    for pattern in MOCK_PATTERNS:
        if pattern.search(content):
            found.append(pattern.pattern)
    return found


def scan_file_path_for_test(path: str) -> bool:
    """
    Check if file path matches test file patterns.

    Args:
        path: File path (just the filename or full path).

    Returns:
        True if the path looks like a test file.
    """
    # Extract just the filename
    filename = path.rsplit("/", 1)[-1] if "/" in path else path
    filename = path.rsplit("\\", 1)[-1] if "\\" in filename else filename

    for pattern in TEST_FILE_PATTERNS:
        if pattern.search(filename):
            return True
    return False


async def mock_detection_hook(
    input_data: dict[str, Any],
    tool_use_id: str | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """
    Pre-tool-use hook that blocks creation of mock/stub/test code.

    Scans Write and Edit tool inputs for mock patterns.
    Returns block decision if pattern found.
    """
    # Check for file path in tool input
    file_path = input_data.get("file_path", "") or input_data.get("path", "")
    if file_path and scan_file_path_for_test(file_path):
        return {
            "decision": "block",
            "reason": (
                f"Iron Rule: Cannot create test file '{file_path}'. "
                "Fix the real system instead."
            ),
        }

    # Check content in Write tool
    content = input_data.get("content", "")
    if content:
        patterns = scan_content_for_mocks(content)
        if patterns:
            return {
                "decision": "block",
                "reason": (
                    f"Iron Rule: Mock/test patterns detected: {patterns[:3]}. "
                    "Fix the real system instead."
                ),
            }

    # Check new_string in Edit tool
    new_string = input_data.get("new_string", "")
    if new_string:
        patterns = scan_content_for_mocks(new_string)
        if patterns:
            return {
                "decision": "block",
                "reason": (
                    f"Iron Rule: Mock/test patterns detected: {patterns[:3]}. "
                    "Fix the real system instead."
                ),
            }

    return {}
