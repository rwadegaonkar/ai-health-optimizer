"""Training Load Model — TRIMP, ACWR, and Training Stress Balance."""

from dataclasses import dataclass


@dataclass
class TrainingLoadInput:
    # Daily training data
    daily_trimp_values: list[float]  # Last 28+ days of TRIMP scores
    # TRIMP = duration(min) * HR_zone_factor
    # Zone factors: Zone 1=1.0, Zone 2=1.5, Zone 3=2.0, Zone 4=3.0, Zone 5=4.0
    hr_zone_minutes: dict[str, int] | None = None  # Today's HR zone time


@dataclass
class TrainingLoadOutput:
    acute_load: float       # 7-day avg (fatigue)
    chronic_load: float     # 28-day avg (fitness)
    acwr: float             # Acute:Chronic Workload Ratio
    tsb: float              # Training Stress Balance = chronic - acute
    zone: str               # "sweet_spot", "caution", "danger", "undertrained"
    recommendation: str
    today_trimp: float


class TrainingLoadModel:
    """
    Monitors training load to prevent overtraining and optimize adaptation.

    Key metrics:
        ACWR (Acute:Chronic Workload Ratio):
            < 0.8  = Undertrained (detraining risk)
            0.8-1.3 = Sweet spot (optimal adaptation)
            1.3-1.5 = Caution (increased injury risk)
            > 1.5  = Danger zone (high injury risk)

        TSB (Training Stress Balance):
            Positive = Fresh (ready to perform)
            Slightly negative (-10 to 0) = Functional overreach (building fitness)
            Very negative (< -30) = Non-functional overreach (risk of overtraining)
    """

    HR_ZONE_FACTORS = {
        "out_of_range": 0.5,
        "fat_burn": 1.0,
        "cardio": 2.0,
        "peak": 3.5,
    }

    def compute(self, input: TrainingLoadInput) -> TrainingLoadOutput:
        values = input.daily_trimp_values

        # Calculate today's TRIMP from HR zones if available
        today_trimp = 0.0
        if input.hr_zone_minutes:
            for zone, minutes in input.hr_zone_minutes.items():
                factor = self.HR_ZONE_FACTORS.get(zone, 1.0)
                today_trimp += minutes * factor
        elif values:
            today_trimp = values[-1]

        # Acute load (7-day rolling average)
        recent_7 = values[-7:] if len(values) >= 7 else values
        acute_load = sum(recent_7) / max(len(recent_7), 1)

        # Chronic load (28-day rolling average)
        recent_28 = values[-28:] if len(values) >= 28 else values
        chronic_load = sum(recent_28) / max(len(recent_28), 1)

        # ACWR
        acwr = acute_load / chronic_load if chronic_load > 0 else 1.0

        # TSB
        tsb = chronic_load - acute_load

        # Zone classification
        if acwr < 0.8:
            zone = "undertrained"
            recommendation = (
                "Your training load has dropped significantly. "
                "Consider gradually increasing volume to maintain fitness."
            )
        elif acwr <= 1.3:
            zone = "sweet_spot"
            recommendation = (
                "Your training load is in the optimal range for adaptation. "
                "Maintain current intensity."
            )
        elif acwr <= 1.5:
            zone = "caution"
            recommendation = (
                "Training load is elevated. Monitor recovery closely. "
                "Consider a lighter session today."
            )
        else:
            zone = "danger"
            recommendation = (
                "Training load is critically high. "
                "Take a rest day or do very light active recovery only."
            )

        return TrainingLoadOutput(
            acute_load=round(acute_load, 1),
            chronic_load=round(chronic_load, 1),
            acwr=round(acwr, 2),
            tsb=round(tsb, 1),
            zone=zone,
            recommendation=recommendation,
            today_trimp=round(today_trimp, 1),
        )
