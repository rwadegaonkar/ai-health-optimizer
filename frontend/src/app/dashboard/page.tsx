"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";
import { formatCalories } from "@/lib/utils";

interface DashboardData {
  today_summary: {
    total_calories: number;
    total_protein_g: number;
    total_carbs_g: number;
    total_fat_g: number;
    meal_count: number;
    target_calories: number | null;
    target_protein_g: number | null;
    target_carbs_g: number | null;
    target_fat_g: number | null;
  } | null;
  latest_metrics: {
    sleep_duration_min: number | null;
    hrv_rmssd: number | null;
    rhr_bpm: number | null;
    steps: number | null;
    recovery_score: number | null;
  } | null;
  latest_insight: {
    content: string;
    date: string;
  } | null;
  weekly_calories: { date: string; calories: number }[];
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

        {loading ? (
          <div className="text-gray-500">Loading dashboard...</div>
        ) : !data ? (
          <div className="text-gray-500">Failed to load dashboard data.</div>
        ) : (
          <div className="space-y-6">
            {/* Calorie Summary Card */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                label="Calories"
                value={formatCalories(data.today_summary?.total_calories || 0)}
                target={data.today_summary?.target_calories ? formatCalories(data.today_summary.target_calories) : undefined}
                unit="kcal"
              />
              <StatCard
                label="Protein"
                value={Math.round(data.today_summary?.total_protein_g || 0).toString()}
                target={data.today_summary?.target_protein_g?.toString()}
                unit="g"
              />
              <StatCard
                label="Carbs"
                value={Math.round(data.today_summary?.total_carbs_g || 0).toString()}
                target={data.today_summary?.target_carbs_g?.toString()}
                unit="g"
              />
              <StatCard
                label="Fat"
                value={Math.round(data.today_summary?.total_fat_g || 0).toString()}
                target={data.today_summary?.target_fat_g?.toString()}
                unit="g"
              />
            </div>

            {/* Recovery Metrics */}
            {data.latest_metrics && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard
                  label="Recovery"
                  value={data.latest_metrics.recovery_score?.toString() || "—"}
                  unit="/100"
                />
                <StatCard
                  label="HRV"
                  value={data.latest_metrics.hrv_rmssd?.toFixed(0) || "—"}
                  unit="ms"
                />
                <StatCard
                  label="Resting HR"
                  value={data.latest_metrics.rhr_bpm?.toString() || "—"}
                  unit="bpm"
                />
                <StatCard
                  label="Sleep"
                  value={
                    data.latest_metrics.sleep_duration_min
                      ? (data.latest_metrics.sleep_duration_min / 60).toFixed(1)
                      : "—"
                  }
                  unit="hrs"
                />
              </div>
            )}

            {/* Weekly Calorie Trend */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Weekly Calorie Trend
              </h2>
              <div className="flex items-end gap-2 h-40">
                {data.weekly_calories.map((day) => {
                  const maxCal = Math.max(
                    ...data.weekly_calories.map((d) => d.calories),
                    1
                  );
                  const height = (day.calories / maxCal) * 100;
                  return (
                    <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
                      <span className="text-xs text-gray-500">
                        {day.calories > 0 ? Math.round(day.calories) : ""}
                      </span>
                      <div
                        className="w-full bg-primary-400 rounded-t-md transition-all"
                        style={{ height: `${Math.max(height, 2)}%` }}
                      />
                      <span className="text-xs text-gray-400">
                        {new Date(day.date).toLocaleDateString("en", { weekday: "short" })}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* AI Insight */}
            {data.latest_insight && (
              <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-primary-500">
                <h2 className="text-lg font-semibold text-gray-900 mb-2">
                  AI Coaching Insight
                </h2>
                <p className="text-gray-700 whitespace-pre-line">
                  {data.latest_insight.content}
                </p>
                <p className="text-xs text-gray-400 mt-3">{data.latest_insight.date}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}

function StatCard({
  label,
  value,
  target,
  unit,
}: {
  label: string;
  value: string;
  target?: string;
  unit?: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">
        {value}
        <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>
      </p>
      {target && (
        <p className="text-xs text-gray-400 mt-1">
          Target: {target} {unit}
        </p>
      )}
    </div>
  );
}
