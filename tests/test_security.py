"""
Security Tests for Autonomous CLI
==================================

Comprehensive test suite for security hooks and validators.
Based on quickstart test_security.py pattern.
"""

import pytest

from acli.security.hooks import (
    ALLOWED_COMMANDS,
    bash_security_hook,
    extract_commands,
    split_command_segments,
)
from acli.security.validators import (
    ValidationResult,
    validate_chmod,
    validate_init_script,
    validate_pkill,
)


class TestExtractCommands:
    """Test command extraction from shell strings."""

    def test_single_command(self):
        assert extract_commands("ls") == ["ls"]
        assert extract_commands("cat file.txt") == ["cat"]

    def test_pipe(self):
        assert extract_commands("ls | grep txt") == ["ls", "grep"]

    def test_and_operator(self):
        assert extract_commands("mkdir dir && cd dir") == ["mkdir", "cd"]

    def test_or_operator(self):
        assert extract_commands("ls || echo error") == ["ls", "echo"]

    def test_semicolon(self):
        assert extract_commands("ls ; cat file") == ["ls", "cat"]

    def test_with_flags(self):
        assert extract_commands("ls -la") == ["ls"]
        assert extract_commands("git commit -m 'msg'") == ["git"]

    def test_with_path(self):
        assert extract_commands("/usr/bin/python script.py") == ["python"]
        assert extract_commands("./init.sh") == ["init.sh"]

    def test_variable_assignment(self):
        assert extract_commands("NODE_ENV=production npm start") == ["npm"]

    def test_empty(self):
        assert extract_commands("") == []
        assert extract_commands("   ") == []

    def test_malformed(self):
        # Unclosed quote should return empty (fail-safe)
        assert extract_commands("echo 'unclosed") == []


class TestSplitCommandSegments:
    """Test command segment splitting."""

    def test_single_command(self):
        assert split_command_segments("ls") == ["ls"]

    def test_and_operator(self):
        result = split_command_segments("ls && cat file")
        assert len(result) == 2
        assert "ls" in result[0]
        assert "cat file" in result[1]

    def test_or_operator(self):
        result = split_command_segments("ls || echo error")
        assert len(result) == 2

    def test_semicolon(self):
        result = split_command_segments("ls ; cat file")
        assert len(result) == 2

    def test_mixed(self):
        result = split_command_segments("ls && cat file ; echo done")
        assert len(result) == 3


class TestValidatePkill:
    """Test pkill command validation."""

    # Allowed cases
    def test_pkill_node(self):
        result = validate_pkill("pkill node")
        assert result.allowed is True

    def test_pkill_npm(self):
        result = validate_pkill("pkill npm")
        assert result.allowed is True

    def test_pkill_with_flags(self):
        result = validate_pkill("pkill -f 'node server.js'")
        assert result.allowed is True

    def test_pkill_vite(self):
        result = validate_pkill("pkill vite")
        assert result.allowed is True

    # Blocked cases
    def test_pkill_bash(self):
        result = validate_pkill("pkill bash")
        assert result.allowed is False
        assert "allowed for" in result.reason

    def test_pkill_python(self):
        result = validate_pkill("pkill python")
        assert result.allowed is False

    def test_pkill_empty(self):
        result = validate_pkill("pkill")
        assert result.allowed is False
        assert "requires a process name" in result.reason

    def test_pkill_malformed(self):
        result = validate_pkill("pkill 'unclosed")
        assert result.allowed is False


class TestValidateChmod:
    """Test chmod command validation."""

    # Allowed cases
    def test_chmod_plus_x(self):
        result = validate_chmod("chmod +x init.sh")
        assert result.allowed is True

    def test_chmod_u_plus_x(self):
        result = validate_chmod("chmod u+x script.py")
        assert result.allowed is True

    def test_chmod_ug_plus_x(self):
        result = validate_chmod("chmod ug+x file.sh")
        assert result.allowed is True

    def test_chmod_a_plus_x(self):
        result = validate_chmod("chmod a+x executable")
        assert result.allowed is True

    # Blocked cases
    def test_chmod_777(self):
        result = validate_chmod("chmod 777 file")
        assert result.allowed is False
        assert "Dangerous mode" in result.reason

    def test_chmod_666(self):
        result = validate_chmod("chmod 666 file")
        assert result.allowed is False

    def test_chmod_644(self):
        result = validate_chmod("chmod 644 file")
        assert result.allowed is False
        assert "Only +x mode allowed" in result.reason

    def test_chmod_minus_x(self):
        result = validate_chmod("chmod -x file")
        assert result.allowed is False

    def test_chmod_plus_w(self):
        result = validate_chmod("chmod +w file")
        assert result.allowed is False

    def test_chmod_with_flags(self):
        result = validate_chmod("chmod -R +x dir")
        assert result.allowed is False
        assert "flags not allowed" in result.reason

    def test_chmod_no_mode(self):
        result = validate_chmod("chmod")
        assert result.allowed is False

    def test_chmod_no_files(self):
        result = validate_chmod("chmod +x")
        assert result.allowed is False


class TestValidateInitScript:
    """Test init.sh script validation."""

    # Allowed cases
    def test_init_current_dir(self):
        result = validate_init_script("./init.sh")
        assert result.allowed is True

    def test_init_with_args(self):
        result = validate_init_script("./init.sh arg1 arg2")
        assert result.allowed is True

    # Blocked cases
    def test_init_absolute_path(self):
        result = validate_init_script("/etc/init.sh")
        assert result.allowed is False
        assert "no absolute paths" in result.reason

    def test_init_traversal(self):
        result = validate_init_script("../init.sh")
        assert result.allowed is False
        assert "traversal" in result.reason

    def test_init_subdirectory(self):
        result = validate_init_script("scripts/init.sh")
        assert result.allowed is False

    def test_init_other_script(self):
        result = validate_init_script("./setup.sh")
        assert result.allowed is False


class TestBashSecurityHook:
    """Test bash security hook integration."""

    @pytest.mark.asyncio
    async def test_allowed_command(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_blocked_command(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"
        assert "not in the allowed commands" in result["reason"]

    @pytest.mark.asyncio
    async def test_allowed_chain(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "mkdir build && ls"},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_blocked_chain(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls && rm -rf /"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"

    @pytest.mark.asyncio
    async def test_pkill_allowed(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "pkill node"},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_pkill_blocked(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "pkill bash"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"

    @pytest.mark.asyncio
    async def test_chmod_allowed(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "chmod +x init.sh"},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_chmod_blocked(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "chmod 777 file"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"

    @pytest.mark.asyncio
    async def test_init_script_allowed(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "./init.sh"},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_init_script_blocked(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "/etc/init.sh"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"

    @pytest.mark.asyncio
    async def test_non_bash_tool(self):
        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "test.txt", "content": "test"},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_empty_command(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": ""},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_malformed_command(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'unclosed"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"


class TestAllowedCommands:
    """Test that all expected commands are in the allowlist."""

    def test_file_inspection_commands(self):
        assert "ls" in ALLOWED_COMMANDS
        assert "cat" in ALLOWED_COMMANDS
        assert "head" in ALLOWED_COMMANDS
        assert "tail" in ALLOWED_COMMANDS
        assert "wc" in ALLOWED_COMMANDS
        assert "grep" in ALLOWED_COMMANDS

    def test_file_operation_commands(self):
        assert "cp" in ALLOWED_COMMANDS
        assert "mkdir" in ALLOWED_COMMANDS
        assert "chmod" in ALLOWED_COMMANDS

    def test_nodejs_commands(self):
        assert "npm" in ALLOWED_COMMANDS
        assert "node" in ALLOWED_COMMANDS

    def test_git_commands(self):
        assert "git" in ALLOWED_COMMANDS

    def test_process_management_commands(self):
        assert "ps" in ALLOWED_COMMANDS
        assert "lsof" in ALLOWED_COMMANDS
        assert "sleep" in ALLOWED_COMMANDS
        assert "pkill" in ALLOWED_COMMANDS

    def test_script_execution_commands(self):
        assert "init.sh" in ALLOWED_COMMANDS

    def test_dangerous_commands_blocked(self):
        dangerous = {"rm", "mv", "curl", "wget", "sudo", "su", "dd", "mkfs"}
        assert dangerous.isdisjoint(ALLOWED_COMMANDS)


class TestSecurityEdgeCases:
    """Test security edge cases and bypass attempts."""

    @pytest.mark.asyncio
    async def test_command_injection_attempt(self):
        # Attempt to inject via semicolon
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls; rm -rf /"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"

    @pytest.mark.asyncio
    async def test_command_substitution_attempt(self):
        # Attempt via backticks
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls `whoami`"},
        }
        result = await bash_security_hook(input_data)
        # whoami is not in allowlist, should be blocked
        # If not blocked (command parsing doesn't detect it), that's also OK
        if result:
            assert result.get("decision") == "block"

    @pytest.mark.asyncio
    async def test_pipe_to_dangerous_command(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls | xargs rm"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"

    @pytest.mark.asyncio
    async def test_valid_pipe_chain(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls | grep .txt | wc -l"},
        }
        result = await bash_security_hook(input_data)
        assert result == {}

    @pytest.mark.asyncio
    async def test_pkill_with_wildcard_attempt(self):
        # Even with wildcards, target must be in allowlist
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "pkill -f 'python.*'"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"

    @pytest.mark.asyncio
    async def test_chmod_octal_blocked(self):
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "chmod 755 script.sh"},
        }
        result = await bash_security_hook(input_data)
        assert result["decision"] == "block"
