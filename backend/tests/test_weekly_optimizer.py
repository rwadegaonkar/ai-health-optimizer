"""Tests for the Weekly Optimizer."""

from app.engine.policy.weekly_optimizer import WeeklyContext, WeeklyOptimizer


class TestWeeklyOptimizer:
    def setup_method(self):
        self.optimizer = WeeklyOptimizer()

    def test_on_track_week(self):
        """Within 15% of target should be on track."""
        ctx = WeeklyContext(
            target_daily_calories=2100,
            daily_actuals=[
                {"date": "2026-02-23", "calories": 2050, "protein_g": 150, "carbs_g": 200, "fat_g": 70},
                {"date": "2026-02-24", "calories": 2200, "protein_g": 160, "carbs_g": 210, "fat_g": 75},
                {"date": "2026-02-25", "calories": 2000, "protein_g": 140, "carbs_g": 190, "fat_g": 65},
            ],
            days_remaining_in_week=4,
            weight_trend_weekly=-0.3,
            goal_type="lose_weight",
        )
        result = self.optimizer.optimize(ctx)
        assert result.on_track is True
        assert "on track" in result.message.lower()

    def test_over_budget_suggests_adjustment(self):
        """Going over weekly budget should suggest lower remaining days."""
        ctx = WeeklyContext(
            target_daily_calories=2000,
            daily_actuals=[
                {"date": "2026-02-23", "calories": 2800, "protein_g": 150, "carbs_g": 200, "fat_g": 70},
                {"date": "2026-02-24", "calories": 2700, "protein_g": 160, "carbs_g": 210, "fat_g": 75},
                {"date": "2026-02-25", "calories": 2600, "protein_g": 140, "carbs_g": 190, "fat_g": 65},
            ],
            days_remaining_in_week=4,
            weight_trend_weekly=0,
            goal_type="lose_weight",
        )
        result = self.optimizer.optimize(ctx)
        assert result.weekly_actual_so_far > result.weekly_target * 3 / 7
        assert result.recommended_daily_for_remaining < 2000

    def test_under_eating_warning(self):
        """Consistently under target should warn about undereating."""
        ctx = WeeklyContext(
            target_daily_calories=2200,
            daily_actuals=[
                {"date": "2026-02-23", "calories": 1400, "protein_g": 100, "carbs_g": 150, "fat_g": 50},
                {"date": "2026-02-24", "calories": 1300, "protein_g": 90, "carbs_g": 140, "fat_g": 45},
                {"date": "2026-02-25", "calories": 1500, "protein_g": 110, "carbs_g": 160, "fat_g": 55},
            ],
            days_remaining_in_week=4,
            weight_trend_weekly=-0.5,
            goal_type="lose_weight",
        )
        result = self.optimizer.optimize(ctx)
        assert "room" in result.message.lower() or "under" in result.message.lower()

    def test_empty_week(self):
        """Start of week with no data should be on track."""
        ctx = WeeklyContext(
            target_daily_calories=2000,
            daily_actuals=[],
            days_remaining_in_week=7,
            weight_trend_weekly=None,
            goal_type="maintain",
        )
        result = self.optimizer.optimize(ctx)
        assert result.on_track is True
        assert result.weekly_actual_so_far == 0
        assert result.weekly_target == 14000

    def test_recommended_never_below_minimum(self):
        """Recommended daily should never go below safe minimum (1500 for male default)."""
        ctx = WeeklyContext(
            target_daily_calories=2000,
            daily_actuals=[
                {"date": "2026-02-23", "calories": 5000, "protein_g": 200, "carbs_g": 500, "fat_g": 150},
                {"date": "2026-02-24", "calories": 5000, "protein_g": 200, "carbs_g": 500, "fat_g": 150},
                {"date": "2026-02-25", "calories": 5000, "protein_g": 200, "carbs_g": 500, "fat_g": 150},
                {"date": "2026-02-26", "calories": 5000, "protein_g": 200, "carbs_g": 500, "fat_g": 150},
                {"date": "2026-02-27", "calories": 5000, "protein_g": 200, "carbs_g": 500, "fat_g": 150},
            ],
            days_remaining_in_week=2,
            weight_trend_weekly=0,
            goal_type="lose_weight",
        )
        result = self.optimizer.optimize(ctx)
        assert result.recommended_daily_for_remaining >= 1500

    def test_flexibility_is_ten_percent(self):
        """Flexibility should be 10% of target."""
        ctx = WeeklyContext(
            target_daily_calories=2000,
            daily_actuals=[],
            days_remaining_in_week=7,
            weight_trend_weekly=None,
            goal_type="maintain",
        )
        result = self.optimizer.optimize(ctx)
        assert result.flexibility_kcal == 200
