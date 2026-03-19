# Two-Agent Build Pattern

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/core/orchestrator_v2.py`
- `src/acli/core/session.py`
- `src/acli/prompts/templates/initializer.md`
- `src/acli/prompts/templates/coding.md`

## Purpose

Enables developers to build entire projects from a plain-English spec by splitting the work into two specialized agent roles: an initializer that plans the project and a coder that implements features one at a time.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (Developer Experience)"
        Dev[Developer provides app_spec.txt] --> Run[acli run project/ ⚡ Single command]
        Run --> Monitor[Watch progress in TUI or logs]
        Monitor --> Done[Working project with git history ✅]
    end

    subgraph "Back-Stage (Two-Agent Pattern)"
        Run --> Check{feature_list.json exists and non-empty?}

        Check -->|No: First Run| InitAgent[Initializer Agent 📊]
        InitAgent --> ReadSpec[Read app_spec.txt 3743 lines]
        ReadSpec --> DetectStack[Detect Tech Stack ✅ Python/Node/Rust/Go]
        DetectStack --> GenFeatures[Generate feature_list.json 🎯 100-200 features]
        GenFeatures --> CreateStructure[Create Project Structure 💾]
        CreateStructure --> InitCommit[git commit 'Initial setup']
        InitCommit --> Next[Next Iteration]

        Check -->|Yes: Subsequent| CodeAgent[Coding Agent 💾]
        CodeAgent --> ReadFeatures[Read feature_list.json]
        ReadFeatures --> PickOne[Pick first incomplete feature ✅]
        PickOne --> Implement[Implement the feature]
        Implement --> Test[Test via CLI/API execution 🛡]
        Test --> Mark[Mark passes: true 💾]
        Mark --> Commit[git commit 'Implement: feature']
        Commit --> Next

        Next --> Check
    end

    InitAgent -->|Error| Retry[Retry up to 3x 🔄]
    CodeAgent -->|Error| Retry
    Retry --> Check

    Test -->|Fails| Fix[Fix and re-test 🔄]
    Fix --> Test
```

## Key Insights

- **Spec-Driven**: A 3,743-line spec produced 200 features, 25 source files, and 3,564 LOC across 4 sessions
- **Tech-Stack Adaptive**: Templates detect Python/Node/Rust/Go from the spec and create appropriate project structure
- **Incremental Progress**: Each coding session implements exactly one feature, making progress resumable after crashes
- **Real Git History**: Every feature gets its own commit, producing a clean, reviewable git log

## Change History

- **2026-03-19:** Initial creation; validated with ALR build (200/200 features, $17.46)
