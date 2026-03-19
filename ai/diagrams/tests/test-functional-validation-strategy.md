# Functional Validation Strategy

**Type:** Test Coverage Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `tests/test_security.py`
- `tests/run_e2e.sh`
- `tests/functional/07-tui-validation.sh`
- `src/acli/validation/mock_detector.py`
- `src/acli/validation/platforms/`

## Purpose

Maps the full testing strategy to the user scenarios it protects -- showing how the "no mocks" policy is enforced, what each test layer covers, and how platform-specific validators connect to real-world evidence collection.

## Diagram

```mermaid
sequenceDiagram
    autonumber

    box Front-Stage (User Experience)
        participant U as User
        participant CLI as CLI
        participant TUI as TUI Dashboard
    end

    box Back-Stage (Implementation)
        participant MD as MockDetector
        participant ST as SecurityTests (67)
        participant E2E as E2E Tests (8)
        participant TV as TUI Validator
        participant PV as Platform Validators
        participant EC as EvidenceCollector
    end

    Note over U,EC: === NO-MOCKS POLICY ENFORCEMENT ===

    U->>CLI: Agent writes code during acli run
    CLI->>MD: Pre-tool-use hook intercepts Write/Edit
    Note right of MD: 🛡️ 20+ regex patterns scan file content

    alt Mock/test code detected
        MD-->>CLI: BLOCKED: mock/test pattern found
        CLI-->>U: "Mock code rejected. Use real validation."
        Note right of MD: 🛡️ Patterns: jest.mock, unittest, MagicMock,<br/>pytest.fixture, sinon.stub, vi.mock, etc.
    else Clean production code
        MD-->>CLI: ALLOWED
        Note right of MD: ✅ File write proceeds
    end

    Note over U,EC: === SECURITY TEST LAYER (67 tests) ===

    U->>CLI: Developer runs: pytest tests/test_security.py
    CLI->>ST: Execute security test suite

    rect rgb(240, 248, 255)
        Note over ST: Security Coverage

        ST->>ST: Command allowlist enforcement
        Note right of ST: 🛡️ Only 16 commands permitted

        ST->>ST: Shell injection prevention
        Note right of ST: 🛡️ shlex parsing blocks: ;, &&, ||, $(), backticks

        ST->>ST: Path traversal prevention
        Note right of ST: 🛡️ Block ../ and absolute path escapes

        ST->>ST: Pre-tool-use hook validation
        Note right of ST: 🛡️ Verify hooks fire before tool execution

        ST->>ST: Mock detector pattern coverage
        Note right of ST: 🛡️ Verify all 20+ patterns trigger correctly
    end

    alt Any test fails
        ST-->>CLI: FAIL with specific violation
        CLI-->>U: Security regression detected
        Note over U: 🔄 Fix before any code ships
    else All pass
        ST-->>CLI: 67/67 PASS
        CLI-->>U: Security layer intact
    end

    Note over U,EC: === E2E TEST LAYER (8 tests) ===

    U->>CLI: Developer runs: bash tests/run_e2e.sh
    CLI->>E2E: Execute full flow tests

    rect rgb(240, 248, 255)
        Note over E2E: E2E Coverage

        E2E->>E2E: acli init creates valid project
        Note right of E2E: ✅ Verify directory structure + spec file

        E2E->>E2E: acli run executes full pipeline
        Note right of E2E: ⚡ Real orchestrator, real agents

        E2E->>E2E: acli onboard analyzes codebase
        Note right of E2E: 💾 Verify context files created

        E2E->>E2E: acli prompt executes single task
        Note right of E2E: 🎯 Prompt classification + execution

        E2E->>E2E: acli config get/set/list
        Note right of E2E: 💾 Configuration persistence

        E2E->>E2E: acli session list/resume
        Note right of E2E: 🔄 Session recovery works

        E2E->>E2E: acli validate runs gates
        Note right of E2E: ✅ Validation engine produces evidence

        E2E->>E2E: acli memory add/list/clear
        Note right of E2E: 💾 Memory persistence cycle
    end

    alt Any test fails
        E2E-->>CLI: FAIL with test name + output
        CLI-->>U: Integration regression
    else All pass
        E2E-->>CLI: 8/8 PASS
        CLI-->>U: All user flows work end-to-end
    end

    Note over U,EC: === TUI VALIDATION ===

    U->>CLI: Developer runs: bash tests/functional/07-tui-validation.sh
    CLI->>TV: Launch TUI in test mode

    TV->>TV: Verify 7-panel layout renders
    Note right of TV: ✅ AgentGraph, Detail, Context, Log, Gates, Stats, Prompt

    TV->>TV: Verify keyboard bindings respond
    Note right of TV: ⏱️ j/k scroll, F1-F4 filter, p/s/q controls

    TV->>TV: Verify streaming events display
    Note right of TV: 📊 21 event types rendered correctly

    TV-->>CLI: TUI validation result
    CLI-->>U: Dashboard functional

    Note over U,EC: === PLATFORM VALIDATORS (runtime) ===

    U->>CLI: acli validate <project-dir>
    CLI->>PV: Select validator by project type

    alt API project
        PV->>PV: APIValidator
        Note right of PV: ⚡ curl against real running server
        PV->>EC: Save response body + status code
        Note right of EC: 💾 Evidence: .acli/evidence/api_*.json
    else CLI project
        PV->>PV: CLIValidator
        Note right of PV: ⚡ Execute real compiled binary
        PV->>EC: Save stdout + exit code
        Note right of EC: 💾 Evidence: .acli/evidence/cli_*.txt
    else Web project
        PV->>PV: WebValidator
        Note right of PV: ⚡ Playwright captures real browser
        PV->>EC: Save screenshots + DOM snapshots
        Note right of EC: 💾 Evidence: .acli/evidence/web_*.png
    else iOS project
        PV->>PV: IOSValidator
        Note right of PV: ⚡ simctl on real simulator
        PV->>EC: Save simulator screenshots
        Note right of EC: 💾 Evidence: .acli/evidence/ios_*.png
    else Unknown project type
        PV->>PV: GenericValidator
        Note right of PV: 🔄 Fallback: file existence + syntax checks
        PV->>EC: Save check results
        Note right of EC: 💾 Evidence: .acli/evidence/generic_*.json
    end

    EC-->>CLI: Evidence files written
    CLI-->>U: Validation result: PASS/FAIL + evidence paths

    Note over U: User reviews real evidence, not test output
```

## Key Insights

- **User Impact 1:** The MockDetector enforces honest validation at the agent level -- users can trust that "PASS" means real code ran against real infrastructure, not that a mock returned a canned response.
- **User Impact 2:** Platform-specific validators mean an API project gets curl evidence, a web project gets real screenshots, and an iOS project gets simulator captures. The validation matches how users actually verify their software.
- **Technical Enabler:** The three test layers form a defense-in-depth chain: SecurityTests guard the sandbox, E2E tests guard CLI flows, and Platform Validators guard agent-produced code. MockDetector sits upstream of all agent output, preventing contamination before any test layer runs.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
