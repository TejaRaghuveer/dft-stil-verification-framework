"""
ML-based pattern optimization for DFT/ATPG pattern selection.

This module provides a lightweight, dependency-free ML workflow:
  - Feature extraction from ATPG/pattern DB vectors
  - Predictor models for coverage/time/power/timing-risk
  - Pattern subset optimization for target coverage
  - Anomaly detection for suspicious patterns
  - Fault likelihood prediction
  - Continuous-learning style metric tracking
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pattern_db.pattern_database import PatternDatabase, PatternRecord


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b else default


def _hamming(a: str, b: str) -> int:
    n = min(len(a), len(b))
    return sum(1 for i in range(n) if a[i] != b[i]) + abs(len(a) - len(b))


def _is_alternating(s: str) -> bool:
    if len(s) < 2:
        return False
    if s[0] not in ("0", "1"):
        return False
    for i in range(1, len(s)):
        if s[i] not in ("0", "1"):
            return False
        if s[i] == s[i - 1]:
            return False
    return True


@dataclass
class PatternFeatureVector:
    pattern_name: str
    features: Dict[str, float]
    labels: Dict[str, float]
    fault_list: List[str] = field(default_factory=list)


class FeatureExtractionEngine:
    """Extract ATPG pattern features and normalize-ready vectors."""

    FEATURE_ORDER = [
        "scan_chain_length",
        "vector_count",
        "bit_transition_count",
        "hamming_between_vectors",
        "zeros_ratio",
        "ones_ratio",
        "alternating_ratio",
        "all_zeros_ratio",
        "all_ones_ratio",
        "capture_cycle_count",
        "io_activity_ratio",
        "estimated_shift_cycles",
        "fault_count",
    ]

    def extract(
        self,
        rec: PatternRecord,
        execution_metrics: Optional[Dict[str, Any]] = None,
    ) -> PatternFeatureVector:
        vectors = [v.strip() for v in rec.vector_lines if v.strip()]
        if not vectors:
            vectors = ["0" * max(rec.size_bits, 1)]
        scan_len = max(rec.size_bits, len(vectors[0]), 1)

        bit_transition_count = 0
        total_adj_pairs = 0
        for vec in vectors:
            for i in range(1, len(vec)):
                if vec[i] in ("0", "1") and vec[i - 1] in ("0", "1"):
                    total_adj_pairs += 1
                    if vec[i] != vec[i - 1]:
                        bit_transition_count += 1

        hamming_between_vectors = 0
        for i in range(1, len(vectors)):
            hamming_between_vectors += _hamming(vectors[i - 1], vectors[i])

        all_bits = "".join(vectors)
        ones = all_bits.count("1")
        zeros = all_bits.count("0")
        total_bits = max(ones + zeros, 1)

        all_zeros_count = sum(1 for v in vectors if set(v).issubset({"0"}))
        all_ones_count = sum(1 for v in vectors if set(v).issubset({"1"}))
        alternating_count = sum(1 for v in vectors if _is_alternating(v))
        vector_count = max(len(vectors), 1)

        capture_cycle_count = max(len(vectors) // 2, 1)
        estimated_shift_cycles = scan_len * vector_count
        io_activity_ratio = _safe_div(bit_transition_count + hamming_between_vectors, max(estimated_shift_cycles, 1))

        em = execution_metrics or {}
        exec_time_ns = float(em.get("duration_ns", rec.execution_time_ns or (estimated_shift_cycles * 100.0)))
        power_proxy_mw = float(
            em.get("power_mw", 15.0 + 0.02 * bit_transition_count + 0.005 * hamming_between_vectors + 0.001 * scan_len)
        )
        timing_margin_ns = float(em.get("timing_margin_ns", max(0.05, 2.5 - 0.0025 * bit_transition_count)))
        timing_violation_prob = float(em.get("timing_violation_prob", 1.0 if timing_margin_ns < 0.2 else 0.05))
        coverage_contribution = float(em.get("coverage_contribution", rec.coverage_contribution or rec.fault_count))

        feats = {
            "scan_chain_length": float(scan_len),
            "vector_count": float(vector_count),
            "bit_transition_count": float(bit_transition_count),
            "hamming_between_vectors": float(hamming_between_vectors),
            "zeros_ratio": _safe_div(zeros, total_bits),
            "ones_ratio": _safe_div(ones, total_bits),
            "alternating_ratio": _safe_div(alternating_count, vector_count),
            "all_zeros_ratio": _safe_div(all_zeros_count, vector_count),
            "all_ones_ratio": _safe_div(all_ones_count, vector_count),
            "capture_cycle_count": float(capture_cycle_count),
            "io_activity_ratio": float(io_activity_ratio),
            "estimated_shift_cycles": float(estimated_shift_cycles),
            "fault_count": float(rec.fault_count),
        }
        labels = {
            "coverage_contribution": max(coverage_contribution, 0.0),
            "execution_time_s": max(exec_time_ns / 1e9, 0.0),
            "power_mw": max(power_proxy_mw, 0.0),
            "timing_violation_prob": min(max(timing_violation_prob, 0.0), 1.0),
            "timing_margin_ns": timing_margin_ns,
        }
        return PatternFeatureVector(
            pattern_name=rec.pattern_name,
            features=feats,
            labels=labels,
            fault_list=list(rec.fault_list),
        )

    def as_array(self, fv: PatternFeatureVector) -> List[float]:
        return [float(fv.features.get(k, 0.0)) for k in self.FEATURE_ORDER]


class MinMaxNormalizer:
    def __init__(self) -> None:
        self._mins: List[float] = []
        self._maxs: List[float] = []

    def fit(self, x: Sequence[Sequence[float]]) -> None:
        if not x:
            self._mins, self._maxs = [], []
            return
        cols = len(x[0])
        self._mins = [min(row[i] for row in x) for i in range(cols)]
        self._maxs = [max(row[i] for row in x) for i in range(cols)]

    def transform_one(self, row: Sequence[float]) -> List[float]:
        out: List[float] = []
        for i, v in enumerate(row):
            mn = self._mins[i]
            mx = self._maxs[i]
            out.append(_safe_div(v - mn, (mx - mn), 0.0))
        return out

    def transform(self, x: Sequence[Sequence[float]]) -> List[List[float]]:
        return [self.transform_one(r) for r in x]


class KNNRegressor:
    """Small k-NN regressor for dependency-free ML prediction."""

    def __init__(self, k: int = 5):
        self.k = k
        self.x: List[List[float]] = []
        self.y: List[float] = []
        self._global_mean: float = 0.0

    def fit(self, x: Sequence[Sequence[float]], y: Sequence[float]) -> None:
        self.x = [list(r) for r in x]
        self.y = [float(v) for v in y]
        self._global_mean = mean(self.y) if self.y else 0.0

    def predict_one(self, row: Sequence[float]) -> float:
        if not self.x:
            return self._global_mean
        dists: List[Tuple[float, float]] = []
        for i, train in enumerate(self.x):
            dist = math.sqrt(sum((train[j] - row[j]) ** 2 for j in range(len(row))))
            dists.append((dist, self.y[i]))
        dists.sort(key=lambda t: t[0])
        top = dists[: max(1, min(self.k, len(dists)))]
        wsum = 0.0
        ysum = 0.0
        for d, val in top:
            w = 1.0 / (d + 1e-9)
            wsum += w
            ysum += w * val
        return _safe_div(ysum, wsum, self._global_mean)

    def predict(self, x: Sequence[Sequence[float]]) -> List[float]:
        return [self.predict_one(r) for r in x]


class PredictionModels:
    def __init__(self) -> None:
        self.coverage = KNNRegressor(k=7)
        self.exec_time = KNNRegressor(k=7)
        self.power = KNNRegressor(k=7)
        self.timing_risk = KNNRegressor(k=7)


class AnomalyDetectionEngine:
    """Flags high-power, long-runtime, and low-coverage outlier patterns."""

    @staticmethod
    def detect(pred_rows: List[Dict[str, Any]]) -> List[str]:
        if not pred_rows:
            return []
        powers = [r["pred_power_mw"] for r in pred_rows]
        times = [r["pred_exec_time_s"] for r in pred_rows]
        covs = [r["pred_coverage"] for r in pred_rows]
        pm = mean(powers)
        tm = mean(times)
        cm = mean(covs)
        ps = math.sqrt(mean([(p - pm) ** 2 for p in powers])) or 1.0
        ts = math.sqrt(mean([(t - tm) ** 2 for t in times])) or 1.0
        alerts: List[str] = []
        for r in pred_rows:
            if (r["pred_power_mw"] - pm) / ps > 2.0:
                alerts.append(
                    f"{r['pattern_name']}: Very high power ({r['pred_power_mw']:.1f} mW) - investigate switching/congestion"
                )
            if (r["pred_exec_time_s"] - tm) / ts > 2.0:
                alerts.append(
                    f"{r['pattern_name']}: High execution time ({r['pred_exec_time_s']:.2f}s) - consider compression"
                )
            if r["pred_coverage"] < max(0.1, cm * 0.2):
                alerts.append(
                    f"{r['pattern_name']}: Low fault detection potential ({r['pred_coverage']:.1f}) - candidate for removal"
                )
        return alerts[:40]


class FaultPredictionEngine:
    """Predict likely-detected faults based on feature similarity."""

    def __init__(self, vectors: Sequence[PatternFeatureVector], fe: FeatureExtractionEngine, norm: MinMaxNormalizer):
        self._fault_signatures: Dict[str, List[float]] = {}
        self._fe = fe
        self._norm = norm
        fault_to_rows: Dict[str, List[List[float]]] = {}
        for v in vectors:
            arr = norm.transform_one(fe.as_array(v))
            for f in v.fault_list:
                fault_to_rows.setdefault(f, []).append(arr)
        for fault, rows in fault_to_rows.items():
            cols = len(rows[0])
            self._fault_signatures[fault] = [mean([r[c] for r in rows]) for c in range(cols)]

    def predict_faults(self, row: List[float], top_n: int = 10) -> List[Tuple[str, float]]:
        if not self._fault_signatures:
            return []
        scored: List[Tuple[str, float]] = []
        for f, sig in self._fault_signatures.items():
            d = math.sqrt(sum((row[i] - sig[i]) ** 2 for i in range(len(row))))
            p = 1.0 / (1.0 + d)
            scored.append((f, p))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:top_n]


class ContinuousLearningTracker:
    def __init__(self, history_file: str):
        self.history_file = Path(history_file)

    def update(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        hist: List[Dict[str, Any]] = []
        if self.history_file.exists():
            try:
                hist = json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception:
                hist = []
        hist.append(metrics)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(hist, indent=2), encoding="utf-8")
        rolling: Dict[str, float] = {}
        for k in metrics.keys():
            vals = [float(h.get(k, 0.0)) for h in hist[-20:]]
            rolling[k] = round(mean(vals), 3) if vals else 0.0
        return {"history_points": len(hist), "rolling_accuracy": rolling}


class PatternSelectionOptimizer:
    def optimize(
        self,
        predictions: List[Dict[str, Any]],
        target_coverage: float = 95.0,
        max_patterns: Optional[int] = None,
    ) -> Dict[str, Any]:
        ranked = sorted(
            predictions,
            key=lambda r: _safe_div(r["pred_coverage"], (r["pred_exec_time_s"] + 1e-3)) - 0.01 * r["pred_power_mw"],
            reverse=True,
        )
        selected: List[Dict[str, Any]] = []
        cov = 0.0
        limit = max_patterns if max_patterns is not None else len(ranked)
        for r in ranked:
            if len(selected) >= limit:
                break
            selected.append(r)
            cov = min(100.0, cov + max(r["pred_coverage"], 0.0))
            if cov >= target_coverage:
                break
        return {
            "selected_patterns": selected,
            "selected_count": len(selected),
            "predicted_coverage_pct": round(cov, 3),
        }


class PatternMLAnalyzer:
    def __init__(self) -> None:
        self.fe = FeatureExtractionEngine()
        self.norm = MinMaxNormalizer()
        self.models = PredictionModels()

    def _build_vectors(
        self,
        db: PatternDatabase,
        execution_metrics_by_pattern: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[PatternFeatureVector]:
        out: List[PatternFeatureVector] = []
        emap = execution_metrics_by_pattern or {}
        for rec in db._patterns.values():
            out.append(self.fe.extract(rec, emap.get(rec.pattern_name)))
        return out

    def _fit_models(self, vectors: List[PatternFeatureVector]) -> Tuple[List[List[float]], Dict[str, List[float]]]:
        x_raw = [self.fe.as_array(v) for v in vectors]
        self.norm.fit(x_raw)
        x = self.norm.transform(x_raw)
        labels = {
            "coverage": [v.labels["coverage_contribution"] for v in vectors],
            "time": [v.labels["execution_time_s"] for v in vectors],
            "power": [v.labels["power_mw"] for v in vectors],
            "timing_risk": [v.labels["timing_violation_prob"] for v in vectors],
        }
        self.models.coverage.fit(x, labels["coverage"])
        self.models.exec_time.fit(x, labels["time"])
        self.models.power.fit(x, labels["power"])
        self.models.timing_risk.fit(x, labels["timing_risk"])
        return x, labels

    def _accuracy_pct(self, y_true: Sequence[float], y_pred: Sequence[float]) -> float:
        if not y_true:
            return 0.0
        ape = []
        for t, p in zip(y_true, y_pred):
            denom = abs(t) if abs(t) > 1e-9 else 1.0
            ape.append(abs(t - p) / denom)
        mape = mean(ape) if ape else 1.0
        return max(0.0, min(100.0, (1.0 - mape) * 100.0))

    def analyze_and_optimize(
        self,
        db: PatternDatabase,
        execution_metrics_by_pattern: Optional[Dict[str, Dict[str, Any]]] = None,
        target_coverage: float = 95.0,
        max_patterns: Optional[int] = None,
        learning_history_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        vectors = self._build_vectors(db, execution_metrics_by_pattern)
        x, labels = self._fit_models(vectors)

        pred_cov = self.models.coverage.predict(x)
        pred_time = self.models.exec_time.predict(x)
        pred_power = self.models.power.predict(x)
        pred_risk = self.models.timing_risk.predict(x)

        perf = {
            "fault_coverage_predictor_accuracy_pct": round(self._accuracy_pct(labels["coverage"], pred_cov), 2),
            "execution_time_predictor_accuracy_pct": round(self._accuracy_pct(labels["time"], pred_time), 2),
            "power_predictor_accuracy_pct": round(self._accuracy_pct(labels["power"], pred_power), 2),
            "timing_margin_predictor_accuracy_pct": round(100.0 - self._accuracy_pct(labels["timing_risk"], pred_risk), 2),
        }

        pred_rows: List[Dict[str, Any]] = []
        for i, v in enumerate(vectors):
            pred_rows.append(
                {
                    "pattern_name": v.pattern_name,
                    "pred_coverage": max(pred_cov[i], 0.0),
                    "pred_exec_time_s": max(pred_time[i], 0.0),
                    "pred_power_mw": max(pred_power[i], 0.0),
                    "pred_timing_violation_prob": min(max(pred_risk[i], 0.0), 1.0),
                    "fault_count": len(v.fault_list),
                    "fault_list": list(v.fault_list),
                }
            )

        optimizer = PatternSelectionOptimizer()
        opt = optimizer.optimize(pred_rows, target_coverage=target_coverage, max_patterns=max_patterns)

        original_n = len(pred_rows)
        selected_n = opt["selected_count"]
        anomalies = AnomalyDetectionEngine.detect(pred_rows)
        fault_pred_engine = FaultPredictionEngine(vectors, self.fe, self.norm)

        # Predict likely faults for top selected patterns.
        top_fault_map: Dict[str, List[Dict[str, Any]]] = {}
        for r in opt["selected_patterns"][:20]:
            v = next((vv for vv in vectors if vv.pattern_name == r["pattern_name"]), None)
            if not v:
                continue
            arr = self.norm.transform_one(self.fe.as_array(v))
            likely = fault_pred_engine.predict_faults(arr, top_n=10)
            top_fault_map[r["pattern_name"]] = [{"fault_id": f, "likelihood": round(p, 4)} for f, p in likely]

        continuous = {}
        if learning_history_path:
            continuous = ContinuousLearningTracker(learning_history_path).update(
                {
                    "coverage_model_accuracy": perf["fault_coverage_predictor_accuracy_pct"],
                    "time_model_accuracy": perf["execution_time_predictor_accuracy_pct"],
                    "power_model_accuracy": perf["power_predictor_accuracy_pct"],
                }
            )

        top50 = sorted(pred_rows, key=lambda r: r["pred_coverage"], reverse=True)[:50]
        top50_table = [
            {
                "rank": i + 1,
                "pattern_name": r["pattern_name"],
                "predicted_faults": round(r["pred_coverage"], 2),
                "unique_faults": r["fault_count"],
                "efficiency": round(_safe_div(r["pred_coverage"], (r["pred_exec_time_s"] + 1e-3)), 3),
            }
            for i, r in enumerate(top50)
        ]

        summary = {
            "original_pattern_set_size": original_n,
            "ml_optimized_set_size": selected_n,
            "optimized_fraction_pct": round(_safe_div(selected_n * 100.0, max(original_n, 1)), 2),
            "predicted_coverage_preserved_pct": round(opt["predicted_coverage_pct"], 3),
            "predicted_test_time_reduction_pct": round(
                100.0
                * (1.0 - _safe_div(
                    sum(x["pred_exec_time_s"] for x in opt["selected_patterns"]),
                    max(sum(x["pred_exec_time_s"] for x in pred_rows), 1e-9),
                )),
                2,
            ),
        }

        return {
            "summary": summary,
            "model_performance": perf,
            "top_50_patterns_by_predicted_coverage": top50_table,
            "anomaly_patterns_detected": anomalies,
            "selected_patterns": opt["selected_patterns"],
            "fault_prediction_for_top_selected": top_fault_map,
            "continuous_learning": continuous,
        }

    @staticmethod
    def format_text_report(report: Dict[str, Any]) -> str:
        s = report.get("summary", {})
        m = report.get("model_performance", {})
        lines = [
            "ML PATTERN OPTIMIZATION RESULTS",
            "=" * 32,
            "",
            f"Original Pattern Set Size: {s.get('original_pattern_set_size', 0)} patterns",
            (
                f"ML-Optimized Set Size: {s.get('ml_optimized_set_size', 0)} patterns "
                f"({s.get('optimized_fraction_pct', 0)}% of original)"
            ),
            f"Coverage Preserved (predicted): {s.get('predicted_coverage_preserved_pct', 0)}%",
            f"Test Time Reduction (predicted): {s.get('predicted_test_time_reduction_pct', 0)}% faster",
            "",
            "ML Model Performance:",
            f"- Fault Coverage Predictor: {m.get('fault_coverage_predictor_accuracy_pct', 0)}% accuracy",
            f"- Execution Time Predictor: {m.get('execution_time_predictor_accuracy_pct', 0)}% accuracy",
            f"- Power Predictor: {m.get('power_predictor_accuracy_pct', 0)}% accuracy",
            "",
            "Top 50 Patterns by Predicted Coverage:",
            "Rank | Pattern Name | Predicted Faults | Unique Faults | Efficiency",
        ]
        for row in report.get("top_50_patterns_by_predicted_coverage", [])[:50]:
            lines.append(
                f"{row['rank']} | {row['pattern_name']} | {row['predicted_faults']} | {row['unique_faults']} | {row['efficiency']}"
            )
        lines.append("")
        lines.append("Anomaly Patterns Detected:")
        for a in report.get("anomaly_patterns_detected", [])[:20]:
            lines.append(f"- {a}")
        if not report.get("anomaly_patterns_detected"):
            lines.append("- None")
        return "\n".join(lines)


def analyze_pattern_db_with_ml(
    db: PatternDatabase,
    execution_metrics_by_pattern: Optional[Dict[str, Dict[str, Any]]] = None,
    target_coverage: float = 95.0,
    max_patterns: Optional[int] = None,
    out_json: Optional[str] = None,
    out_txt: Optional[str] = None,
    learning_history_path: Optional[str] = None,
) -> Dict[str, Any]:
    analyzer = PatternMLAnalyzer()
    report = analyzer.analyze_and_optimize(
        db,
        execution_metrics_by_pattern=execution_metrics_by_pattern,
        target_coverage=target_coverage,
        max_patterns=max_patterns,
        learning_history_path=learning_history_path,
    )
    if out_json:
        Path(out_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if out_txt:
        Path(out_txt).write_text(PatternMLAnalyzer.format_text_report(report), encoding="utf-8")
    return report

