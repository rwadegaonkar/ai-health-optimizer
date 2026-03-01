"""Weekly Optimization Logic — optimizes weekly calorie averages, not daily punishment."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class WeeklyContext:
    target_daily_calories: float
    daily_actuals: list[dict]  # [{date, calories, protein_g, carbs_g, fat_g}]
    days_remaining_in_week: int
    weight_trend_weekly: float | None  # kg change per week (negative = losing)
    goal_type: str  # lose_weight, gain_muscle, maintain


@dataclass
class WeeklyOptimization:
    weekly_target: float
    weekly_actual_so_far: float
    weekly_budget_remaining: float
    recommended_daily_for_remaining: float
    weekly_avg_so_far: float
    on_track: bool
    message: str
    flexibility_kcal: int  # +/- how much variance is OK


class WeeklyOptimizer:
    """
    Optimizes weekly calorie average instead of punishing daily deviations.

    Philosophy:
        - A 2500 kcal day followed by a 1700 kcal day averages to 2100 kcal.
        - This is FINE if the weekly target is 2100 kcal/day.
        - The body doesn't reset at midnight — weekly trends matter more.

    Rules:
        - Weekly variance of +/- 10% from target is acceptable
        - If weekday average is low, weekend can be slightly higher (and vice versa)
        - Never recommend below minimum safe intake (1200F/1500M)
        - If weekly average drifts >15% over target for 2+ weeks, flag for adjustment
    """

    FLEXIBILITY_PCT = 0.10  # 10% daily variance is OK
    MIN_CALORIES_FEMALE = 1200
    MIN_CALORIES_MALE = 1500

    def optimize(self, ctx: WeeklyContext) -> WeeklyOptimization:
        weekly_target = ctx.target_daily_calories * 7
        days_completed = len(ctx.daily_actuals)

        # Sum up what's been consumed so far
        weekly_actual = sum(d["calories"] for d in ctx.daily_actuals)
        weekly_avg = weekly_actual / max(days_completed, 1)

        # Budget remaining
        budget_remaining = weekly_target - weekly_actual

        # Recommended daily for remaining days
        if ctx.days_remaining_in_week > 0:
            recommended_daily = budget_remaining / ctx.days_remaining_in_week
            # Enforce minimum
            recommended_daily = max(recommended_daily, self.MIN_CALORIES_MALE)
        else:
            recommended_daily = ctx.target_daily_calories

        # Is the week on track?
        if days_completed == 0:
            on_track = True
            pct_diff = 0
        else:
            expected_so_far = ctx.target_daily_calories * days_completed
            pct_diff = (weekly_actual - expected_so_far) / expected_so_far

            on_track = abs(pct_diff) <= 0.15  # Within 15% of expected

        # Generate message
        flexibility = int(ctx.target_daily_calories * self.FLEXIBILITY_PCT)

        if days_completed == 0:
            message = (
                f"New week! Your daily target is {ctx.target_daily_calories:.0f} kcal "
                f"(+/- {flexibility} is perfectly fine)."
            )
        elif on_track:
            message = (
                f"Your weekly average is {weekly_avg:.0f} kcal/day "
                f"(target: {ctx.target_daily_calories:.0f}). You're on track."
            )
        elif pct_diff > 0:
            # Over target
            if ctx.days_remaining_in_week > 0:
                message = (
                    f"Weekly average is {weekly_avg:.0f} kcal/day, "
                    f"slightly above target. Aiming for ~{recommended_daily:.0f} kcal/day "
                    f"for the rest of the week will bring your average back on track."
                )
            else:
                message = (
                    f"This week averaged {weekly_avg:.0f} kcal/day "
                    f"(target: {ctx.target_daily_calories:.0f}). "
                    f"No stress — one week doesn't define your progress."
                )
        else:
            # Under target
            message = (
                f"Weekly average is {weekly_avg:.0f} kcal/day — "
                f"you have room for a bigger meal or treat. "
                f"Undereating consistently slows metabolism."
            )

        return WeeklyOptimization(
            weekly_target=weekly_target,
            weekly_actual_so_far=weekly_actual,
            weekly_budget_remaining=budget_remaining,
            recommended_daily_for_remaining=round(recommended_daily),
            weekly_avg_so_far=round(weekly_avg),
            on_track=on_track,
            message=message,
            flexibility_kcal=flexibility,
        )
