# Prompt Routing Engine

**Type:** Feature Diagram
**Last Updated:** 2026-03-19
**Related Files:**
- `src/acli/routing/router.py`
- `src/acli/routing/workflows.py`

## Purpose

Classifies any free-text user prompt into one of 8 typed workflows so the correct agent sequence is spawned automatically, eliminating manual configuration for every project type.

## Diagram

```mermaid
graph TD
    subgraph "Front-Stage (User Experience)"
        User([User]) -->|"acli run . 'fix the login crash'"| PromptEntry[Enter Free-Text Prompt]
        PromptEntry --> Thinking[CLI Shows 'Classifying...']
        Thinking --> Result[Display Detected Workflow Type]
        Result --> AgentSeq[Show Agent Sequence Starting]
        AgentSeq --> User
    end

    subgraph "Back-Stage (Implementation)"
        PromptEntry --> Classify["PromptRouter.classify() ⚡"]
        Classify --> RegexMatch{"Regex Pattern\nMatching 🎯"}

        RegexMatch -->|"fix/debug/broken/crash/error/bug"| DebugWF[WorkflowType.DEBUG]
        RegexMatch -->|"refactor/migrate/convert/restructure"| RefactorWF[WorkflowType.REFACTOR]
        RegexMatch -->|"No keyword match"| ProjectScan["Count Source Files\nin project_dir 📊"]

        ProjectScan --> FileCheck{"source_files < 5? 🎯"}
        FileCheck -->|Yes| GreenfieldWF[WorkflowType.GREENFIELD_APP]
        FileCheck -->|No| BrownfieldDetect{"Prompt implies\nnew task vs onboard? 🎯"}

        BrownfieldDetect -->|"Onboard/analyze"| OnboardWF[WorkflowType.BROWNFIELD_ONBOARD]
        BrownfieldDetect -->|"Task/feature"| TaskWF[WorkflowType.BROWNFIELD_TASK]

        RegexMatch -->|"iOS/swift/xcode patterns"| IOSWF[WorkflowType.IOS_APP]
        RegexMatch -->|"cli/command/flag patterns"| CLIWF[WorkflowType.CLI_TOOL]
        RegexMatch -->|"No category match"| FreeWF[WorkflowType.FREE_TASK]

        DebugWF --> SeqLookup["_get_agent_sequence() ⚡"]
        RefactorWF --> SeqLookup
        GreenfieldWF --> SeqLookup
        OnboardWF --> SeqLookup
        TaskWF --> SeqLookup
        IOSWF --> SeqLookup
        CLIWF --> SeqLookup
        FreeWF --> SeqLookup

        SeqLookup --> AgentPipeline["Build Agent Pipeline 🔄"]
        AgentPipeline --> AgentSeq

        Classify -.->|"Empty/invalid prompt"| ClassifyErr[Return FREE_TASK Fallback]
        ClassifyErr --> FreeWF

        ProjectScan -.->|"Dir not found / permission error"| ScanErr["Log Warning,\nDefault to FREE_TASK ⏱️"]
        ScanErr --> FreeWF
    end
```

## Key Insights

- **Zero Config for Users:** Users type natural language; no YAML, no workflow selection menus. The router handles everything from "fix the crash" to "build me an iOS app."
- **Graceful Fallback:** Unrecognizable prompts and errors always land on FREE_TASK rather than failing, so the system never blocks the user.
- **Technical Enabler:** Regex-first classification is fast (sub-millisecond) and deterministic. File counting for brownfield detection avoids expensive AST parsing at the routing stage.

## Change History

- **2026-03-19:** Initial creation (v2 bootstrap)
