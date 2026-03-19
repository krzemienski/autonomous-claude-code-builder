# Context & Memory System

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/context/store.py`
- `src/acli/context/memory.py`
- `src/acli/context/chunker.py`
- `src/acli/context/onboarder.py`

## Purpose

Gives agents persistent knowledge about the codebase and cross-session memory so they never start from scratch, reducing redundant analysis and enabling intelligent decisions based on project history.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (User Experience)"
        User([User]) -->|"acli onboard ."| StartOnboard[Onboard Existing Project]
        User -->|"acli run . 'add auth'"| StartTask[Run Task With Context]
        User -->|"acli memory list"| ViewMemory[View Stored Facts]
        User -->|"acli context ."| ViewContext[Browse Context Store]

        StartOnboard --> OnboardProgress[Show Analysis Progress]
        OnboardProgress --> OnboardDone[Context Store Populated]
        OnboardDone --> User

        StartTask --> EnrichedAgent[Agent Has Full Context]
        EnrichedAgent --> User

        ViewMemory --> FactList[Display Cross-Session Facts]
        FactList --> User

        ViewContext --> ContextBrowser[Show Analysis + Stack + Conventions]
        ContextBrowser --> User
    end

    subgraph "Back-Stage (Implementation)"
        StartOnboard --> Onboarder["BrownfieldOnboarder\nasync pipeline ⚡"]
        Onboarder --> ScanFiles["Scan Project\nFile Tree 📊"]
        ScanFiles --> DetectStack["Detect Tech Stack\n(package.json, Cargo.toml, etc.) 🎯"]
        DetectStack --> AnalyzeConventions["Extract Code\nConventions 🎯"]
        AnalyzeConventions --> Store["ContextStore.save() 💾"]

        Store --> ContextDir[".acli/context/ 💾"]
        ContextDir --> AnalysisJSON["codebase_analysis.json"]
        ContextDir --> StackJSON["tech_stack.json"]
        ContextDir --> ConventionsJSON["conventions.json"]
        ContextDir --> DecisionsJSONL["decisions.jsonl"]

        StartTask --> LoadContext["ContextStore.load() ⚡"]
        LoadContext --> ContextDir
        LoadContext --> LoadMemory["MemoryManager.load() ⚡"]
        LoadMemory --> MemoryFile[".acli/memory/\nproject_memory.json 💾"]

        LoadContext --> Chunker["KnowledgeChunker\nsegment files 📊"]
        Chunker --> Segments["Relevant Code\nChunks 🎯"]

        LoadMemory --> Facts["Cross-Session\nFacts 💾"]
        Segments --> Inject["AgentFactory\ninject context 🔄"]
        Facts --> Inject
        ContextDir --> Inject
        Inject --> EnrichedAgent

        Onboarder --> AgentLearn["Agents Record\nNew Facts ✅"]
        EnrichedAgent --> AgentLearn
        AgentLearn --> MemWrite["MemoryManager\n.add_fact() 💾"]
        MemWrite --> MemoryFile

        AgentLearn --> DecisionWrite["ContextStore\n.add_decision() 💾"]
        DecisionWrite --> DecisionsJSONL

        Onboarder -.->|"Empty project dir"| EmptyErr["Skip Analysis,\nCreate Empty Store ⏱️"]
        EmptyErr --> Store

        LoadContext -.->|".acli/context/ missing"| NoCtxErr["Return Empty Context,\nSuggest 'acli onboard' 🔄"]
        NoCtxErr --> Inject

        Chunker -.->|"File too large (>10K lines)"| ChunkErr["Split Into Smaller\nSegments ⏱️"]
        ChunkErr --> Segments
    end
```

## Key Insights

- **Never Start From Scratch:** After onboarding, every agent session loads the project's tech stack, conventions, and historical decisions. Session 10 is as informed as session 1.
- **Memory Compounds Value:** Facts recorded by one agent (e.g., "this project uses PostgreSQL with pgvector") are available to all future agents, building institutional knowledge over time.
- **Technical Enabler:** The 4-file context store (analysis, stack, conventions, decisions) separates concerns so agents can load only what they need, keeping prompt sizes manageable.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
