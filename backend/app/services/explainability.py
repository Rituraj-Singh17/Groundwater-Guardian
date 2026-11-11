import pandas as pd

from app.services.reliability import DEFAULT_WEIGHTS


COMPONENTS = {
    "missing_quality": {
        "label": "Missing observations",
        "weight": "missing"
    },
    "flatline_quality": {
        "label": "Repeated or flatline readings",
        "weight": "flatline"
    },
    "sudden_quality": {
        "label": "Sudden groundwater-level changes",
        "weight": "sudden"
    },
    "completeness": {
        "label": "Observation completeness",
        "weight": "completeness"
    }
}


def explain_station_scores(scores):
    required = {
        "station_id",
        "missing_quality",
        "flatline_quality",
        "sudden_quality",
        "completeness",
        "reliability_score",
        "reliability_category",
        "estimated_missing_observations",
        "flatline_repeated_alerts",
        "sudden_change_alerts",
        "missing_rate_per_1000"
    }

    if not required.issubset(scores.columns):
        raise ValueError(
            f"Missing columns: {sorted(required - set(scores.columns))}"
        )

    result = scores.copy()

    for component, details in COMPONENTS.items():
        weight = DEFAULT_WEIGHTS[details["weight"]]
        result[f"{component}_contribution"] = (
            result[component] * weight
        ).round(2)

    explanations = []
    concerns = []
    actions = []
    priorities = []

    for _, row in result.iterrows():
        component_scores = {
            "Missing observations": row["missing_quality"],
            "Repeated or flatline readings": row["flatline_quality"],
            "Sudden groundwater-level changes": row["sudden_quality"],
            "Observation completeness": row["completeness"]
        }

        primary = min(component_scores, key=component_scores.get)
        factors = []

        if row["missing_quality"] < 60:
            factors.append(
                f"Missing observations are a concern: "
                f"{row['estimated_missing_observations']:.0f} "
                f"estimated missing readings "
                f"({row['missing_rate_per_1000']:.2f} per 1,000 expected readings)."
            )

        if row["flatline_quality"] < 60:
            factors.append(
                f"Repeated/flatline behaviour needs review: "
                f"{int(row['flatline_repeated_alerts'])} alerts."
            )

        if row["sudden_quality"] < 60:
            factors.append(
                f"Unusual groundwater-level changes need review: "
                f"{int(row['sudden_change_alerts'])} alerts."
            )

        if row["completeness"] < 80:
            factors.append(
                f"Estimated observation completeness is "
                f"{row['completeness']:.2f}%."
            )

        if not factors:
            factors.append(
                "No component crossed the configured concern thresholds."
            )

        if primary == "Missing observations":
            action = (
                "Review observation gaps and verify the station's "
                "expected reporting schedule."
            )
        elif primary == "Repeated or flatline readings":
            action = (
                "Inspect the repeated-reading periods and compare them "
                "with the station's historical observations."
            )
        elif primary == "Sudden groundwater-level changes":
            action = (
                "Review the unusual changes against nearby observations "
                "and available field records."
            )
        else:
            action = (
                "Verify the expected observation schedule and investigate "
                "the periods with incomplete data."
            )

        category = row["reliability_category"]

        if category in ("Very Low", "Low"):
            priority = "High"
        elif category == "Moderate":
            priority = "Medium"
        else:
            priority = "Routine"

        concerns.append(primary)
        explanations.append(" ".join(factors))
        actions.append(action)
        priorities.append(priority)

    result["primary_concern"] = concerns
    result["explanation"] = explanations
    result["recommended_action"] = actions
    result["investigation_priority"] = priorities

    return result
