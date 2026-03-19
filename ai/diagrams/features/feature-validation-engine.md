# Validation Engine

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/validation/engine.py`
- `src/acli/validation/gates.py`
- `src/acli/validation/evidence.py`
- `src/acli/validation/mock_detector.py`
- `src/acli/validation/platforms/api.py`
- `src/acli/validation/platforms/cli.py`
- `src/acli/validation/platforms/web.py`
- `src/acli/validation/platforms/ios.py`
- `src/acli/validation/platforms/generic.py`

## Purpose

Enforces that every implementation is validated against real running systems with captured evidence, blocking mock/test code creation so agents can never cheat their way to a passing grade.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (User Experience)"
        User([User]) -->|"Code implemented by agents"| TriggerVal[Validation Phase Begins]
        TriggerVal --> GateStatus[TUI Shows Gate Progress]
        GateStatus --> EvidenceView[View Evidence Files]
        EvidenceView --> PassFail{PASS or FAIL?}
        PassFail -->|PASS| Done[Proceed to Next Phase]
        PassFail -->|FAIL| RetryMsg[Show Failure + Evidence]
        RetryMsg -->|"Agent retries implementation"| TriggerVal
        Done --> User
    end

    subgraph "Back-Stage (Implementation)"
        TriggerVal --> MockGuard["MockDetector Pre-Hook 🛡️"]
        MockGuard --> MockCheck{"Write/Edit contains\nmock patterns? 🎯"}
        MockCheck -->|"pytest/unittest/mock.patch\nMagicMock/jest/vitest\n(20+ regex patterns)"| BlockWrite["BLOCK: Reject\nTool Call ✅"]
        BlockWrite -.->|"Agent informed"| MockGuard
        MockCheck -->|"Clean code"| AllowWrite["ALLOW: Proceed ✅"]

        AllowWrite --> Engine["ValidationEngine\n.run_gates() ⚡"]
        Engine --> PlatformDetect{"Detect Platform 🎯"}

        PlatformDetect -->|"HTTP endpoints found"| APIVal["APIValidator\ncurl real servers 📊"]
        PlatformDetect -->|"Binary/script found"| CLIVal["CLIValidator\nexecute real binary 📊"]
        PlatformDetect -->|"Web app detected"| WebVal["WebValidator\nPlaywright screenshots 📊"]
        PlatformDetect -->|"iOS project found"| IOSVal["IOSValidator\nsimctl screenshots 📊"]
        PlatformDetect -->|"No specific platform"| GenVal["GenericValidator\nfallback checks 📊"]

        APIVal --> GateRunner["GateRunner.execute() ⚡"]
        CLIVal --> GateRunner
        WebVal --> GateRunner
        IOSVal --> GateRunner
        GenVal --> GateRunner

        GateRunner --> RealCmd["Run Real Shell\nCommands 💾"]
        RealCmd --> Collect["EvidenceCollector\n.save() 💾"]
        Collect --> EvidenceFiles["evidence/\n  text, JSON,\n  command output ⏱️"]

        EvidenceFiles --> Evaluate{"Gate Criteria\nMet? ✅"}
        Evaluate -->|Yes| EmitPass["Emit GATE_RESULT\nstatus=PASS 🔄"]
        Evaluate -->|No| EmitFail["Emit GATE_RESULT\nstatus=FAIL 🔄"]

        EmitPass --> GateStatus
        EmitFail --> GateStatus

        RealCmd -.->|"Command timeout"| TimeoutErr["Record Timeout\nas FAIL Evidence ⏱️"]
        TimeoutErr --> Evaluate

        RealCmd -.->|"Command not found"| MissingErr["Record Missing\nDependency ⏱️"]
        MissingErr --> Evaluate

        GateRunner -.->|"Platform validator crash"| ValErr["Fallback to\nGenericValidator 🔄"]
        ValErr --> GenVal
    end
```

## Key Insights

- **No Cheating Possible:** MockDetector intercepts tool calls before they execute, so agents cannot create pytest files, jest configs, or any test doubles. Validation only passes with real system evidence.
- **Evidence is Permanent:** Every gate execution produces evidence files (curl output, screenshots, exit codes) stored under `evidence/`, providing an audit trail the user can inspect.
- **Technical Enabler:** Platform-specific validators mean the same engine works for web apps (Playwright), APIs (curl), CLIs (binary exec), and iOS (simctl) without the user configuring anything.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
