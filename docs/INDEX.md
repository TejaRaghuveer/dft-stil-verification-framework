# Documentation Index

## Core Guides

- `README.md`
- `GETTING_STARTED.md`
- `docs/CI_CD_PIPELINE.md`
- `docs/USER_GUIDE.md`
- `docs/ARCHITECTURE.md`
- `docs/API_REFERENCE.md`
- `docs/TROUBLESHOOTING.md`
- `docs/BEST_PRACTICES.md`
- `docs/DESIGN_DOCUMENT.md`

## Knowledge Base

- `docs/KNOWLEDGE_BASE.md`
- `docs/faq.md`
- `docs/glossary.md`
- `docs/CODE_DOCUMENTATION_STANDARD.md`
- `docs/CODE_DOC_ROADMAP.md`
- `docs/DOCUMENTATION_TEMPLATE.md`

## Deep Dives

- `docs/deep_dives/jtag_protocol.md`
- `docs/deep_dives/stil_generation.md`
- `docs/deep_dives/fault_coverage.md`
- `docs/deep_dives/at_speed_testing.md`
- `docs/deep_dives/pattern_compression.md`
- `docs/deep_dives/multi_core_gpu_verification.md`

## Tutorials and Training

- `docs/tutorials/tutorial_1_setup.md`
- `docs/tutorials/tutorial_2_run_patterns.md`
- `docs/tutorials/tutorial_3_debug_failures.md`
- `docs/tutorials/tutorial_4_optimize.md`
- `training/TRAINING_PLAN.md`
- `training/video_scripts/`

## Diagrams

- `docs/diagrams/system_architecture.md`
- `docs/diagrams/data_flow.md`
- `docs/diagrams/jtag_fsm.md`
- `docs/diagrams/test_execution_flow.md`
- `docs/diagrams/coverage_analysis_flow.md`

## Search and Index Tooling

- Generate index: `python scripts/generate_doc_index.py`
- Search docs: `python scripts/doc_search.py "<query>"`
- Prebuilt index file: `docs/search_index.json`

## Changes Made

- Organized documents into clear usage paths (core guides, deep dives, tutorials, diagrams).
- Linked operational docs and implementation docs so onboarding is faster.
- Added local search/index commands so the team can quickly locate answers.

## Challenges

- The documentation set grew across multiple folders and became hard to navigate.
- Similar topics existed in different places, which made ownership and discovery confusing.

## Resolution Approach

- I created a single navigation entry-point with topic-first grouping.
- I standardized section naming so people can quickly choose the right document path.
- I added searchable indexing tooling to reduce time spent manually browsing files.

