const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface FetchOptions extends RequestInit {
  token?: string;
}

// --- API Types ---

export interface DashboardStats {
  today: {
    total_calls: number;
    missed_calls: number;
    recovered_calls: number;
    estimated_revenue: number;
  };
  this_month: {
    total_calls: number;
    missed_calls: number;
    recovered_calls: number;
    estimated_revenue: number;
  };
}

export interface Activity {
  type: "call" | "message" | "lead" | "appointment";
  description: string;
  time_ago: string;
  body_preview?: string;
}

export interface Lead {
  id: string;
  business_id: string;
  phone: string;
  name: string | null;
  email: string | null;
  address: string | null;
  service_needed: string | null;
  urgency: string | null;
  status: string;
  source: string;
  estimated_value: number | null;
  preferred_time: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  business_id: string;
  lead_id: string;
  call_id: string | null;
  status: string;
  follow_up_count: number;
  next_follow_up_at: string | null;
  qualification_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  lead?: Lead;
  lead_name?: string;
  lead_phone?: string;
  last_message?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  business_id: string;
  direction: "inbound" | "outbound";
  sender_type: "caller" | "ai" | "human";
  body: string;
  twilio_sid: string | null;
  status: string;
  created_at: string;
}

export interface Call {
  id: string;
  business_id: string;
  twilio_call_sid: string;
  caller_phone: string;
  status: string;
  duration_seconds: number | null;
  is_after_hours: boolean;
  recording_url: string | null;
  transcription: string | null;
  created_at: string;
}

export interface Appointment {
  id: string;
  business_id: string;
  lead_id: string;
  conversation_id: string | null;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
  service_type: string | null;
  address: string | null;
  status: string;
  notes: string | null;
  lead_name?: string;
  created_at: string;
  updated_at: string;
}

export interface DailyMetric {
  id: string;
  date: string;
  total_calls: number;
  missed_calls: number;
  recovered_calls: number;
  leads_captured: number;
  leads_qualified: number;
  appointments_booked: number;
  estimated_revenue: number;
  messages_sent: number;
  messages_received: number;
}

export interface Report {
  period_start: string;
  period_end: string;
  total_calls: number;
  missed_calls: number;
  recovered_calls: number;
  leads_captured: number;
  leads_qualified: number;
  appointments_booked: number;
  estimated_revenue: number;
  roi_percentage?: number;
  daily_breakdown: DailyMetric[];
}

export interface BusinessSettings {
  name: string;
  owner_name: string;
  owner_email: string;
  owner_phone: string;
  business_phone: string;
  twilio_number: string;
  timezone: string;
  business_hours: Record<string, { open: string; close: string } | null>;
  services: string[];
  ai_greeting: string | null;
  ai_instructions: string | null;
  notification_prefs: {
    sms: boolean;
    email: boolean;
    quiet_start: string;
    quiet_end: string;
  };
}

export interface Service {
  id: string;
  business_id: string;
  name: string;
  description: string | null;
  price: number | null;
  duration_minutes: number;
  is_bookable: boolean;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface CalendarIntegration {
  id: string;
  business_id: string;
  provider: "google" | "outlook";
  calendar_id: string | null;
  is_active: boolean;
  last_sync_at: string | null;
  created_at: string;
}

export interface CreateAppointmentData {
  lead_id: string;
  scheduled_date: string;
  scheduled_time: string;
  service_type?: string;
  address?: string;
  notes?: string;
  conversation_id?: string;
}

// --- API Client ---

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
  apiFetch<{ stats: DashboardStats }>("/api/dashboard/stats", { token });

export const getRecentActivity = (token: string) =>
  apiFetch<{ activities: Activity[] }>("/api/dashboard/recent", { token });

// Leads
export const getLeads = (token: string, status?: string) =>
  apiFetch<{ leads: Lead[] }>(`/api/leads${status ? `?status=${status}` : ""}`, { token });

export const getLead = (token: string, id: string) =>
  apiFetch<{ lead: Lead; conversations: Conversation[]; messages: Message[] }>(`/api/leads/${id}`, { token });

export const updateLead = (token: string, id: string, data: Partial<Lead>) =>
  apiFetch<{ lead: Lead }>(`/api/leads/${id}`, {
    token,
    method: "PATCH",
    body: JSON.stringify(data),
  });

// Conversations
export const getConversations = (token: string, status?: string) =>
  apiFetch<{ conversations: Conversation[] }>(
    `/api/conversations${status ? `?status=${status}` : ""}`,
    { token }
  );

export const getConversation = (token: string, id: string) =>
  apiFetch<{ conversation: Conversation; messages: Message[] }>(`/api/conversations/${id}`, { token });

export const takeoverConversation = (token: string, id: string) =>
  apiFetch<{ conversation: Conversation }>(`/api/conversations/${id}/takeover`, { token, method: "POST" });

export const returnToAI = (token: string, id: string) =>
  apiFetch<{ conversation: Conversation }>(`/api/conversations/${id}/return-ai`, {
    token,
    method: "POST",
  });

export const sendMessage = (token: string, id: string, body: string) =>
  apiFetch<{ message: Message }>(`/api/conversations/${id}/message`, {
    token,
    method: "POST",
    body: JSON.stringify({ body }),
  });

// Calls
export const getCalls = (token: string, status?: string) =>
  apiFetch<{ calls: Call[] }>(`/api/calls${status ? `?status=${status}` : ""}`, { token });

// Appointments
export const getAppointments = (token: string) =>
  apiFetch<{ appointments: Appointment[] }>("/api/appointments", { token });

export const createAppointment = (token: string, data: CreateAppointmentData) =>
  apiFetch<{ appointment: Appointment }>("/api/appointments", {
    token,
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateAppointment = (token: string, id: string, data: Partial<Appointment>) =>
  apiFetch<{ appointment: Appointment }>(`/api/appointments/${id}`, {
    token,
    method: "PATCH",
    body: JSON.stringify(data),
  });

// Reports
export const getWeeklyReport = (token: string) =>
  apiFetch<{ report: Report }>("/api/reports/weekly", { token });

export const getMonthlyReport = (token: string) =>
  apiFetch<{ report: Report }>("/api/reports/monthly", { token });

// Settings
export const getSettings = (token: string) =>
  apiFetch<{ settings: BusinessSettings }>("/api/settings", { token });

export const updateSettings = (token: string, data: Partial<BusinessSettings>) =>
  apiFetch<{ settings: BusinessSettings }>("/api/settings", {
    token,
    method: "PATCH",
    body: JSON.stringify(data),
  });

// Services
export const getServices = (token: string) =>
  apiFetch<{ services: Service[] }>("/api/services", { token });

export const createService = (token: string, data: Partial<Service>) =>
  apiFetch<{ service: Service }>("/api/services", {
    token,
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateService = (token: string, id: string, data: Partial<Service>) =>
  apiFetch<{ service: Service }>(`/api/services/${id}`, {
    token,
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteService = (token: string, id: string) =>
  apiFetch<{ deleted: boolean }>(`/api/services/${id}`, {
    token,
    method: "DELETE",
  });

// Calendar Integrations
export const getCalendarIntegrations = (token: string) =>
  apiFetch<{ integrations: CalendarIntegration[] }>("/api/calendar/integrations", { token });

export const connectCalendar = (token: string, provider: string) =>
  apiFetch<{ auth_url: string }>(`/api/calendar/connect/${provider}`, { token });

export const disconnectCalendar = (token: string, id: string) =>
  apiFetch<{ deleted: boolean }>(`/api/calendar/integrations/${id}`, {
    token,
    method: "DELETE",
  });
