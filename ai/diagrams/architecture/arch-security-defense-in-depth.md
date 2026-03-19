# ACLI v2 Security — Defense-in-Depth

**Type:** Architecture Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/security/validators.py`
- `src/acli/security/hooks.py`
- `src/acli/validation/mock_detector.py`

## Purpose

Shows the 6 layered security barriers that protect the user's system from dangerous agent actions — each layer catches threats the previous one missed, ensuring no single bypass compromises safety.

## Diagram

```mermaid
graph TB
    subgraph Front-Stage["Front-Stage (User Experience)"]
        User((User))
        Prompt["User Prompt<br/>e.g. 'build a REST API'"]
        SafeOutput["Safe Output ✅<br/>Real code, no mocks,<br/>validated evidence"]
        BlockedNotice["Blocked Action Notice ⚠️<br/>Explains what was blocked & why"]

        User -->|"submits"| Prompt
        SafeOutput --> User
        BlockedNotice --> User
    end

    subgraph Back-Stage["Back-Stage (Implementation)"]
        subgraph Layer1["Layer 1: OS Sandbox 🛡️"]
            Sandbox["OS-Level Sandbox<br/>Process isolation<br/>Filesystem restrictions"]
        end

        subgraph Layer2["Layer 2: File Permissions 🛡️"]
            FilePerm["File Permission Checks<br/>Read/write boundaries<br/>Project directory scoping"]
        end

        subgraph Layer3["Layer 3: Command Allowlist 🛡️"]
            Allowlist["16-Command Allowlist ⚡<br/>ls | cat | npm | npx | git<br/>python | pip | node | curl | wget<br/>touch | mkdir | rm | echo | chmod | pkill"]
            CmdReject["Command Rejected 🔄<br/>Not in allowlist"]
        end

        subgraph Layer4["Layer 4: Argument Parsing 🛡️"]
            Shlex["shlex Parsing ⚡<br/>Shell injection prevention<br/>Argument tokenization<br/>Quote handling"]
            ArgReject["Injection Blocked 🔄<br/>Dangerous arguments detected"]
        end

        subgraph Layer5["Layer 5: Pre-Tool-Use Hooks 🛡️"]
            Hooks["Pre-Tool-Use Hooks ⏱️<br/>Intercept before execution<br/>Validate tool parameters<br/>Block dangerous operations"]
            HookReject["Hook Blocked 🔄<br/>Tool use denied"]
        end

        subgraph Layer6["Layer 6: Mock Detection 🛡️"]
            MockDetect["MockDetector ✅<br/>20+ Regex Patterns"]

            subgraph Patterns["Detection Patterns"]
                P1["jest.mock / vi.mock / sinon"]
                P2["@pytest.fixture / unittest.mock"]
                P3[".test.ts / .spec.ts / __tests__/"]
                P4["MagicMock / patch / stub"]
                P5["Testing Library imports"]
                P6["conftest.py / jest.config"]
            end

            MockReject["Mock Code Blocked 🔄<br/>Write/Edit denied<br/>Agent re-routed to real code"]
        end

        Prompt --> Sandbox
        Sandbox -->|"pass"| FilePerm
        Sandbox -->|"fail"| BlockedNotice

        FilePerm -->|"pass"| Allowlist
        FilePerm -->|"fail"| BlockedNotice

        Allowlist -->|"command in list"| Shlex
        Allowlist -->|"command not in list"| CmdReject
        CmdReject --> BlockedNotice

        Shlex -->|"safe arguments"| Hooks
        Shlex -->|"injection detected"| ArgReject
        ArgReject --> BlockedNotice

        Hooks -->|"tool allowed"| MockDetect
        Hooks -->|"tool blocked"| HookReject
        HookReject --> BlockedNotice

        MockDetect --> Patterns
        MockDetect -->|"real code"| SafeOutput
        MockDetect -->|"mock/test detected"| MockReject
        MockReject --> BlockedNotice
    end

    style Front-Stage stroke:#0ff,stroke-width:2px
    style Back-Stage stroke:#f0f,stroke-width:2px
    style Layer1 stroke:#ff6,stroke-width:1px
    style Layer2 stroke:#ff6,stroke-width:1px
    style Layer3 stroke:#ff6,stroke-width:1px
    style Layer4 stroke:#ff6,stroke-width:1px
    style Layer5 stroke:#ff6,stroke-width:1px
    style Layer6 stroke:#ff6,stroke-width:1px
```

## Key Insights

- **User Impact 1:** The user never sees a dangerous command execute — 6 layers guarantee that even if an agent hallucinates `rm -rf /` or tries shell injection, it gets caught before execution.
- **User Impact 2:** Mock detection ensures the user always gets real, functional code — agents cannot sneak in `jest.mock()`, `unittest.mock`, or test doubles that would pass fake validation.
- **Technical Enabler:** Each layer is independent. The command allowlist catches broad categories (only 16 commands allowed), shlex catches injection within allowed commands, hooks catch semantic misuse of allowed tools, and mock detection catches code-level cheating. No single bypass defeats all layers.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
