from core.attention_router import route_attention
from core.compute_controller import ComputePath, decide_compute_path
from core.goal_frame import GoalIntent, RiskLevel, infer_goal_frame
from core.noetic_core import StatementType, analyze_noetic


def test_goal_frame_marks_verify_high_risk():
    goal = infer_goal_frame("verify security evidence for this API")
    assert goal.intent == GoalIntent.VERIFY
    assert goal.risk_level == RiskLevel.HIGH
    assert goal.requires_verification


def test_compute_controller_uses_verify_path_for_high_risk():
    decision = decide_compute_path("verify medical claim")
    assert decision.path == ComputePath.VERIFY_PATH
    assert decision.require_truth_gate
    assert decision.require_reflection


def test_attention_router_prefers_validated_relevant_fact():
    route = route_attention(
        "tree prevents erosion",
        [
            {
                "fact_id": "f1",
                "claim": "Tree roots prevent soil erosion",
                "epistemic_state": "Validated",
                "confidence": 0.95,
                "retrieval_score": 0.9,
                "graph_score": 0.8,
            },
            {
                "fact_id": "f2",
                "claim": "Unrelated decorative note",
                "epistemic_state": "Observed",
                "confidence": 0.4,
                "retrieval_score": 0.1,
                "noise": 0.8,
            },
        ],
        top_k=1,
    )
    assert route.selected[0].fact_id == "f1"
    assert route.selected[0].score > 0


def test_noetic_core_marks_predictions_as_predictions_not_facts():
    result = analyze_noetic(
        "what follows from tree roots?",
        [
            {"fact_id": "a", "claim": "Tree roots hold soil", "confidence": 0.9},
            {"fact_id": "b", "claim": "Soil erosion decreases", "confidence": 0.8},
        ],
        [
            {
                "from_fact_id": "a",
                "to_fact_id": "b",
                "relation_type": "causes",
                "confidence": 0.7,
            }
        ],
    )
    assert result.essence
    assert result.causal_chain
    assert result.predictions
    assert result.predictions[0].kind == StatementType.PREDICTION
    assert "prediction_requires_review" in result.predictions[0].uncertainty
