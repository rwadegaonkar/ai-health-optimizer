"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";
import { todayISO } from "@/lib/utils";

export default function InsightsPage() {
  const [dailyInsight, setDailyInsight] = useState<any>(null);
  const [weeklySummaries, setWeeklySummaries] = useState<any[]>([]);

  useEffect(() => {
    const loadInsights = async () => {
      try {
        const [daily, weekly] = await Promise.all([
          api.getDailyInsight(todayISO()).catch(() => null),
          api.getWeeklySummaries(4).catch(() => []),
        ]);
        setDailyInsight(daily);
        setWeeklySummaries(weekly);
      } catch (err) {
        console.error(err);
      }
    };
    loadInsights();
  }, []);

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">AI Insights</h1>

        {/* Today's Insight */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6 border-l-4 border-primary-500">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Today&apos;s Coaching
          </h2>
          {dailyInsight ? (
            <p className="text-gray-700 whitespace-pre-line leading-relaxed">
              {dailyInsight.content}
            </p>
          ) : (
            <p className="text-gray-500">
              No insight generated for today yet. Insights are generated once you have food and wearable data.
            </p>
          )}
        </div>

        {/* Weekly Summaries */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Weekly Reviews</h2>
          {weeklySummaries.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-6 text-gray-500">
              Weekly reviews will appear here after your first full week of tracking.
            </div>
          ) : (
            weeklySummaries.map((summary) => (
              <div key={summary.id} className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">
                    Week of {summary.week_start}
                  </h3>
                  <div className="flex gap-4 text-sm text-gray-500">
                    <span>Avg: {Math.round(summary.avg_calories || 0)} kcal</span>
                    <span>
                      Sleep: {summary.avg_sleep_min ? (summary.avg_sleep_min / 60).toFixed(1) : "—"}h
                    </span>
                    <span>
                      Recovery: {summary.avg_recovery ? Math.round(summary.avg_recovery) : "—"}/100
                    </span>
                  </div>
                </div>
                {summary.ai_summary && (
                  <p className="text-gray-700 text-sm whitespace-pre-line">
                    {summary.ai_summary}
                  </p>
                )}
                {summary.weight_change != null && (
                  <p className="text-xs text-gray-400 mt-3">
                    Weight change: {summary.weight_change > 0 ? "+" : ""}
                    {summary.weight_change.toFixed(1)} kg
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}
