"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getLeads, type Lead } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { useRealtimeLeads } from "@/hooks/use-realtime";
import { ChevronRight, AlertTriangle } from "lucide-react";

const statusTabs = [
  { key: "", label: "All Leads" },
  { key: "new", label: "New" },
  { key: "qualifying", label: "Qualifying" },
  { key: "qualified", label: "Qualified" },
  { key: "booked", label: "Booked" },
];

const statusColors: Record<string, string> = {
  new: "bg-blue-50 text-blue-700",
  contacted: "bg-sky-50 text-sky-700",
  qualifying: "bg-yellow-50 text-yellow-700",
  qualified: "bg-green-50 text-green-700",
  booked: "bg-purple-50 text-purple-700",
  unresponsive: "bg-gray-50 text-gray-500",
};

export default function LeadsPage() {
  const { token } = useAuth();
  const [filter, setFilter] = useState("");
  useRealtimeLeads();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["leads", filter],
    queryFn: () => getLeads(token!, filter || undefined),
    enabled: !!token,
  });

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Leads</h1>

        {/* Status Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit mb-6 flex-wrap">
          {statusTabs.map((tab) => (
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

        {/* Lead List */}
        <div className="bg-white rounded-lg border border-gray-200">
          {isError ? (
            <div className="p-6 flex items-center gap-3 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              <p className="text-sm">Failed to load leads. Please try refreshing.</p>
            </div>
          ) : isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600 mx-auto" />
            </div>
          ) : data?.leads?.length ? (
            <ul className="divide-y divide-gray-100">
              {data.leads.map((lead: Lead) => (
                <li key={lead.id}>
                  <Link
                    href={`/leads/${lead.id}`}
                    className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <p className="text-sm font-medium text-gray-900">
                          {lead.name || formatPhone(lead.phone)}
                        </p>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            statusColors[lead.status] || statusColors.new
                          }`}
                        >
                          {lead.status}
                        </span>
                      </div>
                      <div className="flex gap-4 mt-1">
                        {lead.service_needed && (
                          <p className="text-xs text-gray-500">
                            {lead.service_needed}
                          </p>
                        )}
                        {lead.urgency && (
                          <p className={`text-xs ${
                            lead.urgency === "emergency"
                              ? "text-red-600 font-medium"
                              : "text-gray-500"
                          }`}>
                            {lead.urgency}
                          </p>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-center py-8">
              No leads captured yet.
            </p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
