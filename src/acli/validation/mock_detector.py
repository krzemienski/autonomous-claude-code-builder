"""Mock detection hook — blocks test files and mock patterns in agent output."""

import re
from typing import Any

# Content patterns that indicate mock/test code
_MOCK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Python mocks
    (re.compile(r"from\s+unittest\.mock\s+import"), "unittest.mock import"),
    (re.compile(r"mock\.patch\("), "mock.patch usage"),
    (re.compile(r"@patch\("), "@patch decorator"),
    (re.compile(r"MagicMock\("), "MagicMock usage"),
    (re.compile(r"from\s+unittest\s+import"), "unittest import"),
    (re.compile(r"import\s+pytest"), "pytest import"),
    (re.compile(r"@pytest\.fixture"), "pytest fixture"),
    # JavaScript mocks
    (re.compile(r"jest\.mock\("), "jest.mock usage"),
    (re.compile(r"jest\.fn\("), "jest.fn usage"),
    (re.compile(r"sinon\.(stub|spy|mock)\("), "sinon mock"),
    (re.compile(r"vi\.mock\("), "vitest mock"),
    # In-memory databases
    (re.compile(r":memory:", re.IGNORECASE), "in-memory database"),
    (re.compile(r"sqlite.*:memory:", re.IGNORECASE), "SQLite in-memory"),
    # Test mode flags
    (re.compile(r"TEST_MODE\s*=\s*True", re.IGNORECASE), "TEST_MODE flag"),
    (re.compile(r"TESTING\s*=\s*True", re.IGNORECASE), "TESTING flag"),
    # Java/Kotlin mocks
    (re.compile(r"@Mock\b"), "@Mock annotation"),
    (re.compile(r"Mockito\.(when|verify|mock)\("), "Mockito usage"),
]

# File path patterns that indicate test files
_TEST_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"test_\w+\.py$"),
    re.compile(r"\w+_test\.py$"),
    re.compile(r"\w+\.test\.\w+$"),
    re.compile(r"\w+\.spec\.\w+$"),
    re.compile(r"\w+Tests\.swift$"),
    re.compile(r"\w+_test\.go$"),
    re.compile(r"__tests__/"),
    re.compile(r"tests?/test_"),
]


def scan_content_for_mocks(content: str) -> list[str]:
    """Scan content for mock/test patterns. Returns list of matched pattern names."""
    matches: list[str] = []
    for pattern, name in _MOCK_PATTERNS:
        if pattern.search(content):
            matches.append(name)
    return matches


def scan_file_path_for_test(path: str) -> bool:
    """Return True if path matches test file naming conventions."""
    return any(p.search(path) for p in _TEST_PATH_PATTERNS)


async def mock_detection_hook(
    input_data: dict[str, Any],
    tool_use_id: str | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """PreToolUse hook for Write/Edit — blocks mock/test code creation."""
    # Check file path
    file_path = input_data.get("file_path", "") or input_data.get("path", "")
    if file_path and scan_file_path_for_test(file_path):
        return {
            "continue_": False,
            "decision": "block",
            "reason": f"IRON RULE: Blocked test file creation at {file_path}. "
            "Use functional validation instead of unit tests.",
        }

    # Check content
    content = input_data.get("content", "") or input_data.get("new_string", "")
    if content:
        mocks = scan_content_for_mocks(content)
        if mocks:
            return {
                "continue_": False,
                "decision": "block",
                "reason": f"IRON RULE: Blocked mock pattern(s): {', '.join(mocks)}. "
                "Use real system execution for validation.",
            }

    return {"continue_": True}
