const API_BASE_URL = "http://localhost:8000/api/v1";

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    ...options.headers,
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("token");
      window.dispatchEvent(new Event("auth-changed"));
    }
    const errData = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(errData.detail || "Server error");
  }

  return response.json() as Promise<T>;
}

export const api = {
  auth: {
    login: async (email: string, password: string) => {
      const data = await request<{ access_token: string; user: any }>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      window.dispatchEvent(new Event("auth-changed"));
      return data.user;
    },
    logout: () => {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.dispatchEvent(new Event("auth-changed"));
    },
    getCurrentUser: async () => {
      return request<any>("/auth/me");
    },
  },
  
  loans: {
    list: async () => {
      return request<any[]>("/loans");
    },
    get: async (id: number) => {
      return request<any>(`/loans/${id}`);
    },
    predict: async (loanData: any) => {
      return request<any>("/loans/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loanData),
      });
    },
    uploadDocument: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}/loans/upload-document`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errData.detail || "Upload error");
      }
      return response.json();
    },
    explain: async (id: number) => {
      return request<any>(`/loans/${id}/explain`);
    },
    recommend: async (id: number) => {
      return request<any>(`/loans/${id}/recommend`);
    },
  },

  models: {
    list: async () => {
      return request<any[]>("/models");
    },
    active: async () => {
      return request<any>("/models/active");
    },
    uploadDataset: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}/models/upload-dataset`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload error");
      }
      return response.json();
    },
    train: async (filename: string) => {
      return request<any>(`/models/train-model?dataset_filename=${encodeURIComponent(filename)}`, {
        method: "POST",
      });
    },
  },

  dashboard: {
    getSummary: async () => {
      return request<any>("/dashboard");
    },
  },
};
