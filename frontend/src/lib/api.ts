const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("access_token", token);
    } else {
      localStorage.removeItem("access_token");
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      (headers as Record<string, string>)["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.setToken(null);
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || "Request failed");
    }

    if (response.status === 204) return {} as T;
    return response.json();
  }

  // Auth
  async register(email: string, password: string, name: string) {
    return this.request<{ access_token: string; refresh_token: string }>(
      "/api/v1/auth/register",
      { method: "POST", body: JSON.stringify({ email, password, name }) }
    );
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string }>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    );
  }

  // User
  async getProfile() {
    return this.request<any>("/api/v1/users/me");
  }

  async updateProfile(data: any) {
    return this.request<any>("/api/v1/users/me", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  // Food
  async searchFood(query: string) {
    return this.request<any[]>(`/api/v1/food/search?q=${encodeURIComponent(query)}`);
  }

  async createFoodLog(data: any) {
    return this.request<any>("/api/v1/food/log", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getFoodLogs(date: string) {
    return this.request<any[]>(`/api/v1/food/logs?target_date=${date}`);
  }

  async getDailySummary(date: string) {
    return this.request<any>(`/api/v1/food/summary?target_date=${date}`);
  }

  async logFoodPhoto(file: File, mealType: string) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<any>(
      `/api/v1/food/log-photo?meal_type=${mealType}`,
      { method: "POST", body: formData }
    );
  }

  async deleteFoodLog(id: string) {
    return this.request<void>(`/api/v1/food/logs/${id}`, { method: "DELETE" });
  }

  // Dashboard
  async getDashboard() {
    return this.request<any>("/api/v1/dashboard");
  }

  // Targets
  async setMacroTargets(data: any) {
    return this.request<any>("/api/v1/insights/targets", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getCurrentTargets() {
    return this.request<any>("/api/v1/insights/targets/current");
  }

  // Wearables
  async getWearableConnections() {
    return this.request<any[]>("/api/v1/wearables/connections");
  }

  async getWearableMetrics(startDate: string, endDate: string) {
    return this.request<any[]>(
      `/api/v1/wearables/metrics?start_date=${startDate}&end_date=${endDate}`
    );
  }

  async connectFitbit() {
    return this.request<{ authorization_url: string }>(
      "/api/v1/integrations/fitbit/connect"
    );
  }

  async syncFitbit() {
    return this.request<any>("/api/v1/integrations/fitbit/sync", {
      method: "POST",
    });
  }

  // Insights
  async getDailyInsight(date: string) {
    return this.request<any>(`/api/v1/insights/daily?target_date=${date}`);
  }

  async getWeeklySummaries(weeks: number = 4) {
    return this.request<any[]>(`/api/v1/insights/weekly?weeks=${weeks}`);
  }
}

export const api = new ApiClient();
