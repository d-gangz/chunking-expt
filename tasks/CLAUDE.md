# What This Does

Contains Product Requirements Documents (PRDs) and implementation task lists for major infrastructure changes and feature development in the chunking experiment project.

# File Structure

```
├── prd-migrate-to-local-supabase.md      # PRD for cloud to local migration
├── prd-setup_db.md                       # Database setup requirements
├── tasks-prd-migrate-to-local-supabase.md # Migration implementation tasks
└── tasks-setup_db_plan.md               # Database setup task breakdown
```

# Quick Start

- Entry point: Read PRDs before implementation tasks
- PRDs: Define requirements and goals
- Task lists: Break down implementation steps

# How It Works

PRDs define the "what" and "why" of major changes, while task lists provide the "how" with specific implementation steps. This separation ensures clear requirements before diving into technical details.

# Interfaces

```
Document Structure:
PRDs:
- Introduction/Overview
- Goals (numbered list)
- User Stories
- Functional Requirements
- Technical Specifications
- Success Criteria

Task Lists:
- Prerequisites
- Step-by-step implementation
- Verification procedures
- Rollback plans
```

# Dependencies

**Documentation Dependencies:**
- Informs: Implementation in all numbered directories
- References: Existing architecture and constraints
- Guides: Technical decision making

**Cross-Directory Usage:**
- Implemented by: Respective feature directories
- Referenced by: `/communication/` for planning
- Results in: Changes across multiple directories

# Key Patterns

- PRD-first approach for major changes
- Task decomposition for complex features
- Clear success criteria definition
- Rollback planning for infrastructure changes

# Common Tasks

- New feature: Write PRD first, then task list
- Review progress: Check task completion status
- Understand rationale: Read PRD before implementation

# Recent Updates

- Completed local Supabase migration
- Established PRD-driven development process
- Created detailed task breakdowns

# Watch Out For

- Always create PRD before major changes
- Keep task lists updated during implementation
- Document decisions and trade-offs
- Consider rollback procedures for infrastructure