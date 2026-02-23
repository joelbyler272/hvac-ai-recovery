"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getAppointments, type Appointment } from "@/lib/api";
import { Calendar, Clock, MapPin, AlertTriangle } from "lucide-react";
import { SkeletonList } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";

export default function AppointmentsPage() {
  const { token } = useAuth();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["appointments"],
    queryFn: () => getAppointments(token!),
    enabled: !!token,
  });

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-navy mb-6">Appointments</h1>

        {isError ? (
          <div className="bg-white rounded-card shadow-card p-6 flex items-center gap-3 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <p className="text-sm">Failed to load appointments. Please try refreshing.</p>
          </div>
        ) : isLoading ? (
          <SkeletonList rows={4} />
        ) : data?.appointments?.length ? (
          <div className="bg-white rounded-card shadow-card">
            <ul className="divide-y divide-gray-100">
              {data.appointments.map((appt: Appointment) => (
                <li key={appt.id} className="px-4 py-4 hover:bg-warm-white transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <p className="text-sm font-medium text-navy">
                          {appt.lead_name || "Unknown Customer"}
                        </p>
                        <StatusBadge status={appt.status} variant="appointment" />
                      </div>
                      <div className="flex flex-wrap gap-4 text-xs text-slate-muted">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {appt.scheduled_date}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {appt.scheduled_time}
                        </span>
                        {appt.address && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {appt.address}
                          </span>
                        )}
                        {appt.service_type && (
                          <span>{appt.service_type}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <EmptyState
            icon={Calendar}
            heading="No appointments scheduled"
            description="Appointments are created when the AI successfully books a service call with a lead."
          />
        )}
      </div>
    </DashboardLayout>
  );
}
