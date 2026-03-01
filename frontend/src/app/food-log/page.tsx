"use client";

import { useEffect, useState, useRef } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api";
import { todayISO } from "@/lib/utils";

export default function FoodLogPage() {
  const [date, setDate] = useState(todayISO());
  const [logs, setLogs] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [mealType, setMealType] = useState("lunch");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchData = async () => {
    try {
      const [logsData, summaryData] = await Promise.all([
        api.getFoodLogs(date),
        api.getDailySummary(date),
      ]);
      setLogs(logsData);
      setSummary(summaryData);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [date]);

  const handleSearch = async () => {
    if (searchQuery.length < 2) return;
    setSearching(true);
    try {
      const results = await api.searchFood(searchQuery);
      setSearchResults(results);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleAddFood = async (food: any) => {
    try {
      await api.createFoodLog({
        food_name: food.food_name,
        brand_name: food.brand_name,
        meal_type: mealType,
        calories: food.calories,
        protein_g: food.protein_g,
        carbs_g: food.carbs_g,
        fat_g: food.fat_g,
        fiber_g: food.fiber_g,
        serving_size: food.serving_size,
        serving_weight_g: food.serving_weight_g,
      });
      setSearchResults([]);
      setSearchQuery("");
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await api.logFoodPhoto(file, mealType);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteFoodLog(id);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Food Log</h1>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        {/* Daily Summary Bar */}
        {summary && (
          <div className="bg-white rounded-xl shadow-sm p-4 mb-6 grid grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(summary.total_calories)}
              </p>
              <p className="text-xs text-gray-500">
                / {summary.target_calories || "—"} kcal
              </p>
            </div>
            <div>
              <p className="text-lg font-semibold text-blue-600">
                {Math.round(summary.total_protein_g)}g
              </p>
              <p className="text-xs text-gray-500">Protein</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-amber-600">
                {Math.round(summary.total_carbs_g)}g
              </p>
              <p className="text-xs text-gray-500">Carbs</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-red-600">
                {Math.round(summary.total_fat_g)}g
              </p>
              <p className="text-xs text-gray-500">Fat</p>
            </div>
          </div>
        )}

        {/* Add Food */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Add Food</h2>

          <div className="flex gap-2 mb-4">
            {["breakfast", "lunch", "dinner", "snack"].map((type) => (
              <button
                key={type}
                onClick={() => setMealType(type)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium capitalize ${
                  mealType === type
                    ? "bg-primary-100 text-primary-700"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search for a food..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              {searching ? "..." : "Search"}
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
            >
              Photo
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handlePhotoUpload}
              className="hidden"
            />
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mt-4 border border-gray-200 rounded-lg divide-y">
              {searchResults.map((food, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleAddFood(food)}
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {food.food_name}
                      {food.brand_name && (
                        <span className="text-gray-400 ml-2">{food.brand_name}</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-500">
                      {Math.round(food.calories)} kcal | P: {Math.round(food.protein_g)}g | C:{" "}
                      {Math.round(food.carbs_g)}g | F: {Math.round(food.fat_g)}g
                    </p>
                  </div>
                  <span className="text-primary-600 text-sm font-medium">+ Add</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Food Log List */}
        <div className="bg-white rounded-xl shadow-sm divide-y">
          {logs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No food logged for this date. Search and add your meals above.
            </div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex items-center justify-between p-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">{log.food_name}</p>
                  <p className="text-xs text-gray-500 capitalize">
                    {log.meal_type} | {Math.round(log.calories)} kcal | P:{" "}
                    {Math.round(log.protein_g)}g C: {Math.round(log.carbs_g)}g F:{" "}
                    {Math.round(log.fat_g)}g
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(log.id)}
                  className="text-xs text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}
