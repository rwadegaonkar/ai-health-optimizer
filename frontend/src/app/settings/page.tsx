"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";
import { todayISO } from "@/lib/utils";

export default function SettingsPage() {
  const [profile, setProfile] = useState<any>(null);
  const [targets, setTargets] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [p, t] = await Promise.all([
          api.getProfile(),
          api.getCurrentTargets().catch(() => null),
        ]);
        setProfile(p);
        setTargets(t);
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, []);

  const handleProfileSave = async () => {
    setSaving(true);
    setMessage("");
    try {
      await api.updateProfile({
        height_cm: profile.height_cm,
        weight_kg: profile.weight_kg,
        age: profile.age,
        sex: profile.sex,
        activity_level: profile.activity_level,
        goal_type: profile.goal_type,
        dietary_preferences: profile.dietary_preferences,
      });
      setMessage("Profile saved!");
    } catch (err) {
      setMessage("Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const handleTargetsSave = async () => {
    if (!targets) return;
    setSaving(true);
    setMessage("");
    try {
      await api.setMacroTargets({
        calories: targets.calories,
        protein_g: targets.protein_g,
        carbs_g: targets.carbs_g,
        fat_g: targets.fat_g,
        effective_from: todayISO(),
      });
      setMessage("Targets saved!");
    } catch (err) {
      setMessage("Failed to save targets");
    } finally {
      setSaving(false);
    }
  };

  if (!profile) {
    return (
      <AppLayout>
        <div className="text-gray-500">Loading...</div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

        {message && (
          <div className="bg-primary-50 text-primary-700 p-3 rounded-lg mb-4 text-sm">
            {message}
          </div>
        )}

        {/* Profile */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Profile</h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Height (cm)" value={profile.height_cm || ""} onChange={(v) => setProfile({ ...profile, height_cm: parseFloat(v) || null })} type="number" />
            <Field label="Weight (kg)" value={profile.weight_kg || ""} onChange={(v) => setProfile({ ...profile, weight_kg: parseFloat(v) || null })} type="number" />
            <Field label="Age" value={profile.age || ""} onChange={(v) => setProfile({ ...profile, age: parseInt(v) || null })} type="number" />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sex</label>
              <select value={profile.sex || ""} onChange={(e) => setProfile({ ...profile, sex: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="">Select</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Activity Level</label>
              <select value={profile.activity_level || ""} onChange={(e) => setProfile({ ...profile, activity_level: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="sedentary">Sedentary</option>
                <option value="lightly_active">Lightly Active</option>
                <option value="moderately_active">Moderately Active</option>
                <option value="very_active">Very Active</option>
                <option value="extremely_active">Extremely Active</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Goal</label>
              <select value={profile.goal_type || ""} onChange={(e) => setProfile({ ...profile, goal_type: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="lose_weight">Lose Weight</option>
                <option value="gain_muscle">Gain Muscle</option>
                <option value="maintain">Maintain</option>
                <option value="recomposition">Recomposition</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <Field label="Dietary Preferences" value={profile.dietary_preferences || ""} onChange={(v) => setProfile({ ...profile, dietary_preferences: v })} />
          </div>
          <button onClick={handleProfileSave} disabled={saving} className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
            Save Profile
          </button>
        </div>

        {/* Macro Targets */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Daily Macro Targets</h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Calories (kcal)" value={targets?.calories || ""} onChange={(v) => setTargets({ ...targets, calories: parseFloat(v) || 0 })} type="number" />
            <Field label="Protein (g)" value={targets?.protein_g || ""} onChange={(v) => setTargets({ ...targets, protein_g: parseFloat(v) || 0 })} type="number" />
            <Field label="Carbs (g)" value={targets?.carbs_g || ""} onChange={(v) => setTargets({ ...targets, carbs_g: parseFloat(v) || 0 })} type="number" />
            <Field label="Fat (g)" value={targets?.fat_g || ""} onChange={(v) => setTargets({ ...targets, fat_g: parseFloat(v) || 0 })} type="number" />
          </div>
          <button onClick={handleTargetsSave} disabled={saving} className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
            Save Targets
          </button>
        </div>
      </div>
    </AppLayout>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: any; onChange: (v: string) => void; type?: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
    </div>
  );
}
