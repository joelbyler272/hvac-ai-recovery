"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getLeads, type Lead } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { useRealtimeLeads } from "@/hooks/use-realtime";
import { ChevronRight, AlertTriangle, Users } from "lucide-react";
import { SkeletonList } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";

const statusTabs = [
  { key: "", label: "All Leads" },
  { key: "new", label: "New" },
  { key: "qualifying", label: "Qualifying" },
  { key: "qualified", label: "Qualified" },
  { key: "booked", label: "Booked" },
];

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
        <h1 className="text-2xl font-bold text-navy mb-6">Leads</h1>

        {/* Status Tabs */}
        <div className="flex gap-1 bg-navy/5 p-1 rounded-lg w-fit mb-6 flex-wrap">
          {statusTabs.map((tab) => (
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

        {/* Lead List */}
        {isError ? (
          <div className="bg-white rounded-card shadow-card p-6 flex items-center gap-3 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <p className="text-sm">Failed to load leads. Please try refreshing.</p>
          </div>
        ) : isLoading ? (
          <SkeletonList rows={5} />
        ) : data?.leads?.length ? (
          <div className="bg-white rounded-card shadow-card">
            <ul className="divide-y divide-gray-100">
              {data.leads.map((lead: Lead) => (
                <li key={lead.id}>
                  <Link
                    href={`/leads/${lead.id}`}
                    className="flex items-center justify-between px-4 py-3 hover:bg-warm-white transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <p className="text-sm font-medium text-navy">
                          {lead.name || formatPhone(lead.phone)}
                        </p>
                        <StatusBadge status={lead.status} variant="lead" />
                      </div>
                      <div className="flex gap-4 mt-1">
                        {lead.service_needed && (
                          <p className="text-xs text-slate-muted">
                            {lead.service_needed}
                          </p>
                        )}
                        {lead.urgency && (
                          <p className={`text-xs ${
                            lead.urgency === "emergency"
                              ? "text-red-600 font-medium"
                              : "text-slate-muted"
                          }`}>
                            {lead.urgency}
                          </p>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-muted" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <EmptyState
            icon={Users}
            heading="No leads captured yet"
            description="Leads are created automatically when missed calls are recovered through AI conversations."
          />
        )}
      </div>
    </DashboardLayout>
  );
}
