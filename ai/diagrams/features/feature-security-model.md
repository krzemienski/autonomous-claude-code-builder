# Defense-in-Depth Security Model

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/security/validators.py`
- `src/acli/security/hooks.py`
- `src/acli/core/client.py`
- `src/acli/validation/mock_detector.py`

## Purpose

Protects developers from agent misuse by enforcing four layers of security on every tool call, ensuring the autonomous agent cannot execute dangerous commands, access unauthorized files, or bypass validation.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (Developer Trust)"
        Dev[Developer runs acli run] --> Config[Security settings auto-written ✅]
        Config --> Trust[Agent operates safely within boundaries 🛡]
    end

    subgraph "Back-Stage (Defense Layers)"
        Agent[Agent requests tool call] --> L1{Layer 1: OS Sandbox 🛡}
        L1 -->|Sandboxed| L2{Layer 2: File Permissions 🛡}
        L1 -->|Blocked| Deny1[Blocked: Outside sandbox]

        L2 -->|Project files only| L3{Layer 3: Command Allowlist 🛡}
        L2 -->|Blocked| Deny2[Blocked: Unauthorized path]

        L3 -->|16 allowed commands| L4{Layer 4: Pre-Tool Hooks ✅}
        L3 -->|Blocked| Deny3[Blocked: Disallowed command]

        L4 -->|Passes validation| Execute[Tool executes safely ⚡]
        L4 -->|Blocked| Deny4[Blocked: Hook rejected]
    end

    subgraph "Per-Command Validators"
        L3 --> PK[pkill: dev processes only 🛡]
        L3 --> CH[chmod: only +x mode 🛡]
        L3 --> SH[init.sh: must be ./init.sh 🛡]
        L3 --> Bash[Bash: shlex parsing ✅]
    end

    subgraph "Hook Layer"
        L4 --> BashHook[bash_security_hook 🛡 Validates commands]
        L4 --> MockHook[mock_detection_hook ✅ Iron Rule enforcement]
    end

    Deny1 --> Report[Error reported to developer 🔄]
    Deny2 --> Report
    Deny3 --> Report
    Deny4 --> Report
```

## Key Insights

- **16-Command Allowlist**: Only ls, cat, npm, npx, git, python, pip, node, curl, wget, touch, mkdir, rm, echo, chmod, pkill are allowed
- **Per-Command Validation**: pkill only kills dev processes (node, npm, vite, webpack); chmod only allows +x
- **Iron Rule**: Mock detection hook blocks creation of test/mock files, enforcing real system validation
- **Zero-Config**: Security settings are auto-written to `.claude_settings.json` on every session start

## Change History

- **2026-03-19:** Initial creation
