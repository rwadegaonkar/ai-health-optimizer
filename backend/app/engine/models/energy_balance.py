"""Energy Balance Model — TDEE estimation and adaptive metabolic rate tracking."""

from dataclasses import dataclass
from enum import Enum


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityMultiplier(float, Enum):
    SEDENTARY = 1.2
    LIGHTLY_ACTIVE = 1.375
    MODERATELY_ACTIVE = 1.55
    VERY_ACTIVE = 1.725
    EXTREMELY_ACTIVE = 1.9


@dataclass
class EnergyInput:
    weight_kg: float
    height_cm: float
    age: int
    sex: str
    activity_level: str
    goal_type: str  # lose_weight, gain_muscle, maintain, recomposition
    # Wearable data (optional, improves accuracy)
    active_calories: float | None = None
    bmr_calories: float | None = None


@dataclass
class EnergyOutput:
    bmr: float  # Basal Metabolic Rate
    tdee: float  # Total Daily Energy Expenditure
    target_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    deficit_or_surplus: float
    method: str  # "mifflin_st_jeor" or "wearable_adjusted"


class EnergyBalanceModel:
    """
    Calculates BMR, TDEE, and macro targets.

    BMR formula: Mifflin-St Jeor (most accurate for general population)
        Male:   10 * weight(kg) + 6.25 * height(cm) - 5 * age - 161 + 166
        Female: 10 * weight(kg) + 6.25 * height(cm) - 5 * age - 161

    Protein targets:
        Lose weight:    2.0-2.4 g/kg lean body mass (estimated)
        Gain muscle:    1.8-2.2 g/kg body weight
        Maintain:       1.6-2.0 g/kg body weight
        Recomposition:  2.2-2.6 g/kg lean body mass

    Fat minimum: 0.8 g/kg body weight (hormonal health floor)
    Carbs: remainder of calories after protein and fat
    """

    GOAL_ADJUSTMENTS = {
        "lose_weight": -500,       # 500 kcal deficit (~0.45 kg/week loss)
        "gain_muscle": 300,        # 300 kcal surplus (~lean gain)
        "maintain": 0,
        "recomposition": -200,     # Mild deficit with high protein
    }

    PROTEIN_MULTIPLIERS = {
        "lose_weight": 2.2,        # g per kg body weight
        "gain_muscle": 2.0,
        "maintain": 1.8,
        "recomposition": 2.4,
    }

    def compute(self, input: EnergyInput) -> EnergyOutput:
        # BMR via Mifflin-St Jeor
        bmr = 10 * input.weight_kg + 6.25 * input.height_cm - 5 * input.age
        if input.sex == "male":
            bmr += 5
        else:
            bmr -= 161

        # TDEE
        try:
            multiplier = ActivityMultiplier[input.activity_level.upper()].value
        except KeyError:
            multiplier = ActivityMultiplier.MODERATELY_ACTIVE.value

        tdee = bmr * multiplier
        method = "mifflin_st_jeor"

        # If wearable data available, use weighted average
        if input.active_calories is not None and input.bmr_calories is not None:
            wearable_tdee = input.bmr_calories + input.active_calories
            tdee = tdee * 0.4 + wearable_tdee * 0.6  # Trust wearable more
            method = "wearable_adjusted"

        # Target calories
        adjustment = self.GOAL_ADJUSTMENTS.get(input.goal_type, 0)
        target_calories = tdee + adjustment

        # Ensure minimum safe intake
        min_calories = 1200 if input.sex == "female" else 1500
        target_calories = max(target_calories, min_calories)

        # Macros
        protein_per_kg = self.PROTEIN_MULTIPLIERS.get(input.goal_type, 1.8)
        protein_g = input.weight_kg * protein_per_kg
        fat_g = max(input.weight_kg * 0.8, 50)  # Minimum 0.8g/kg or 50g

        protein_cal = protein_g * 4
        fat_cal = fat_g * 9
        remaining_cal = target_calories - protein_cal - fat_cal
        carbs_g = max(remaining_cal / 4, 50)  # Minimum 50g carbs

        return EnergyOutput(
            bmr=round(bmr),
            tdee=round(tdee),
            target_calories=round(target_calories),
            protein_g=round(protein_g),
            carbs_g=round(carbs_g),
            fat_g=round(fat_g),
            deficit_or_surplus=adjustment,
            method=method,
        )
