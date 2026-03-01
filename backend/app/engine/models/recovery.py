"""Recovery Index Model — computes a 0-100 recovery score from wearable data."""

from dataclasses import dataclass


@dataclass
class RecoveryInput:
    hrv_rmssd: float | None
    hrv_7d_avg: float | None
    rhr_bpm: float | None
    rhr_7d_avg: float | None
    sleep_duration_min: float | None
    sleep_target_min: float = 480  # 8 hours default
    sleep_efficiency: float | None = None
    sleep_deep_pct: float | None = None
    days_since_rest: int = 0
    acwr: float | None = None  # Acute:Chronic Workload Ratio


@dataclass
class RecoveryOutput:
    score: float  # 0-100
    category: str  # "optimal", "good", "moderate", "low", "critical"
    limiting_factors: list[str]
    recommendations: list[str]


class RecoveryModel:
    """
    Weighted composite model for recovery scoring.

    Components and weights:
        HRV trend:       30%  (Z-score relative to personal baseline)
        RHR deviation:    15%  (lower is better, deviation from baseline penalized)
        Sleep quality:    30%  (duration + efficiency + deep sleep %)
        Training load:    15%  (ACWR — sweet spot is 0.8-1.3)
        Rest frequency:   10%  (days since last rest day)
    """

    WEIGHTS = {
        "hrv": 0.30,
        "rhr": 0.15,
        "sleep": 0.30,
        "training_load": 0.15,
        "rest_frequency": 0.10,
    }

    CATEGORIES = [
        (85, "optimal"),
        (70, "good"),
        (50, "moderate"),
        (30, "low"),
        (0, "critical"),
    ]

    def compute(self, input: RecoveryInput) -> RecoveryOutput:
        scores = {}
        limiting_factors = []
        recommendations = []

        # 1. HRV Score (0-100)
        if input.hrv_rmssd is not None and input.hrv_7d_avg is not None and input.hrv_7d_avg > 0:
            hrv_ratio = input.hrv_rmssd / input.hrv_7d_avg
            # 1.0 = at baseline (score 70), >1.1 = above (score 85+), <0.85 = below (score <50)
            scores["hrv"] = min(100, max(0, 70 + (hrv_ratio - 1.0) * 200))
            if hrv_ratio < 0.85:
                limiting_factors.append(f"HRV {int((1 - hrv_ratio) * 100)}% below baseline")
                recommendations.append("Prioritize sleep and reduce training intensity today")
        else:
            scores["hrv"] = 65  # Default if no data

        # 2. RHR Score (0-100)
        if input.rhr_bpm is not None and input.rhr_7d_avg is not None and input.rhr_7d_avg > 0:
            rhr_deviation = input.rhr_bpm - input.rhr_7d_avg
            # Lower is better. Each BPM above baseline reduces score
            scores["rhr"] = min(100, max(0, 80 - rhr_deviation * 10))
            if rhr_deviation > 3:
                limiting_factors.append(f"RHR elevated {rhr_deviation:.0f} BPM above baseline")
                recommendations.append("Your elevated heart rate suggests incomplete recovery")
        else:
            scores["rhr"] = 65

        # 3. Sleep Score (0-100)
        if input.sleep_duration_min is not None:
            duration_ratio = input.sleep_duration_min / input.sleep_target_min
            duration_score = min(100, max(0, duration_ratio * 100))

            efficiency_score = (input.sleep_efficiency or 85)  # Default 85%
            deep_score = min(100, (input.sleep_deep_pct or 15) / 20 * 100)  # 20% deep = 100

            scores["sleep"] = duration_score * 0.5 + efficiency_score * 0.3 + deep_score * 0.2

            if duration_ratio < 0.75:
                limiting_factors.append(
                    f"Only {input.sleep_duration_min / 60:.1f}h sleep "
                    f"(target: {input.sleep_target_min / 60:.0f}h)"
                )
                recommendations.append("Aim to get to bed 30 minutes earlier tonight")
        else:
            scores["sleep"] = 60

        # 4. Training Load Score (ACWR)
        if input.acwr is not None:
            if 0.8 <= input.acwr <= 1.3:
                scores["training_load"] = 85  # Sweet spot
            elif input.acwr < 0.8:
                scores["training_load"] = 70  # Undertrained
            elif input.acwr <= 1.5:
                scores["training_load"] = 50  # Caution zone
                limiting_factors.append(f"Training load ratio elevated ({input.acwr:.2f})")
                recommendations.append("Consider reducing training volume this week")
            else:
                scores["training_load"] = 25  # Danger zone
                limiting_factors.append(f"Training load ratio critical ({input.acwr:.2f})")
                recommendations.append("Significantly reduce training to prevent overtraining")
        else:
            scores["training_load"] = 70

        # 5. Rest Frequency
        if input.days_since_rest <= 2:
            scores["rest_frequency"] = 90
        elif input.days_since_rest <= 4:
            scores["rest_frequency"] = 70
        elif input.days_since_rest <= 6:
            scores["rest_frequency"] = 50
            limiting_factors.append(f"{input.days_since_rest} days without rest")
            recommendations.append("Schedule a rest or active recovery day soon")
        else:
            scores["rest_frequency"] = 25
            limiting_factors.append(f"{input.days_since_rest} consecutive training days")
            recommendations.append("Take a rest day — your body needs recovery time")

        # Weighted total
        total_score = sum(
            scores[key] * self.WEIGHTS[key] for key in self.WEIGHTS if key in scores
        )

        # Determine category
        category = "critical"
        for threshold, cat in self.CATEGORIES:
            if total_score >= threshold:
                category = cat
                break

        return RecoveryOutput(
            score=round(total_score, 1),
            category=category,
            limiting_factors=limiting_factors,
            recommendations=recommendations,
        )
