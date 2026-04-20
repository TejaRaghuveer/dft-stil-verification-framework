# Documentation Index

I use this file as the main navigation point for the project docs. When someone joins the repo or needs to jump between usage guides, deep dives, and training material, this is the quickest path.

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

I organized the docs into practical usage paths (core guides, deep dives, tutorials, and diagrams) so the flow from onboarding to advanced debugging is clearer. I also linked operational docs with implementation references and added local search/index commands so people can find answers quickly without digging through folders manually.

## Challenges

As the project grew, documentation spread across multiple folders and similar topics started to overlap. That made discovery slower and made it harder to know which file should be treated as the source of truth during handoff.

## Resolution Approach

I treated this index as the single entry point, grouped content by topic, and standardized section names so teams can quickly decide where to go next. The search index tooling is there to reduce manual browsing and make day-to-day documentation use more efficient.

