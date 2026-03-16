# Fault Coverage Metrics, Standards, and Industry Best Practices

This document provides detailed comments on fault coverage metrics, relevant IEEE/IEC standards, and industry best practices used in the fault coverage analysis system.

---

## 1. Fault Coverage Metrics (Detailed Comments)

### 1.1 Fault Coverage (FC)

**Formula:** Fault Coverage = (Detected / (Total − Undetectable)) × 100%

**Definition:** Percentage of *detectable* faults that are detected by the test set. Undetectable (redundant) faults are excluded from the denominator because they cannot be detected by any test; including them would unfairly lower the metric.

**Usage:** Primary metric for sign-off. Industry typically targets ≥95% for commercial devices; safety-critical or high-reliability applications often require ≥99%.

**Note:** "Total" is the full fault list (e.g. single stuck-at, transition, or path delay); "Detected" counts faults for which at least one pattern produces a failing response when the fault is present.

---

### 1.2 Test Coverage (TC)

**Formula:** Test Coverage = (Detected / (Total − Undetectable − Untestable)) × 100%

**Definition:** Percentage of *testable* faults that are detected. Untestable faults are those that cannot be reached or observed by the test infrastructure (e.g. sequential depth limit, no scan path, initialization impossible). They are excluded from the denominator so that the metric reflects how well the test set covers faults that are in principle testable.

**Usage:** Complements Fault Coverage by separating "we did not generate a pattern" from "the design does not allow a pattern." High FC with lower TC indicates many untestable faults (design or flow limitation).

---

### 1.3 Defect Level (DL)

**Formula (escape rate):** DL = 1 − (Fault_Coverage / 100) when expressed as a fraction of defects escaping test. In parts per million: DL_ppm = (1 − FC/100) × 10⁶.

**Williams–Brown model (yield-based):** DL = 1 − Y^(1−T), where:
- Y = manufacturing yield (fraction of defect-free parts),
- T = fault coverage (0 ≤ T ≤ 1).

This relates defect level (probability a shipped part is defective) to yield and test effectiveness. Higher fault coverage and higher yield both reduce defect level.

**Interpretation:** Defect level (or escape rate) is the proportion of defective parts that pass test. Targets are often expressed in ppm (e.g. &lt;100 ppm for mature processes, &lt;30 ppm for critical applications).

---

### 1.4 Pattern Efficiency

**Formula:** Pattern Efficiency = (Total faults detected across all patterns) / (Number of patterns that detect at least one fault).

**Definition:** Average number of faults detected per pattern. Used to compare ATPG strategies and to estimate how many additional patterns might be needed to reach a coverage target (in combination with gap analysis).

---

### 1.5 Coverage Contribution (per pattern)

**Definition:** For each pattern, the number of *unique* faults it detects and the percentage of the detectable fault set that this represents. Used for:
- Identifying high-value patterns (e.g. for smoke or minimal suites),
- Pareto analysis (top N patterns detect X% of faults),
- Redundancy and essential-pattern analysis.

---

## 2. IEEE and IEC Standards (Relevant to Fault Coverage and Testability)

### 2.1 IEEE 1149.1 (Boundary-Scan / JTAG)

**Title:** Standard for Test Access Port and Boundary-Scan Architecture.

**Relevance:** Defines the test access port (TAP) and boundary-scan architecture used for board-level and chip-level test. Many ATPG flows use the same or similar scan chains and clocking; fault coverage is measured for faults that are *observable* and *controllable* via this (or an equivalent) test infrastructure. Compliance with 1149.1 does not specify a fault coverage number but implies that testability is designed in (e.g. scan, TAP).

---

### 2.2 IEEE 1450 (STIL)

**Title:** Standard Test Interface Language (STIL).

**Relevance:** STIL describes test patterns, timing, and structure. The fault coverage analysis system can consume pattern data that originates from or is exported in STIL-compliant flows. Pattern names, vector counts, and (when provided by the flow) fault lists can be used to compute coverage and pattern contribution.

---

### 2.3 IEC 61149.1 and Related Testability Expectations

**Note:** IEC 61149.1 and similar IEC standards are sometimes cited in the context of testability and quality expectations for electronic systems. Exact numbering and scope may vary by industry (e.g. safety, automotive). In practice:

- **Testability and coverage expectations** are often specified in customer or safety standards (e.g. ISO 26262 for automotive, DO-254 for aerospace), which may reference or align with IEC/IEEE test and quality practices.
- **Fault coverage** is used as a *measure of test quality*: higher coverage is generally required for higher integrity levels.
- This implementation follows the common definitions of Fault Coverage, Test Coverage, and Defect Level as used in semiconductor ATPG and in standards that reference fault simulation and defect level.

When a project cites a specific standard (e.g. IEC 61149.1), the user should map that standard’s requirements to the metrics above (e.g. minimum FC %, maximum defect level in ppm) and configure the report target and thresholds accordingly (e.g. `coverage_target_pct`, defect level in the analysis report).

---

## 3. Industry Best Practices

### 3.1 Coverage Targets

- **Stuck-at faults:** Typically ≥95% fault coverage for production; ≥99% for safety-critical or high-reliability.
- **Transition delay (TDF) / path delay:** Often slightly lower than stuck-at (e.g. 90–95%) due to timing and pattern count; at-speed capture and timing closure are critical.
- **Defect level:** Often specified in ppm (e.g. &lt;100 ppm); achieved by combining high yield and high fault coverage (Williams–Brown).

### 3.2 Categorizing Undetected Faults

- **DETECTED:** At least one pattern detects the fault.
- **UNDETECTABLE:** Redundant or no observable path; exclude from coverage denominator; design review if count is high.
- **UNTESTABLE:** Not reachable/observable with current test infrastructure (depth, scan, init); improve design-for-test or relax ATPG constraints.
- **RETRY_NEEDED:** May be detectable with different patterns or timing (e.g. at-speed, different capture edge); re-run ATPG or add patterns.

Best practice: feed ATPG tool’s aborted/undetectable/untestable lists into the analyzer so that Fault Coverage and Test Coverage use the correct denominators and reports are accurate.

### 3.3 Pattern and Report Usage

- Use **Pareto analysis** (top N patterns detect X% of faults) to build minimal or smoke suites and to spot over-reliance on a few patterns.
- Use **pattern contribution** and **essential/redundant** analysis to trim redundancy and protect high-value patterns.
- Use **coverage by type** (stuck-at, transition, path) and **by module** to find gaps and target ATPG or design changes.
- Use **recommendations** (e.g. “Path delay below target”, “Consider scan for FSM”) to drive follow-up actions.

### 3.4 Design and Flow

- Keep **sequential depth** and **scan access** in mind; high untestable counts often indicate design or flow limits.
- For **at-speed and delay tests**, align pattern generation (e.g. capture edge, clocking) with the report’s fault types and recommendations.
- **Re-target aborted faults** with relaxed or different constraints when RETRY_NEEDED or untestable counts are high.

---

## 4. References (Conceptual)

- Williams, T.W., Brown, N.C.: “Defect Level as a Function of Fault Coverage,” IEEE Trans. Computers, 1981 (Williams–Brown defect level model).
- IEEE Std 1149.1: Test Access Port and Boundary-Scan Architecture.
- IEEE Std 1450: Standard Test Interface Language (STIL).
- Project-specific or customer standards (e.g. IEC 61149.1, ISO 26262, DO-254) should be consulted for exact coverage and defect-level requirements.
