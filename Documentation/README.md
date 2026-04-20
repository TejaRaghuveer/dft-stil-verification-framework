# DFT Verification Documentation Hub

| Document | Description |
|----------|-------------|
| [WEEK3_PRODUCTION.md](WEEK3_PRODUCTION.md) | Week 3 integration overview |
| [pattern_execution_manual.md](pattern_execution_manual.md) | How to run patterns and flows |
| [testbench_user_guide.md](testbench_user_guide.md) | UVM testbench quick reference |
| [troubleshooting_guide.md](troubleshooting_guide.md) | Common failures and fixes |
| [production_readiness_checklist.md](production_readiness_checklist.md) | Tapeout checklist |
| [design_modification_recommendations.md](design_modification_recommendations.md) | When FC/timing gaps remain |
| [GPU_SHADER_DFT_SPECIALIZATION.md](GPU_SHADER_DFT_SPECIALIZATION.md) | GPU ALU/register/pipeline DFT specialization |
| [MULTI_CORE_CACHE_INTERCONNECT_DFT.md](MULTI_CORE_CACHE_INTERCONNECT_DFT.md) | Cache coherence and interconnect verification |
| [ML_PATTERN_OPTIMIZATION.md](ML_PATTERN_OPTIMIZATION.md) | ML-based test pattern optimization and fault prediction |

Project docs also live under `docs/` (architecture, user guide, API, CI/CD).

## Changes I Made to This Documentation Set

- Grouped documents by execution flow, troubleshooting, readiness, and advanced specialization.
- Added GPU shader, multi-core interconnect, and ML optimization references into one discoverable hub.
- Kept the document map compact so new contributors can quickly find the right guide.

## Difficulties I Faced While Organizing Docs

- Some topics overlap (for example, troubleshooting across production and user guides).
- Technical depth differs by audience, from onboarding-level to architecture-level material.

## How I Resolved Those Difficulties

- I used this file as the primary map and delegated details to topic-specific documents.
- I kept short descriptions per file to reduce ambiguity during team handoff.
- I separated practical run guides from design rationale to support both day-to-day use and long-term maintenance.

## Documentation Contact

For updates or clarifications, contact **Raghuveer**:
- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`
