# Brownfield Onboarding Journey

**Type:** Sequence Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/cli_v2.py`
- `src/acli/context/onboarder.py`
- `src/acli/context/chunker.py`
- `src/acli/context/store.py`
- `src/acli/context/memory.py`

## Purpose

Shows how a user onboards an existing codebase so ACLI can operate on it with full project awareness -- from the initial command through async analysis, context persistence, and memory seeding, including the error path when a project has no source files.

## Diagram

```mermaid
sequenceDiagram
    autonumber

    box Front-Stage (User Experience)
        participant U as User
        participant CLI as CLI (typer)
        participant TUI as StreamingHandler
    end

    box Back-Stage (Implementation)
        participant BO as BrownfieldOnboarder
        participant KC as KnowledgeChunker
        participant CS as ContextStore
        participant MM as MemoryManager
    end

    Note over U,CLI: User points ACLI at an existing project

    U->>CLI: acli onboard <project-dir>
    CLI->>CLI: Resolve + validate project path

    alt Directory does not exist
        CLI-->>U: Error: path not found
    end

    CLI->>BO: start_onboarding(project_dir)
    Note right of BO: ⚡ Begin async analysis pipeline

    BO->>BO: scan_directory(project_dir)
    Note right of BO: 💾 Walk filesystem, count files by extension

    alt No source files found
        BO-->>CLI: Warning: no recognizable source files
        CLI-->>U: "No source files detected. Add code and retry."
        Note over U: 🔄 User adds files, runs onboard again
    end

    BO->>TUI: emit(CONTEXT_UPDATE, "Scanning...")
    TUI-->>U: "Scanning project..."

    rect rgb(240, 248, 255)
        Note over KC,CS: Codebase Analysis Phase

        BO->>KC: segment(project_dir)
        Note right of KC: ⚡ Split files into knowledge chunks
        KC->>KC: group_by_directory()
        KC->>KC: detect_boundaries()
        Note right of KC: 🎯 Identify module boundaries + entry points
        KC-->>BO: FileChunk[] (segmented codebase)

        BO->>BO: analyze_tech_stack(chunks)
        Note right of BO: 🎯 Detect language, framework, build system

        BO->>BO: analyze_architecture(chunks)
        Note right of BO: 🎯 Infer patterns: MVC, microservice, monolith

        BO->>BO: extract_conventions(chunks)
        Note right of BO: 🎯 Naming, imports, style, config patterns
    end

    BO->>TUI: emit(CONTEXT_UPDATE, "Analyzing...")
    TUI-->>U: "Analyzing codebase structure..."

    rect rgb(240, 248, 255)
        Note over CS,MM: Persistence Phase

        BO->>CS: save("codebase_analysis.json", analysis)
        Note right of CS: 💾 .acli/context/codebase_analysis.json

        BO->>CS: save("tech_stack.json", tech_stack)
        Note right of CS: 💾 .acli/context/tech_stack.json

        BO->>CS: save("conventions.json", conventions)
        Note right of CS: 💾 .acli/context/conventions.json

        BO->>MM: seed(project_facts)
        Note right of MM: 💾 .acli/memory/project_memory.json
        MM->>MM: merge_with_existing()
        Note right of MM: 🔄 Preserve prior memory, add new facts
    end

    BO->>TUI: emit(CONTEXT_UPDATE, "Complete")
    TUI-->>U: "Onboarding complete"

    BO-->>CLI: OnboardingResult(stats, context_path, memory_path)

    CLI-->>U: Summary: files scanned, language, framework, architecture
    Note over U,CLI: Stats: "247 files, Python/FastAPI, src/ layout, REST API"

    alt User inspects context
        U->>CLI: acli context <project-dir>
        CLI-->>U: Display stored analysis + tech stack + conventions
    end

    alt User inspects memory
        U->>CLI: acli memory list
        CLI-->>U: Display seeded project facts
    end

    Note over U: Project is now ready for: acli run / acli prompt
```

## Key Insights

- **User Impact 1:** Onboarding is a single command -- users do not manually describe their project. ACLI auto-detects language, framework, and architecture so subsequent `acli run` commands have full context.
- **User Impact 2:** The "no source files" guard prevents confusing downstream failures by catching the problem early with a clear message and recovery path.
- **Technical Enabler:** KnowledgeChunker segments the codebase into retrievable chunks before analysis, enabling the AgentFactory to inject relevant context slices into each agent's prompt rather than flooding it with the entire codebase.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
