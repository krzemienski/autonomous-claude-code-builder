# Unified Impact Diagrams Index

This directory contains all diagrams for the ACLI v2 (Shannon-ACLI) project, following Diagram Driven Development (DDD) methodology.

**Last Updated:** 2026-03-19

## Quick Links

- [System Architecture](#architecture-overview)
- [User Journeys](#user-journeys)
- [Features](#features)
- [Test Coverage](#test-coverage)

## Architecture Overview

High-level system design and component relationships.

- [System Overview](architecture/arch-system-overview.md) - Complete ACLI v2 pipeline: CLI → routing → orchestrator → 7 agents → validation → TUI
- [Security Defense-in-Depth](architecture/arch-security-defense-in-depth.md) - 6-layer security model protecting user projects from unauthorized operations
- [Agent Model Routing](architecture/arch-agent-model-routing.md) - How 7 agent types route to Opus (deep reasoning) vs Sonnet (fast execution)

## User Journeys

Time-based user experiences across the platform.

- [Prompt to Completion](journeys/sequence-prompt-to-completion.md) - Full lifecycle from typing a prompt to seeing completed work
- [Brownfield Onboarding](journeys/sequence-brownfield-onboarding.md) - Onboarding an existing codebase for context-aware AI assistance

## Features

Individual features and their user value.

- [Prompt Routing Engine](features/feature-prompt-routing-engine.md) - Classifying any prompt into 8 workflow types with appropriate agent sequences
- [Validation Engine](features/feature-validation-engine.md) - Functional validation with real evidence collection and mock detection
- [Context & Memory System](features/feature-context-memory-system.md) - Persistent project knowledge across sessions for smarter AI agents
- [TUI Dashboard](features/feature-tui-dashboard.md) - 7-panel cyberpunk monitoring dashboard with real-time agent streaming

## Test Coverage

How we protect user value through testing.

- [Functional Validation Strategy](tests/test-functional-validation-strategy.md) - No-mocks testing: 67 security tests + 8 E2E tests + platform validators

## Diagram Guidelines

All diagrams follow DDD principles:
- Show both Front-Stage (user experience) and Back-Stage (implementation)
- Include impact annotations explaining user value (⚡💾🛡️✅⏱️🔄📊🎯)
- Show error paths and recovery options
- Connect technical decisions to user benefit

## Recent Changes

- **2026-03-19:** Initial bootstrap — 10 diagrams covering full ACLI v2 architecture
