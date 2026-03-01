"""Tests for the Recovery Index Model."""

from app.engine.models.recovery import RecoveryInput, RecoveryModel


class TestRecoveryModel:
    def setup_method(self):
        self.model = RecoveryModel()

    def test_optimal_recovery(self):
        """All metrics at or above baseline should yield high score."""
        input = RecoveryInput(
            hrv_rmssd=55.0,
            hrv_7d_avg=50.0,
            rhr_bpm=58,
            rhr_7d_avg=60,
            sleep_duration_min=480,
            sleep_efficiency=92,
            sleep_deep_pct=22,
            days_since_rest=1,
            acwr=1.0,
        )
        result = self.model.compute(input)
        assert result.score >= 75
        assert result.category in ("optimal", "good")
        assert len(result.limiting_factors) == 0

    def test_low_recovery_poor_sleep(self):
        """Short sleep should lower score and flag as limiting factor."""
        input = RecoveryInput(
            hrv_rmssd=50.0,
            hrv_7d_avg=50.0,
            rhr_bpm=60,
            rhr_7d_avg=60,
            sleep_duration_min=300,  # 5 hours
            sleep_target_min=480,
            sleep_efficiency=75,
            days_since_rest=1,
            acwr=1.0,
        )
        result = self.model.compute(input)
        assert result.score < 80
        assert any("sleep" in f.lower() for f in result.limiting_factors)

    def test_low_recovery_elevated_rhr(self):
        """RHR elevated above baseline should reduce score."""
        input = RecoveryInput(
            hrv_rmssd=50.0,
            hrv_7d_avg=50.0,
            rhr_bpm=68,  # 8 above baseline
            rhr_7d_avg=60,
            sleep_duration_min=480,
            days_since_rest=1,
            acwr=1.0,
        )
        result = self.model.compute(input)
        assert any("RHR" in f for f in result.limiting_factors)

    def test_low_recovery_depressed_hrv(self):
        """HRV well below baseline should flag concern."""
        input = RecoveryInput(
            hrv_rmssd=35.0,  # 30% below baseline
            hrv_7d_avg=50.0,
            rhr_bpm=60,
            rhr_7d_avg=60,
            sleep_duration_min=480,
            days_since_rest=1,
            acwr=1.0,
        )
        result = self.model.compute(input)
        assert any("HRV" in f for f in result.limiting_factors)

    def test_danger_zone_acwr(self):
        """ACWR above 1.5 should flag as danger."""
        input = RecoveryInput(
            hrv_rmssd=50.0,
            hrv_7d_avg=50.0,
            rhr_bpm=60,
            rhr_7d_avg=60,
            sleep_duration_min=480,
            days_since_rest=1,
            acwr=1.8,
        )
        result = self.model.compute(input)
        assert any("critical" in f.lower() or "Training load" in f for f in result.limiting_factors)

    def test_too_many_days_without_rest(self):
        """7+ days without rest should flag."""
        input = RecoveryInput(
            hrv_rmssd=50.0,
            hrv_7d_avg=50.0,
            rhr_bpm=60,
            rhr_7d_avg=60,
            sleep_duration_min=480,
            days_since_rest=8,
            acwr=1.0,
        )
        result = self.model.compute(input)
        assert any("rest" in f.lower() or "consecutive" in f.lower() for f in result.limiting_factors)
        assert len(result.recommendations) > 0

    def test_missing_data_defaults_gracefully(self):
        """Model should handle None values without crashing."""
        input = RecoveryInput(
            hrv_rmssd=None,
            hrv_7d_avg=None,
            rhr_bpm=None,
            rhr_7d_avg=None,
            sleep_duration_min=None,
            days_since_rest=0,
            acwr=None,
        )
        result = self.model.compute(input)
        assert 0 <= result.score <= 100
        assert result.category in ("optimal", "good", "moderate", "low", "critical")

    def test_score_always_in_range(self):
        """Score must always be between 0 and 100."""
        # Extreme positive
        input = RecoveryInput(
            hrv_rmssd=100.0,
            hrv_7d_avg=50.0,
            rhr_bpm=40,
            rhr_7d_avg=60,
            sleep_duration_min=600,
            sleep_efficiency=99,
            sleep_deep_pct=30,
            days_since_rest=0,
            acwr=1.0,
        )
        result = self.model.compute(input)
        assert 0 <= result.score <= 100

        # Extreme negative
        input2 = RecoveryInput(
            hrv_rmssd=10.0,
            hrv_7d_avg=50.0,
            rhr_bpm=90,
            rhr_7d_avg=60,
            sleep_duration_min=120,
            sleep_efficiency=40,
            days_since_rest=14,
            acwr=2.5,
        )
        result2 = self.model.compute(input2)
        assert 0 <= result2.score <= 100
