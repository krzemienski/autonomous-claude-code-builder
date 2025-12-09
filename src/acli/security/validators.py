"""
Per-Command Validators
======================

Validation functions for sensitive commands.
Uses shlex for safe parsing (prevents injection).
"""

import re
import shlex
from typing import Callable, NamedTuple


# Allowed process names for pkill
ALLOWED_PKILL_TARGETS: set[str] = {
    "node",
    "npm",
    "npx",
    "vite",
    "next",
    "webpack",
    "tsc",
}

# Dangerous chmod modes
DANGEROUS_CHMOD_MODES: set[str] = {"777", "666", "000"}


class ValidationResult(NamedTuple):
    """Result of command validation."""

    allowed: bool
    reason: str = ""


def validate_pkill(command: str) -> ValidationResult:
    """
    Validate pkill - only dev processes allowed.

    Examples:
        validate_pkill("pkill node")  # OK
        validate_pkill("pkill -f 'node server.js'")  # OK
        validate_pkill("pkill bash")  # BLOCKED
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return ValidationResult(False, "Could not parse pkill command")

    if not tokens:
        return ValidationResult(False, "Empty pkill command")

    # Extract non-flag arguments
    args = [t for t in tokens[1:] if not t.startswith("-")]

    if not args:
        return ValidationResult(False, "pkill requires a process name")

    target = args[-1]

    # Handle -f flag (full command match): "node server.js" -> "node"
    if " " in target:
        target = target.split()[0]

    if target in ALLOWED_PKILL_TARGETS:
        return ValidationResult(True)

    return ValidationResult(
        False, f"pkill only allowed for: {ALLOWED_PKILL_TARGETS}"
    )


def validate_chmod(command: str) -> ValidationResult:
    """
    Validate chmod - only +x mode allowed.

    Examples:
        validate_chmod("chmod +x init.sh")  # OK
        validate_chmod("chmod u+x script.py")  # OK
        validate_chmod("chmod 777 file")  # BLOCKED
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return ValidationResult(False, "Could not parse chmod command")

    if not tokens or tokens[0] != "chmod":
        return ValidationResult(False, "Not a chmod command")

    # Extract mode and files
    mode = None
    files = []

    for token in tokens[1:]:
        if token.startswith("-"):
            return ValidationResult(False, "chmod flags not allowed")
        elif mode is None:
            mode = token
        else:
            files.append(token)

    if mode is None:
        return ValidationResult(False, "chmod requires a mode")

    if not files:
        return ValidationResult(False, "chmod requires file(s)")

    # Check for dangerous modes
    if mode in DANGEROUS_CHMOD_MODES:
        return ValidationResult(False, f"Dangerous mode: {mode}")

    # Only allow +x variants
    if not re.match(r"^[ugoa]*\+x$", mode):
        return ValidationResult(False, f"Only +x mode allowed, got: {mode}")

    return ValidationResult(True)


def validate_init_script(command: str) -> ValidationResult:
    """
    Validate init.sh - only ./init.sh in project directory.

    Examples:
        validate_init_script("./init.sh")  # OK
        validate_init_script("/etc/init.sh")  # BLOCKED
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return ValidationResult(False, "Could not parse command")

    if not tokens:
        return ValidationResult(False, "Empty command")

    script = tokens[0]

    # Only allow ./init.sh (current directory)
    if script == "./init.sh":
        return ValidationResult(True)

    # Block absolute paths and directory traversal
    if script.startswith("/") or ".." in script:
        return ValidationResult(False, "Only ./init.sh allowed (no absolute paths or traversal)")

    # Block other variations
    if script.endswith("/init.sh"):
        return ValidationResult(False, f"Only ./init.sh allowed, got: {script}")

    return ValidationResult(False, f"Only ./init.sh allowed, got: {script}")


# Validator registry
VALIDATORS: dict[str, Callable[[str], ValidationResult]] = {
    "pkill": validate_pkill,
    "chmod": validate_chmod,
    "init.sh": validate_init_script,
}


def get_validator(command_name: str) -> Callable[[str], ValidationResult] | None:
    """Get validator for a command, if one exists."""
    return VALIDATORS.get(command_name)
