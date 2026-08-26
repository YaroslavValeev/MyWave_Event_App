"""Scoring engines — pure calculation (no DB).

Engines aligned with packages/shared-policy/rules_catalog.yaml:
- WSWS_DRIVE
- IWWF_CABLE_TI
- IWWF_BOAT_EIC
- MANUAL_PLACE (passthrough)
"""

from __future__ import annotations

from statistics import mean
from typing import Any

ENGINE_CRITERIA: dict[str, tuple[str, ...]] = {
    "WSWS_DRIVE": ("difficulty", "risk", "intensity", "variety", "execution"),
    "IWWF_CABLE_TI": ("technical_performance", "impression"),
    "IWWF_BOAT_EIC": ("execution", "intensity", "composition"),
    "MANUAL_PLACE": (),
    "IWWF_WAKESURF_SUBJECTIVE": ("overall",),
}

CRITERIA_LABELS_RU: dict[str, str] = {
    "difficulty": "Difficulty (сложность)",
    "risk": "Risk (риск)",
    "intensity": "Intensity (интенсивность)",
    "variety": "Variety (разнообразие)",
    "execution": "Execution (исполнение)",
    "technical_performance": "Technical (техника)",
    "impression": "Impression (впечатление)",
    "composition": "Composition (композиция)",
    "overall": "Overall",
}


class ScoringError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def criteria_for_engine(engine: str) -> tuple[str, ...]:
    if engine not in ENGINE_CRITERIA:
        raise ScoringError("unknown_engine", f"Unknown scoring engine: {engine}")
    return ENGINE_CRITERIA[engine]


def normalize_criteria_scores(
    engine: str,
    criteria: dict[str, float],
    *,
    max_score: float = 100.0,
) -> dict[str, float]:
    expected = criteria_for_engine(engine)
    if not expected:
        raise ScoringError("manual_engine", "MANUAL_PLACE does not accept criteria scores")
    missing = [c for c in expected if c not in criteria]
    if missing:
        raise ScoringError("missing_criteria", f"Missing criteria: {', '.join(missing)}")
    out: dict[str, float] = {}
    for key in expected:
        value = float(criteria[key])
        if value < 0 or value > max_score:
            raise ScoringError(
                "criteria_out_of_range",
                f"{key} must be between 0 and {max_score}",
            )
        out[key] = round(value, 3)
    return out


def judge_sheet_total(engine: str, criteria: dict[str, float]) -> float:
    """One judge sheet → single total (0–100 scale via mean of criteria)."""
    norms = normalize_criteria_scores(engine, criteria)
    if not norms:
        return 0.0
    return round(mean(norms.values()), 3)


def aggregate_panel(
    engine: str,
    judge_totals: list[float],
    *,
    drop_extremes: bool = False,
) -> dict[str, Any]:
    """Aggregate multiple judges into panel score."""
    if not judge_totals:
        raise ScoringError("no_judges", "At least one judge score is required")
    totals = [round(float(t), 3) for t in judge_totals]
    used = list(totals)
    dropped: list[float] = []
    if drop_extremes and len(used) >= 5:
        ordered = sorted(used)
        dropped = [ordered[0], ordered[-1]]
        used = ordered[1:-1]
    panel = round(mean(used), 3)
    return {
        "engine": engine,
        "judge_count": len(totals),
        "judge_totals": totals,
        "used_totals": used,
        "dropped_totals": dropped,
        "panel_score": panel,
    }


def best_of_runs(run_scores: list[float]) -> dict[str, Any]:
    if not run_scores:
        raise ScoringError("no_runs", "At least one run score is required")
    scores = [round(float(s), 3) for s in run_scores]
    best = max(scores)
    return {
        "run_scores": scores,
        "best_score": best,
        "best_run_index": scores.index(best) + 1,
    }


def engine_meta(engine: str) -> dict[str, Any]:
    criteria = list(criteria_for_engine(engine))
    return {
        "engine": engine,
        "criteria": criteria,
        "criteria_labels_ru": {c: CRITERIA_LABELS_RU.get(c, c) for c in criteria},
        "aggregation": "mean_of_judge_totals",
        "drop_extremes_if_judges_ge": 5 if engine == "WSWS_DRIVE" else None,
        "best_of_runs": engine == "IWWF_CABLE_TI",
        "placement_overrides_score": engine == "IWWF_BOAT_EIC",
    }
