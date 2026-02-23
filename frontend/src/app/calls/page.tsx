"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getCalls, type Call } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { useRealtimeCalls } from "@/hooks/use-realtime";
import { Phone, PhoneMissed, PhoneIncoming, AlertTriangle } from "lucide-react";
import { SkeletonList } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";

const tabs = [
  { key: "", label: "All Calls" },
  { key: "missed", label: "Missed" },
  { key: "answered", label: "Answered" },
];

export default function CallsPage() {
  const { token } = useAuth();
  const [filter, setFilter] = useState("");
  useRealtimeCalls();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["calls", filter],
    queryFn: () => getCalls(token!, filter || undefined),
    enabled: !!token,
  });

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-navy mb-6">Call Log</h1>

        {/* Tabs */}
        <div className="flex gap-1 bg-navy/5 p-1 rounded-lg w-fit mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                filter === tab.key
                  ? "bg-white text-navy shadow-card"
                  : "text-slate-light hover:text-navy"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Call List */}
        {isError ? (
          <div className="bg-white rounded-card shadow-card p-6 flex items-center gap-3 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <p className="text-sm">Failed to load calls. Please try refreshing.</p>
          </div>
        ) : isLoading ? (
          <SkeletonList rows={5} />
        ) : data?.calls?.length ? (
          <div className="bg-white rounded-card shadow-card">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left text-xs font-medium text-slate-muted uppercase px-4 py-3">
                    Status
                  </th>
                  <th className="text-left text-xs font-medium text-slate-muted uppercase px-4 py-3">
                    Caller
                  </th>
                  <th className="text-left text-xs font-medium text-slate-muted uppercase px-4 py-3">
                    Duration
                  </th>
                  <th className="text-left text-xs font-medium text-slate-muted uppercase px-4 py-3">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.calls.map((call: Call) => (
                  <tr key={call.id} className="hover:bg-warm-white transition-colors">
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5">
                        {call.status === "missed" ? (
                          <PhoneMissed className="h-3 w-3 text-red-500" />
                        ) : (
                          <PhoneIncoming className="h-3 w-3 text-teal" />
                        )}
                        <StatusBadge status={call.status} variant="call" />
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-navy">
                      {formatPhone(call.caller_phone)}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-light">
                      {call.duration_seconds ? `${call.duration_seconds}s` : "-"}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-light">
                      {new Date(call.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Phone}
            heading="No calls recorded yet"
            description="Calls will appear here as they come in. Make sure your Twilio number is configured."
          />
        )}
      </div>
    </DashboardLayout>
  );
}
