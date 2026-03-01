"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface User {
  id: string;
  email: string;
  name: string;
  height_cm: number | null;
  weight_kg: number | null;
  age: number | null;
  goal_type: string | null;
  profile_completed: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchUser = useCallback(async () => {
    try {
      const token = api.getToken();
      if (!token) {
        setLoading(false);
        return;
      }
      const profile = await api.getProfile();
      setUser(profile);
    } catch {
      api.setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    const data = await api.login(email, password);
    api.setToken(data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const profile = await api.getProfile();
    setUser(profile);
    router.push(profile.profile_completed ? "/dashboard" : "/onboarding");
  };

  const register = async (email: string, password: string, name: string) => {
    const data = await api.register(email, password, name);
    api.setToken(data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const profile = await api.getProfile();
    setUser(profile);
    router.push(profile.profile_completed ? "/dashboard" : "/onboarding");
  };

  const logout = () => {
    api.setToken(null);
    localStorage.removeItem("refresh_token");
    setUser(null);
    router.push("/auth/login");
  };

  return { user, loading, login, register, logout, refetchUser: fetchUser };
}
