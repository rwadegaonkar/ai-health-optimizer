"""Tests for the Energy Balance Model."""

from app.engine.models.energy_balance import EnergyBalanceModel, EnergyInput


class TestEnergyBalanceModel:
    def setup_method(self):
        self.model = EnergyBalanceModel()

    def test_male_maintenance_calories(self):
        """Standard male maintenance should produce reasonable TDEE."""
        input = EnergyInput(
            weight_kg=80,
            height_cm=175,
            age=30,
            sex="male",
            activity_level="moderately_active",
            goal_type="maintain",
        )
        result = self.model.compute(input)
        assert 2200 < result.tdee < 3200
        assert result.target_calories == result.tdee  # No deficit for maintain
        assert result.deficit_or_surplus == 0

    def test_female_weight_loss(self):
        """Female weight loss should have a 500 kcal deficit."""
        input = EnergyInput(
            weight_kg=65,
            height_cm=165,
            age=28,
            sex="female",
            activity_level="lightly_active",
            goal_type="lose_weight",
        )
        result = self.model.compute(input)
        assert result.target_calories == result.tdee - 500
        assert result.deficit_or_surplus == -500

    def test_muscle_gain_surplus(self):
        """Muscle gain should have a 300 kcal surplus."""
        input = EnergyInput(
            weight_kg=75,
            height_cm=178,
            age=25,
            sex="male",
            activity_level="very_active",
            goal_type="gain_muscle",
        )
        result = self.model.compute(input)
        assert result.target_calories == result.tdee + 300
        assert result.deficit_or_surplus == 300

    def test_minimum_calorie_floor_female(self):
        """Should never recommend below 1200 kcal for females."""
        input = EnergyInput(
            weight_kg=45,
            height_cm=150,
            age=50,
            sex="female",
            activity_level="sedentary",
            goal_type="lose_weight",
        )
        result = self.model.compute(input)
        assert result.target_calories >= 1200

    def test_minimum_calorie_floor_male(self):
        """Should never recommend below 1500 kcal for males."""
        input = EnergyInput(
            weight_kg=55,
            height_cm=160,
            age=50,
            sex="male",
            activity_level="sedentary",
            goal_type="lose_weight",
        )
        result = self.model.compute(input)
        assert result.target_calories >= 1500

    def test_protein_target_weight_loss(self):
        """Weight loss should have higher protein (2.2g/kg)."""
        input = EnergyInput(
            weight_kg=80,
            height_cm=175,
            age=30,
            sex="male",
            activity_level="moderately_active",
            goal_type="lose_weight",
        )
        result = self.model.compute(input)
        assert result.protein_g == round(80 * 2.2)

    def test_fat_minimum(self):
        """Fat should be at least 0.8g/kg or 50g."""
        input = EnergyInput(
            weight_kg=50,
            height_cm=160,
            age=25,
            sex="female",
            activity_level="moderately_active",
            goal_type="maintain",
        )
        result = self.model.compute(input)
        assert result.fat_g >= 50

    def test_wearable_adjusted_method(self):
        """When wearable data is provided, method should be wearable_adjusted."""
        input = EnergyInput(
            weight_kg=80,
            height_cm=175,
            age=30,
            sex="male",
            activity_level="moderately_active",
            goal_type="maintain",
            active_calories=800,
            bmr_calories=1800,
        )
        result = self.model.compute(input)
        assert result.method == "wearable_adjusted"

    def test_no_wearable_uses_formula(self):
        """Without wearable data, method should be mifflin_st_jeor."""
        input = EnergyInput(
            weight_kg=80,
            height_cm=175,
            age=30,
            sex="male",
            activity_level="moderately_active",
            goal_type="maintain",
        )
        result = self.model.compute(input)
        assert result.method == "mifflin_st_jeor"

    def test_macros_sum_to_target(self):
        """Protein + carbs + fat calories should roughly equal target."""
        input = EnergyInput(
            weight_kg=80,
            height_cm=175,
            age=30,
            sex="male",
            activity_level="moderately_active",
            goal_type="maintain",
        )
        result = self.model.compute(input)
        macro_calories = result.protein_g * 4 + result.carbs_g * 4 + result.fat_g * 9
        # Should be within 50 kcal of target (rounding)
        assert abs(macro_calories - result.target_calories) < 50
