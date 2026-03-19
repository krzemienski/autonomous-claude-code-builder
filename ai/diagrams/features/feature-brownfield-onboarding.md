# Brownfield Codebase Onboarding

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/cli.py` (onboard command)
- `src/acli/context/onboarder.py`
- `src/acli/context/store.py`
- `src/acli/context/memory.py`

## Purpose

Enables developers to bring existing projects into ACLI by automatically analyzing the codebase's tech stack, structure, and patterns — creating context that helps the agent make better decisions.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (Developer Experience)"
        Dev[Developer has existing project] --> Onboard[acli onboard project/ ⚡ One command]
        Onboard --> Report[Tech stack detected ✅]
        Report --> AddFacts[acli memory add category fact 💾]
        AddFacts --> Context[acli context project/ 📊 View analysis]
    end

    subgraph "Back-Stage (Analysis Pipeline)"
        Onboard --> Scanner[BrownfieldOnboarder 🎯 Codebase scanner]

        Scanner --> TechDetect[Detect Tech Stack ✅]
        TechDetect --> PyCheck{pyproject.toml or setup.py?}
        TechDetect --> NodeCheck{package.json?}
        TechDetect --> DockerCheck{Dockerfile?}
        TechDetect --> GoCheck{go.mod?}

        PyCheck -->|Yes| Python[Python + Poetry/pip 📊]
        NodeCheck -->|Yes| Node[Node.js + npm/yarn 📊]
        DockerCheck -->|Yes| Docker[Docker + Compose 📊]
        GoCheck -->|Yes| Go[Go modules 📊]

        Scanner --> FileMap[Map Files 💾 Count and categorize]
        FileMap --> LOC[Count LOC 📊 Per file type]
        LOC --> Dirs[Map Directory Structure 📊]

        Scanner --> Persist[Persist to .acli/context/ 💾]
        Persist --> TechJSON[tech_stack.json 💾]
        Persist --> AnalysisJSON[codebase_analysis.json 💾]
    end

    Scanner -->|No recognizable stack| Fallback[Generic analysis 🔄]
    Fallback --> Persist

    Python --> Persist
    Node --> Persist
    Docker --> Persist
    Go --> Persist
```

## Key Insights

- **Zero-Config Detection**: Automatically identifies Python/Node/Docker/Go from project files
- **Persistent Context**: Analysis stored in `.acli/context/` survives across sessions
- **Memory System**: Developers can annotate with facts (`acli memory add`) that agents access later
- **E2E Validated**: Successfully onboarded ALR project (26 files, 3,574 LOC, Python/Docker/Poetry detected)

## Change History

- **2026-03-19:** Initial creation; validated with ALR brownfield onboarding
