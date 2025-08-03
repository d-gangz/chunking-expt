# What This Does

Contains team communication, planning documents, and experiment strategies for coordinating the chunking optimization project across team members.

# File Structure

```
├── 1-aug.md        # Team update from August 1st
├── expt-plan.md    # Comprehensive experiment plan and methodology
└── request.md      # Initial project requirements and goals
```

# Quick Start

- Entry point: `expt-plan.md` - read for overall strategy
- Background: `request.md` - understand project goals
- Updates: `1-aug.md` - latest team communication

# How It Works

These documents coordinate the multi-phase experiment to evaluate different chunking strategies, defining roles, responsibilities, and the systematic approach for fair comparison across methods.

# Interfaces

```
Team Structure:
- Gang (Product): Ground truth, chunking strategies, evaluation
- Jake (Engineer): Database setup, API endpoints
- Jair (ML): Review and validation
- Mark (PM): Business requirements

Experiment Flow:
1. Create base ground truth (Step 0)
2. Implement chunking strategy
3. Generate embeddings and load DB
4. Map ground truth to chunks
5. Run evaluations
6. Analyze results
```

# Dependencies

**Process Dependencies:**
- Defines workflow for all numbered directories
- Sets evaluation methodology and metrics
- Establishes team responsibilities

**Cross-Directory Usage:**
- Referenced by: All implementation directories
- Guides: Overall project execution
- Documents: Decision rationale and approach

# Key Patterns

- Systematic evaluation framework
- Strategy-agnostic ground truth
- Repeatable process for new strategies
- Clear team responsibility matrix

# Common Tasks

- Add new strategy: Follow Step 1-5 in expt-plan.md
- Understand context: Read request.md first
- Check progress: Review latest update file

# Recent Updates

- Defined comprehensive experiment methodology
- Established base ground truth approach
- Created repeatable evaluation framework

# Watch Out For

- Keep all strategies using same base ground truth
- Document decisions in communication files
- Coordinate database changes with Jake
- Review with Jair/Mark before major changes