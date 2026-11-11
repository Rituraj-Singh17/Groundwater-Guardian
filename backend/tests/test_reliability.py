import pandas as pd
import pytest

from app.services.reliability import score_stations


def make_observations():
    return pd.DataFrame({
        "station_id": ["A"] * 5 + ["B"] * 5,
        "observed_at": list(pd.date_range(
            "2025-01-01", periods=5, freq="6h"
        )) * 2,
        "groundwater_level_m": [10, 10, 10, 10, 10] * 2
    })


def test_returns_one_score_per_station():
    result = score_stations(make_observations(), pd.DataFrame())
    assert len(result) == 2
    assert set(result.station_id) == {"A", "B"}


def test_scores_are_between_zero_and_hundred():
    result = score_stations(make_observations(), pd.DataFrame())
    assert result.reliability_score.between(0, 100).all()


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        score_stations(
            make_observations(),
            pd.DataFrame(),
            weights={
                "missing": 0.5,
                "flatline": 0.5,
                "sudden": 0.5,
                "completeness": 0.5
            }
        )


def test_missing_observations_reduce_completeness():
    data = make_observations()
    data.loc[0, "groundwater_level_m"] = None

    result = score_stations(data, pd.DataFrame())
    score = result.set_index("station_id").loc["A", "completeness"]

    assert score < 100


def test_more_missing_faults_reduce_missing_quality():
    data = make_observations()

    alerts = pd.DataFrame({
        "station_id": ["A"],
        "alert_type": ["missing_readings"],
        "evidence": [
            "{'estimated_missing_readings': 2}"
        ]
    })

    result = score_stations(data, alerts)
    scores = result.set_index("station_id")

    assert scores.loc["A", "missing_quality"] < 100
    assert scores.loc["B", "missing_quality"] == 100


def test_invalid_interval_is_rejected():
    with pytest.raises(ValueError):
        score_stations(
            make_observations(),
            pd.DataFrame(),
            expected_interval_hours=0
        )


def test_higher_penalty_reduces_reliability():
    data = pd.DataFrame({
        "station_id": ["A"] * 100,
        "observed_at": pd.date_range(
            "2025-01-01", periods=100, freq="6h"
        ),
        "groundwater_level_m": [10.0] * 100
    })

    alerts = pd.DataFrame({
        "station_id": ["A"],
        "alert_type": ["missing_readings"],
        "evidence": ["{'estimated_missing_readings': 2}"]
    })

    normal = score_stations(data, alerts)
    strict = score_stations(
        data, alerts,
        penalties={
            "missing": 2.0,
            "flatline": 5.0,
            "sudden": 5.0
        }
    )

    normal_row = normal.set_index("station_id").loc["A"]
    strict_row = strict.set_index("station_id").loc["A"]

    assert strict_row["missing_quality"] < normal_row["missing_quality"]
    assert strict_row["reliability_score"] < normal_row["reliability_score"]

from app.services.explainability import explain_station_scores


def test_explainability_adds_required_fields():
    scores = score_stations(make_observations(), pd.DataFrame())
    result = explain_station_scores(scores)

    required = [
        "primary_concern",
        "explanation",
        "recommended_action",
        "investigation_priority"
    ]

    for column in required:
        assert column in result.columns
        assert result[column].notna().all()


def test_weighted_contributions_match_final_score():
    scores = score_stations(make_observations(), pd.DataFrame())
    result = explain_station_scores(scores)

    contribution_columns = [
        "missing_quality_contribution",
        "flatline_quality_contribution",
        "sudden_quality_contribution",
        "completeness_contribution"
    ]

    contribution_sum = result[contribution_columns].sum(axis=1)

    assert (
        (contribution_sum - result["reliability_score"]).abs() < 0.05
    ).all()


def test_explainability_rejects_missing_columns():
    with pytest.raises(ValueError):
        explain_station_scores(pd.DataFrame({"station_id": ["A"]}))
