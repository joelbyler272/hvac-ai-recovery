"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getAppointments, type Appointment } from "@/lib/api";
import { Calendar, Clock, MapPin, AlertTriangle } from "lucide-react";

const statusColors: Record<string, string> = {
  scheduled: "bg-blue-50 text-blue-700",
  confirmed: "bg-green-50 text-green-700",
  completed: "bg-gray-50 text-gray-700",
  cancelled: "bg-red-50 text-red-700",
  no_show: "bg-yellow-50 text-yellow-700",
};

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
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Appointments</h1>

        <div className="bg-white rounded-lg border border-gray-200">
          {isError ? (
            <div className="p-6 flex items-center gap-3 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              <p className="text-sm">Failed to load appointments. Please try refreshing.</p>
            </div>
          ) : isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600 mx-auto" />
            </div>
          ) : data?.appointments?.length ? (
            <ul className="divide-y divide-gray-100">
              {data.appointments.map((appt: Appointment) => (
                <li key={appt.id} className="px-4 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <p className="text-sm font-medium text-gray-900">
                          {appt.lead_name || "Unknown Customer"}
                        </p>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            statusColors[appt.status] || statusColors.scheduled
                          }`}
                        >
                          {appt.status}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-4 text-xs text-gray-500">
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
                          <span className="flex items-center gap-1">
                            {appt.service_type}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-center py-8">
              No appointments scheduled.
            </p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
