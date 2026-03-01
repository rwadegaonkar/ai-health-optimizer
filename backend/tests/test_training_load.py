"""Tests for the Training Load Model."""

from app.engine.models.training_load import TrainingLoadInput, TrainingLoadModel


class TestTrainingLoadModel:
    def setup_method(self):
        self.model = TrainingLoadModel()

    def test_sweet_spot_acwr(self):
        """ACWR between 0.8 and 1.3 should be sweet spot."""
        # Consistent load: 100 TRIMP every day for 28 days
        values = [100.0] * 28
        input = TrainingLoadInput(daily_trimp_values=values)
        result = self.model.compute(input)
        assert 0.8 <= result.acwr <= 1.3
        assert result.zone == "sweet_spot"

    def test_danger_zone_spike(self):
        """Sudden spike in training load should trigger danger zone."""
        # Low load for 21 days, then very high for 7 days
        values = [50.0] * 21 + [200.0] * 7
        input = TrainingLoadInput(daily_trimp_values=values)
        result = self.model.compute(input)
        assert result.acwr > 1.3
        assert result.zone in ("caution", "danger")

    def test_undertrained(self):
        """Sudden drop in training should flag undertrained."""
        # High load for 21 days, then very low for 7 days
        values = [150.0] * 21 + [30.0] * 7
        input = TrainingLoadInput(daily_trimp_values=values)
        result = self.model.compute(input)
        assert result.acwr < 0.8
        assert result.zone == "undertrained"

    def test_tsb_positive_means_fresh(self):
        """When chronic > acute, TSB should be positive (fresh)."""
        values = [100.0] * 21 + [50.0] * 7
        input = TrainingLoadInput(daily_trimp_values=values)
        result = self.model.compute(input)
        assert result.tsb > 0

    def test_tsb_negative_means_fatigued(self):
        """When acute > chronic, TSB should be negative (fatigued)."""
        values = [50.0] * 21 + [150.0] * 7
        input = TrainingLoadInput(daily_trimp_values=values)
        result = self.model.compute(input)
        assert result.tsb < 0

    def test_hr_zone_trimp_calculation(self):
        """HR zone minutes should be converted to TRIMP correctly."""
        input = TrainingLoadInput(
            daily_trimp_values=[100.0] * 28,
            hr_zone_minutes={
                "fat_burn": 30,   # 30 * 1.0 = 30
                "cardio": 20,     # 20 * 2.0 = 40
                "peak": 5,        # 5 * 3.5 = 17.5
            },
        )
        result = self.model.compute(input)
        assert result.today_trimp == 87.5  # 30 + 40 + 17.5

    def test_short_history(self):
        """Model should handle less than 28 days of data."""
        values = [100.0] * 5
        input = TrainingLoadInput(daily_trimp_values=values)
        result = self.model.compute(input)
        assert result.acute_load > 0
        assert result.chronic_load > 0

    def test_empty_history(self):
        """Model should handle empty data without crashing."""
        input = TrainingLoadInput(daily_trimp_values=[])
        result = self.model.compute(input)
        assert result.acute_load == 0
        assert result.chronic_load == 0

    def test_recommendation_not_empty(self):
        """Every result should include a recommendation."""
        values = [100.0] * 28
        input = TrainingLoadInput(daily_trimp_values=values)
        result = self.model.compute(input)
        assert len(result.recommendation) > 0
