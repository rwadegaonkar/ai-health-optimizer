"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (checked) return;
    const token = api.getToken();
    if (!token) {
      router.push("/auth/login");
      return;
    }
    api
      .getProfile()
      .then((profile) => {
        router.push(profile.profile_completed ? "/dashboard" : "/onboarding");
      })
      .catch(() => {
        api.setToken(null);
        router.push("/auth/login");
      })
      .finally(() => setChecked(true));
  }, [router, checked]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse text-lg text-gray-500">Loading...</div>
    </div>
  );
}
