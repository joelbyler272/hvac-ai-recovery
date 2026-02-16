const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface FetchOptions extends RequestInit {
  token?: string;
}

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Dashboard
export const getDashboardStats = (token: string) =>
  apiFetch("/api/dashboard/stats", { token });

export const getRecentActivity = (token: string) =>
  apiFetch("/api/dashboard/recent", { token });

// Leads
export const getLeads = (token: string, status?: string) =>
  apiFetch(`/api/leads${status ? `?status=${status}` : ""}`, { token });

export const getLead = (token: string, id: string) =>
  apiFetch(`/api/leads/${id}`, { token });

// Conversations
export const getConversations = (token: string) =>
  apiFetch("/api/conversations", { token });

export const getConversation = (token: string, id: string) =>
  apiFetch(`/api/conversations/${id}`, { token });

export const takeoverConversation = (token: string, id: string) =>
  apiFetch(`/api/conversations/${id}/takeover`, { token, method: "POST" });

export const returnToAI = (token: string, id: string) =>
  apiFetch(`/api/conversations/${id}/return-ai`, { token, method: "POST" });

// Appointments
export const getAppointments = (token: string) =>
  apiFetch("/api/appointments", { token });
