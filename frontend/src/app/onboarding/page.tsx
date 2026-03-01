"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

const ACTIVITY_LEVELS = [
  { value: "sedentary", label: "Sedentary" },
  { value: "lightly_active", label: "Lightly Active" },
  { value: "moderately_active", label: "Moderately Active" },
  { value: "very_active", label: "Very Active" },
  { value: "extremely_active", label: "Extremely Active" },
];

const GOAL_TYPES = [
  { value: "lose_weight", label: "Lose Weight" },
  { value: "gain_muscle", label: "Gain Muscle" },
  { value: "maintain", label: "Maintain Weight" },
  { value: "recomposition", label: "Body Recomposition" },
];

export default function OnboardingPage() {
  const { user, loading, refetchUser } = useAuth();
  const router = useRouter();

  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState("");
  const [activityLevel, setActivityLevel] = useState("moderately_active");
  const [goalType, setGoalType] = useState("maintain");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
    if (!loading && user?.profile_completed) {
      router.push("/dashboard");
    }
  }, [loading, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!heightCm || !weightKg || !age || !sex) {
      setError("Please fill in all required fields.");
      return;
    }

    setSubmitting(true);
    try {
      await api.updateProfile({
        height_cm: parseFloat(heightCm),
        weight_kg: parseFloat(weightKg),
        age: parseInt(age, 10),
        sex,
        activity_level: activityLevel,
        goal_type: goalType,
      });
      await refetchUser();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to save profile. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse text-lg text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!user || user.profile_completed) return null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-lg w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to AI Health Optimizer</h1>
          <p className="mt-2 text-gray-600">
            Tell us a bit about yourself so we can personalize your experience.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-5 bg-white p-8 rounded-xl shadow-sm"
        >
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{error}</div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="height" className="block text-sm font-medium text-gray-700">
                Height (cm) *
              </label>
              <input
                id="height"
                type="number"
                required
                min="100"
                max="250"
                step="0.1"
                value={heightCm}
                onChange={(e) => setHeightCm(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                placeholder="175"
              />
            </div>

            <div>
              <label htmlFor="weight" className="block text-sm font-medium text-gray-700">
                Weight (kg) *
              </label>
              <input
                id="weight"
                type="number"
                required
                min="30"
                max="300"
                step="0.1"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                placeholder="70"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="age" className="block text-sm font-medium text-gray-700">
                Age *
              </label>
              <input
                id="age"
                type="number"
                required
                min="13"
                max="120"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                placeholder="30"
              />
            </div>

            <div>
              <label htmlFor="sex" className="block text-sm font-medium text-gray-700">
                Sex *
              </label>
              <select
                id="sex"
                required
                value={sex}
                onChange={(e) => setSex(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="activity" className="block text-sm font-medium text-gray-700">
              Activity Level
            </label>
            <select
              id="activity"
              value={activityLevel}
              onChange={(e) => setActivityLevel(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
            >
              {ACTIVITY_LEVELS.map((al) => (
                <option key={al.value} value={al.value}>
                  {al.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="goal" className="block text-sm font-medium text-gray-700">
              Goal
            </label>
            <select
              id="goal"
              value={goalType}
              onChange={(e) => setGoalType(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
            >
              {GOAL_TYPES.map((g) => (
                <option key={g.value} value={g.value}>
                  {g.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {submitting ? "Saving..." : "Get Started"}
          </button>
        </form>
      </div>
    </div>
  );
}
