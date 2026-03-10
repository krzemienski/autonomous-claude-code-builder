# Changelog

All notable changes to Autonomous CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-08

### Added

- **Initial Release** of Autonomous CLI (acli)
- Real-time streaming dashboard with Rich library
  - Multi-pane TUI showing tool execution, logs, and progress
  - Tool board with execution status and timing
  - Live log streaming with timestamps
  - Progress bar with percentage display
- Spec enhancement system
  - Convert plain English to structured JSON specifications
  - Interactive prompting for missing details
  - Claude-powered intelligent conversion
- Two-agent orchestration pattern
  - Initializer agent: Generates feature list and project structure
  - Coding agent: Implements features one-by-one with testing
  - Automatic agent selection based on project state
- Feature-based progress tracking
  - `feature_list.json` format with ~200 test cases
  - Persistent progress across sessions
  - Resume capability after interruption
- Comprehensive security model
  - 16-command allowlist (ls, cat, npm, git, etc.)
  - Per-command validators for pkill, chmod, init.sh
  - Shlex-based command parsing (injection-safe)
  - OS-level bash sandbox
  - Project-directory filesystem restriction
- Browser automation integration
  - Puppeteer MCP server support (default)
  - Playwright MCP server support (alternative)
  - Browser manager with provider switching
  - Command wrappers for both providers
- Configuration management
  - User-level config: `~/.config/acli/config.json`
  - Model selection, max iterations, browser provider
  - CLI commands for get/set/list
- Comprehensive test suite
  - 87+ security tests covering allowlist, validators, hooks
  - CLI command tests with mocked dependencies
  - Orchestrator and session tests
  - Browser manager and wrapper tests
  - >80% code coverage

### Commands

- `acli init <name>` - Initialize new project with spec enhancement
- `acli run [dir]` - Run autonomous coding loop
- `acli status [dir]` - Show progress status
- `acli enhance [file]` - Enhance spec interactively
- `acli config [key] [value]` - Manage configuration

### Security Features

- OS-level sandbox for bash commands
- Project-directory filesystem restriction
- Command allowlist with validators
- Pre-tool-use security hooks
- Safe command parsing (shlex)
- Validator registry for extensibility

### Documentation

- Comprehensive README with installation and usage
- Architecture documentation (ARCHITECTURE.md)
- Quick start guide (QUICKSTART.md)
- API reference (API.md)
- Contributing guidelines (CONTRIBUTING.md)
- This changelog

### Dependencies

- `claude-agent-sdk>=0.1.48` - Claude Agent SDK integration
- `rich>=13.7.0` - Terminal UI
- `typer>=0.9.0` - CLI framework
- `pydantic>=2.5.0` - Data validation
- `httpx>=0.25.0` - HTTP client

### Development Dependencies

- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting
- `ruff>=0.1.0` - Linting
- `mypy>=1.7.0` - Type checking

## [Unreleased]

### Planned for v1.1.0

- **Pause/Resume Control**
  - Pause agent mid-session
  - Resume from exact state
  - Save/load session snapshots

- **Tool Approval Mode**
  - Manual approval for each tool call
  - Batch approval for similar operations
  - Reject and provide alternative

- **Mid-Flight Spec Editing**
  - Modify spec during execution
  - Regenerate feature list dynamically
  - Adapt to changing requirements

- **Real-Time Debugging Console**
  - Interactive Python REPL
  - Inspect agent state
  - Manual tool execution

- **Config Hot-Reload**
  - Update config without restart
  - Apply changes to running sessions

### Planned for v1.2.0

- **Multi-Project Support**
  - Run multiple projects in parallel
  - Dashboard switching between projects
  - Shared configuration

- **Plugin System**
  - Custom tool integration
  - Third-party MCP servers
  - Custom prompt templates

- **Enhanced Browser Testing**
  - Visual regression testing
  - Screenshot comparison
  - Accessibility testing

### Planned for v2.0.0

- **Cloud Integration**
  - Remote execution
  - Shared project collaboration
  - Cloud-based progress storage

- **AI-Powered Debugging**
  - Automatic error detection
  - Suggested fixes
  - Self-healing capabilities

## Version History

### Version Numbering

- **Major (X.0.0)**: Breaking API changes
- **Minor (1.X.0)**: New features, backwards-compatible
- **Patch (1.0.X)**: Bug fixes, documentation updates

### Support Policy

- **Current**: v1.0.0 - Full support
- **Security Updates**: All versions receive security patches
- **End of Life**: Announced 6 months in advance

## Links

- [GitHub Repository](https://github.com/claude-code-skills-factory/autonomous-cli)
- [Documentation](https://github.com/claude-code-skills-factory/autonomous-cli#readme)
- [Issue Tracker](https://github.com/claude-code-skills-factory/autonomous-cli/issues)
- [PyPI Package](https://pypi.org/project/autonomous-cli/)
