# Multi-Core GPU Cache & Interconnect DFT Verification

This guide documents the multi-core specialization for cache coherence protocol and chip interconnect verification in GPU shader systems.

## Why this specialization exists

Single-core ALU/register checks are not enough for modern shader fabrics. Multi-core GPU behavior must validate:

- cache coherence correctness under concurrent accesses,
- routing and arbitration behavior under traffic contention,
- cross-core synchronization and data transfer integrity,
- protocol progress properties (deadlock/livelock freedom).

## Implemented modules

All logic lives in `python/gpu_shader/multi_core_verification.py`.

### 1) `CacheCoherenceVerifier`

Targets coherence behavior for MSI/MESI/MOESI-style designs:

- state transition checks,
- invalidation and write-back checks,
- cache tag hit/miss verification,
- scan-oriented cache tag/data write-read checks and corruption detection.

### 2) `InterconnectVerificationAgent`

Targets chip interconnect paths (NoC / mesh / crossbar / ring / bus):

- routing path verification,
- arbitration scenario verification (priority / round-robin),
- data integrity checks through routing,
- control propagation checks.

### 3) `MultiCoreTestCoordination`

Coordinates simultaneous per-core verification:

- synchronized launch across shader cores,
- inter-core transfer checks over interconnect,
- concurrent access scenario modeling.

### 4) `ProtocolComplianceVerifier`

Adds protocol compliance checks:

- coherence state-machine consistency checks,
- deadlock and livelock checks,
- lightweight formal proof stubs for coherence properties.

### 5) `InterconnectCoverageAnalyzer`

Summarizes:

- routing-path coverage,
- arbitration-scenario coverage,
- protocol-transition coverage,
- untested-feature diagnostics.

### 6) `MultiCoreTestSuite`

Includes:

- single-core functional test,
- multi-core coherence test,
- interconnect stress test,
- memory consistency test,
- cache invalidation test.

### 7) Result aggregation

Generated payload includes:

- per-core coverage summary,
- system-level coherence/interconnect coverage,
- critical path latency proxies across cores,
- inter-core communication verification status.

## Configuration format

Use:

```text
multi_core_config {
  num_shader_cores: 4;
  cache_level: L1;
  cache_type: INSTRUCTION_DATA_UNIFIED;
  cache_size_kb: 32;
  cache_line_bytes: 64;
  coherence_protocol: MESI;
  interconnect_type: MESH;
  verify_coherence: true;
  verify_interconnect: true;
}
```

Example file:

- `config/multi_core_config.example.txt`

## Running from Week 3 flow

From repo root:

```bash
set PYTHONPATH=python
python python/integrated_flow/week3_production.py --dry-run --out deliverables --multi-core-config config/multi_core_config.example.txt
```

To combine with per-core GPU specialization:

```bash
python python/integrated_flow/week3_production.py --dry-run --out deliverables --gpu-shader-config config/gpu_shader_config.example.txt --multi-core-config config/multi_core_config.example.txt
```

## Output artifacts

In `Reports/`:

- `multi_core_cache_interconnect_verification.json`
- `multi_core_cache_interconnect_verification.html`

Manifest keys:

- `outputs.multi_core_report_json`
- `outputs.multi_core_report_html`
- `multi_core_specialization`

## Notes on strategy

- Coherence transition checks are modeled as protocol-state/event coverage goals.
- Interconnect checks include route and arbitration stress but stay light enough for CI dry-runs.
- Formal proof content is generated as stubs and should be replaced with tool-generated logs for production sign-off.

## Maintainer

- **Raghuveer**
- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`
