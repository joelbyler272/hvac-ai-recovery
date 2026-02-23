"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import {
  getSettings,
  updateSettings,
  getServices,
  createService,
  updateService,
  deleteService,
  getCalendarIntegrations,
  connectCalendar,
  disconnectCalendar,
  type BusinessSettings,
  type Service,
  type CalendarIntegration,
} from "@/lib/api";
import {
  Save,
  Check,
  AlertTriangle,
  Plus,
  Pencil,
  Trash2,
  X,
  Clock,
  DollarSign,
  Calendar,
} from "lucide-react";

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

// ── Service Form Component ──────────────────────────────────────────────

interface ServiceFormData {
  name: string;
  description: string;
  price: string;
  duration_minutes: number;
  is_bookable: boolean;
}

const emptyServiceForm: ServiceFormData = {
  name: "",
  description: "",
  price: "",
  duration_minutes: 60,
  is_bookable: false,
};

function ServiceForm({
  initial,
  onSave,
  onCancel,
  saving,
}: {
  initial: ServiceFormData;
  onSave: (data: ServiceFormData) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<ServiceFormData>(initial);

  return (
    <div className="border border-ember/20 bg-ember/5 rounded-card p-4 space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-navy mb-1">Service Name</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-ember"
            placeholder="e.g., AC Repair"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-navy mb-1">Duration (minutes)</label>
          <input
            type="number"
            value={form.duration_minutes}
            onChange={(e) => setForm({ ...form, duration_minutes: parseInt(e.target.value) || 60 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-ember"
            min={15}
            step={15}
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-navy mb-1">Description (optional)</label>
        <input
          type="text"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-ember"
          placeholder="Brief description of this service"
        />
      </div>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.is_bookable}
            onChange={(e) => setForm({ ...form, is_bookable: e.target.checked })}
            className="rounded border-gray-300 text-ember focus:ring-ember"
          />
          <span className="text-sm text-navy">Fixed price (book directly)</span>
        </label>

        {form.is_bookable && (
          <div className="flex items-center gap-1">
            <DollarSign className="h-4 w-4 text-slate-muted" />
            <input
              type="number"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
              className="w-24 px-2 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-ember"
              placeholder="Price"
              min={0}
              step={0.01}
            />
          </div>
        )}

        {!form.is_bookable && (
          <span className="text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded-full font-medium">
            Estimate Required
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 pt-1">
        <button
          onClick={() => onSave(form)}
          disabled={saving || !form.name.trim()}
          className="px-3 py-1.5 bg-ember text-white rounded-lg text-sm font-medium hover:bg-ember-dark disabled:opacity-50 transition-colors active:scale-[0.98]"
        >
          {saving ? "Saving..." : "Save Service"}
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-slate-light hover:text-navy text-sm transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

// ── Main Settings Page ──────────────────────────────────────────────────

export default function SettingsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);
  const [addingService, setAddingService] = useState(false);
  const [editingServiceId, setEditingServiceId] = useState<string | null>(null);

  const { data, isError } = useQuery({
    queryKey: ["settings"],
    queryFn: () => getSettings(token!),
    enabled: !!token,
  });

  const { data: servicesData } = useQuery({
    queryKey: ["services"],
    queryFn: () => getServices(token!),
    enabled: !!token,
  });

  const { data: calendarData } = useQuery({
    queryKey: ["calendar-integrations"],
    queryFn: () => getCalendarIntegrations(token!),
    enabled: !!token,
  });

  const settings = data?.settings;
  const services = servicesData?.services || [];
  const integrations = calendarData?.integrations || [];
  const [form, setForm] = useState<Partial<BusinessSettings>>({});

  useEffect(() => {
    if (settings) setForm(settings);
  }, [settings]);

  const settingsMutation = useMutation({
    mutationFn: (data: Partial<BusinessSettings>) => updateSettings(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const createServiceMutation = useMutation({
    mutationFn: (data: Partial<Service>) => createService(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] });
      setAddingService(false);
    },
  });

  const updateServiceMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Service> }) =>
      updateService(token!, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] });
      setEditingServiceId(null);
    },
  });

  const deleteServiceMutation = useMutation({
    mutationFn: (id: string) => deleteService(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] });
    },
  });

  const connectCalendarMutation = useMutation({
    mutationFn: (provider: string) => connectCalendar(token!, provider),
    onSuccess: (data) => {
      window.location.href = data.auth_url;
    },
  });

  const disconnectCalendarMutation = useMutation({
    mutationFn: (id: string) => disconnectCalendar(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["calendar-integrations"] });
    },
  });

  const handleSave = () => settingsMutation.mutate(form);

  const updateField = (key: keyof BusinessSettings, value: unknown) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const updateHours = (day: string, field: string, value: string | null) => {
    const hours = { ...(form.business_hours || {}) };
    if (value === null) {
      hours[day] = null;
    } else {
      hours[day] = { ...(hours[day] || { open: "08:00", close: "17:00" }), [field]: value };
    }
    updateField("business_hours", hours);
  };

  const handleCreateService = (formData: ServiceFormData) => {
    createServiceMutation.mutate({
      name: formData.name,
      description: formData.description || undefined,
      price: formData.is_bookable && formData.price ? parseFloat(formData.price) : undefined,
      duration_minutes: formData.duration_minutes,
      is_bookable: formData.is_bookable,
    });
  };

  const handleUpdateService = (id: string, formData: ServiceFormData) => {
    updateServiceMutation.mutate({
      id,
      data: {
        name: formData.name,
        description: formData.description || null,
        price: formData.is_bookable && formData.price ? parseFloat(formData.price) : null,
        duration_minutes: formData.duration_minutes,
        is_bookable: formData.is_bookable,
      },
    });
  };

  const handleDeleteService = (id: string, name: string) => {
    if (confirm(`Remove "${name}" from your services?`)) {
      deleteServiceMutation.mutate(id);
    }
  };

  const getCalendarForProvider = (provider: string) =>
    integrations.find((i) => i.provider === provider);

  if (isError) return (
    <DashboardLayout>
      <div className="p-6">
        <div className="flex items-center gap-3 rounded-card border border-red-200 bg-red-50 p-4">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          <p className="text-sm text-red-800">Failed to load settings. Please try refreshing.</p>
        </div>
      </div>
    </DashboardLayout>
  );

  if (!settings) return (
    <DashboardLayout>
      <div className="p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ember" />
      </div>
    </DashboardLayout>
  );

  return (
    <DashboardLayout>
      <div className="p-6 max-w-3xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-navy">Settings</h1>
          <button
            onClick={handleSave}
            disabled={settingsMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 bg-ember text-white rounded-lg text-sm font-medium hover:bg-ember-dark disabled:opacity-50 transition-colors active:scale-[0.98]"
          >
            {saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
            {saved ? "Saved!" : "Save Changes"}
          </button>
        </div>

        {settingsMutation.isError && (
          <div className="mb-6 flex items-center gap-3 rounded-card border border-red-200 bg-red-50 p-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-800">Failed to save settings. Please try again.</p>
          </div>
        )}

        <div className="space-y-6">
          {/* Business Hours */}
          <section className="bg-white rounded-card shadow-card p-6">
            <h2 className="text-lg font-medium text-navy mb-4">Business Hours</h2>
            <div className="space-y-3">
              {DAYS.map((day) => {
                const hours = form.business_hours?.[day];
                const isOpen = hours !== null && hours !== undefined;
                return (
                  <div key={day} className="flex items-center gap-4">
                    <label className="w-28 text-sm font-medium text-navy capitalize">
                      {day}
                    </label>
                    <input
                      type="checkbox"
                      checked={isOpen}
                      onChange={(e) =>
                        updateHours(day, "open", e.target.checked ? "08:00" : null)
                      }
                      className="rounded border-gray-300 text-ember focus:ring-ember"
                    />
                    {isOpen && (
                      <>
                        <input
                          type="time"
                          value={hours?.open || "08:00"}
                          onChange={(e) => updateHours(day, "open", e.target.value)}
                          className="px-2 py-1 border border-gray-300 rounded-lg text-sm"
                        />
                        <span className="text-slate-muted">to</span>
                        <input
                          type="time"
                          value={hours?.close || "17:00"}
                          onChange={(e) => updateHours(day, "close", e.target.value)}
                          className="px-2 py-1 border border-gray-300 rounded-lg text-sm"
                        />
                      </>
                    )}
                    {!isOpen && <span className="text-sm text-slate-muted">Closed</span>}
                  </div>
                );
              })}
            </div>
          </section>

          {/* Services */}
          <section className="bg-white rounded-card shadow-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-navy">Services & Pricing</h2>
              {!addingService && (
                <button
                  onClick={() => setAddingService(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-ember hover:text-ember-dark hover:bg-ember/5 rounded-lg transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  Add Service
                </button>
              )}
            </div>

            <div className="space-y-3">
              {services.map((svc) =>
                editingServiceId === svc.id ? (
                  <ServiceForm
                    key={svc.id}
                    initial={{
                      name: svc.name,
                      description: svc.description || "",
                      price: svc.price?.toString() || "",
                      duration_minutes: svc.duration_minutes,
                      is_bookable: svc.is_bookable,
                    }}
                    onSave={(data) => handleUpdateService(svc.id, data)}
                    onCancel={() => setEditingServiceId(null)}
                    saving={updateServiceMutation.isPending}
                  />
                ) : (
                  <div
                    key={svc.id}
                    className="flex items-center justify-between p-3 bg-warm-white rounded-lg group hover:bg-navy/5 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-navy">{svc.name}</span>
                        {svc.is_bookable ? (
                          <span className="text-xs bg-teal/10 text-teal px-2 py-0.5 rounded-full font-medium">
                            ${svc.price?.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-xs bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full font-medium">
                            Estimate Required
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className="text-xs text-slate-muted flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {svc.duration_minutes} min
                        </span>
                        {svc.description && (
                          <span className="text-xs text-slate-muted">{svc.description}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => setEditingServiceId(svc.id)}
                        className="p-1.5 text-slate-muted hover:text-navy rounded"
                        title="Edit"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteService(svc.id, svc.name)}
                        className="p-1.5 text-slate-muted hover:text-red-500 rounded"
                        title="Remove"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                )
              )}

              {addingService && (
                <ServiceForm
                  initial={emptyServiceForm}
                  onSave={handleCreateService}
                  onCancel={() => setAddingService(false)}
                  saving={createServiceMutation.isPending}
                />
              )}

              {services.length === 0 && !addingService && (
                <p className="text-sm text-slate-muted text-center py-4">
                  No services configured yet. Add your first service above.
                </p>
              )}
            </div>
          </section>

          {/* Calendar Integrations */}
          <section className="bg-white rounded-card shadow-card p-6">
            <h2 className="text-lg font-medium text-navy mb-4">Calendar Integrations</h2>
            <p className="text-sm text-slate-light mb-4">
              Connect your calendar so we check your availability before booking appointments.
              New appointments will also appear on your calendar.
            </p>

            <div className="space-y-3">
              {/* Google Calendar */}
              {(() => {
                const google = getCalendarForProvider("google");
                return (
                  <div className="flex items-center justify-between p-3 bg-warm-white rounded-lg">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-navy" />
                      <div>
                        <p className="text-sm font-medium text-navy">Google Calendar</p>
                        {google ? (
                          <p className="text-xs text-teal">
                            Connected{google.last_sync_at && ` · Last synced ${new Date(google.last_sync_at).toLocaleDateString()}`}
                          </p>
                        ) : (
                          <p className="text-xs text-slate-muted">Not connected</p>
                        )}
                      </div>
                    </div>
                    {google ? (
                      <button
                        onClick={() => disconnectCalendarMutation.mutate(google.id)}
                        disabled={disconnectCalendarMutation.isPending}
                        className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => connectCalendarMutation.mutate("google")}
                        disabled={connectCalendarMutation.isPending}
                        className="px-3 py-1.5 text-sm font-medium text-ember hover:text-ember-dark hover:bg-ember/5 rounded-lg transition-colors"
                      >
                        Connect
                      </button>
                    )}
                  </div>
                );
              })()}

              {/* Microsoft Outlook */}
              {(() => {
                const outlook = getCalendarForProvider("outlook");
                return (
                  <div className="flex items-center justify-between p-3 bg-warm-white rounded-lg">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-navy" />
                      <div>
                        <p className="text-sm font-medium text-navy">Microsoft Outlook</p>
                        {outlook ? (
                          <p className="text-xs text-teal">
                            Connected{outlook.last_sync_at && ` · Last synced ${new Date(outlook.last_sync_at).toLocaleDateString()}`}
                          </p>
                        ) : (
                          <p className="text-xs text-slate-muted">Not connected</p>
                        )}
                      </div>
                    </div>
                    {outlook ? (
                      <button
                        onClick={() => disconnectCalendarMutation.mutate(outlook.id)}
                        disabled={disconnectCalendarMutation.isPending}
                        className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => connectCalendarMutation.mutate("outlook")}
                        disabled={connectCalendarMutation.isPending}
                        className="px-3 py-1.5 text-sm font-medium text-ember hover:text-ember-dark hover:bg-ember/5 rounded-lg transition-colors"
                      >
                        Connect
                      </button>
                    )}
                  </div>
                );
              })()}
            </div>
          </section>

          {/* AI Greeting */}
          <section className="bg-white rounded-card shadow-card p-6">
            <h2 className="text-lg font-medium text-navy mb-4">AI Greeting Message</h2>
            <textarea
              value={form.ai_greeting || ""}
              onChange={(e) => updateField("ai_greeting", e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-ember"
              placeholder="Hey! Sorry we missed your call. This is [Your Business]. How can we help you today?"
            />
            <p className="text-xs text-slate-muted mt-1">
              This is the first message sent to callers after a missed call.
            </p>
          </section>

          {/* AI Instructions */}
          <section className="bg-white rounded-card shadow-card p-6">
            <h2 className="text-lg font-medium text-navy mb-4">Additional AI Instructions</h2>
            <textarea
              value={form.ai_instructions || ""}
              onChange={(e) => updateField("ai_instructions", e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-ember"
              placeholder="e.g., Always mention our 24/7 emergency service..."
            />
          </section>

          {/* Notifications */}
          <section className="bg-white rounded-card shadow-card p-6">
            <h2 className="text-lg font-medium text-navy mb-4">Notifications</h2>
            <div className="space-y-3">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={form.notification_prefs?.sms !== false}
                  onChange={(e) =>
                    updateField("notification_prefs", {
                      ...form.notification_prefs,
                      sms: e.target.checked,
                    })
                  }
                  className="rounded border-gray-300 text-ember focus:ring-ember"
                />
                <span className="text-sm text-navy">SMS notifications</span>
              </label>
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={form.notification_prefs?.email !== false}
                  onChange={(e) =>
                    updateField("notification_prefs", {
                      ...form.notification_prefs,
                      email: e.target.checked,
                    })
                  }
                  className="rounded border-gray-300 text-ember focus:ring-ember"
                />
                <span className="text-sm text-navy">Email notifications</span>
              </label>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-sm text-navy">Quiet hours:</span>
                <input
                  type="time"
                  value={form.notification_prefs?.quiet_start || "21:00"}
                  onChange={(e) =>
                    updateField("notification_prefs", {
                      ...form.notification_prefs,
                      quiet_start: e.target.value,
                    })
                  }
                  className="px-2 py-1 border border-gray-300 rounded-lg text-sm"
                />
                <span className="text-slate-muted">to</span>
                <input
                  type="time"
                  value={form.notification_prefs?.quiet_end || "07:00"}
                  onChange={(e) =>
                    updateField("notification_prefs", {
                      ...form.notification_prefs,
                      quiet_end: e.target.value,
                    })
                  }
                  className="px-2 py-1 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>
          </section>
        </div>
      </div>
    </DashboardLayout>
  );
}
