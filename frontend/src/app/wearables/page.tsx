"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";

export default function WearablesPage() {
  const [connections, setConnections] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [conns, metricsData] = await Promise.all([
        api.getWearableConnections(),
        api.getWearableMetrics(
          new Date(Date.now() - 7 * 86400000).toISOString().split("T")[0],
          new Date().toISOString().split("T")[0]
        ),
      ]);
      setConnections(conns);
      setMetrics(metricsData);
    } catch (err) {
      console.error(err);
    }
  };

  const handleConnectFitbit = async () => {
    try {
      const { authorization_url } = await api.connectFitbit();
      window.location.href = authorization_url;
    } catch (err) {
      console.error(err);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.syncFitbit();
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const fitbitConnected = connections.some(
    (c) => c.provider === "fitbit" && c.is_active
  );

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Wearables</h1>

        {/* Connection Status */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Connected Devices</h2>

          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 font-bold">
                FB
              </div>
              <div>
                <p className="font-medium text-gray-900">Fitbit</p>
                <p className="text-xs text-gray-500">
                  {fitbitConnected ? "Connected" : "Not connected"}
                </p>
              </div>
            </div>
            {fitbitConnected ? (
              <button
                onClick={handleSync}
                disabled={syncing}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
              >
                {syncing ? "Syncing..." : "Sync Now"}
              </button>
            ) : (
              <button
                onClick={handleConnectFitbit}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
              >
                Connect
              </button>
            )}
          </div>

          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg mt-3 opacity-50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600 font-bold">
                AW
              </div>
              <div>
                <p className="font-medium text-gray-900">Apple Watch</p>
                <p className="text-xs text-gray-500">Coming soon</p>
              </div>
            </div>
          </div>
        </div>

        {/* Metrics Table */}
        {metrics.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Metrics (7 days)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2 pr-4">Date</th>
                    <th className="pb-2 pr-4">Sleep</th>
                    <th className="pb-2 pr-4">HRV</th>
                    <th className="pb-2 pr-4">RHR</th>
                    <th className="pb-2 pr-4">Steps</th>
                    <th className="pb-2">Recovery</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((m) => (
                    <tr key={m.date} className="border-b last:border-0">
                      <td className="py-2 pr-4 text-gray-600">{m.date}</td>
                      <td className="py-2 pr-4">
                        {m.sleep_duration_min
                          ? `${(m.sleep_duration_min / 60).toFixed(1)}h`
                          : "—"}
                      </td>
                      <td className="py-2 pr-4">
                        {m.hrv_rmssd ? `${m.hrv_rmssd.toFixed(0)} ms` : "—"}
                      </td>
                      <td className="py-2 pr-4">
                        {m.rhr_bpm ? `${m.rhr_bpm} bpm` : "—"}
                      </td>
                      <td className="py-2 pr-4">
                        {m.steps?.toLocaleString() || "—"}
                      </td>
                      <td className="py-2">
                        {m.recovery_score ? (
                          <span
                            className={`font-medium ${
                              m.recovery_score >= 70
                                ? "text-green-600"
                                : m.recovery_score >= 50
                                ? "text-amber-600"
                                : "text-red-600"
                            }`}
                          >
                            {m.recovery_score}/100
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
