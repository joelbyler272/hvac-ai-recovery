"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getCalls, type Call } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { useRealtimeCalls } from "@/hooks/use-realtime";
import { Phone, PhoneMissed, PhoneIncoming, AlertTriangle } from "lucide-react";

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
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Call Log</h1>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                filter === tab.key
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Call List */}
        <div className="bg-white rounded-lg border border-gray-200">
          {isError ? (
            <div className="p-6 flex items-center gap-3 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              <p className="text-sm">Failed to load calls. Please try refreshing.</p>
            </div>
          ) : isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600 mx-auto" />
            </div>
          ) : data?.calls?.length ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                    Status
                  </th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                    Caller
                  </th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                    Duration
                  </th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.calls.map((call: Call) => (
                  <tr key={call.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                          call.status === "missed"
                            ? "bg-red-50 text-red-700"
                            : call.status === "answered"
                            ? "bg-green-50 text-green-700"
                            : "bg-gray-50 text-gray-700"
                        }`}
                      >
                        {call.status === "missed" ? (
                          <PhoneMissed className="h-3 w-3" />
                        ) : (
                          <PhoneIncoming className="h-3 w-3" />
                        )}
                        {call.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatPhone(call.caller_phone)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {call.duration ? `${call.duration}s` : "-"}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(call.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 text-center py-8">
              No calls recorded yet.
            </p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
