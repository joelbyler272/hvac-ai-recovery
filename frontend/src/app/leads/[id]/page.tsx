"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getLead, type Message } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { useRealtimeMessages } from "@/hooks/use-realtime";
import { SkeletonLine } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import Link from "next/link";
import {
  ArrowLeft,
  Phone,
  MapPin,
  Wrench,
  AlertTriangle,
  Clock,
  User,
  MessageSquare,
} from "lucide-react";

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  const { token } = useAuth();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["lead", params.id],
    queryFn: () => getLead(token!, params.id),
    enabled: !!token,
  });

  const lead = data?.lead;
  const messages = data?.messages || [];

  const convoId = data?.conversations?.[0]?.id;
  useRealtimeMessages(convoId);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-card shadow-card p-5 space-y-4">
              <SkeletonLine className="h-6 w-32" />
              <SkeletonLine className="h-4 w-48" />
              <SkeletonLine className="h-4 w-40" />
              <SkeletonLine className="h-4 w-36" />
            </div>
            <div className="lg:col-span-2 bg-white rounded-card shadow-card p-5 space-y-3">
              <SkeletonLine className="h-6 w-28" />
              <SkeletonLine className="h-12 w-3/4" />
              <SkeletonLine className="h-12 w-2/3 ml-auto" />
              <SkeletonLine className="h-12 w-3/4" />
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (isError) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="flex items-center gap-3 rounded-card border border-red-200 bg-red-50 p-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-800">Failed to load lead details. Please try refreshing.</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!lead) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <p className="text-slate-light">Lead not found.</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        <Link
          href="/leads"
          className="inline-flex items-center gap-1 text-sm text-slate-light hover:text-navy mb-4 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Leads
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lead Info Card */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-card shadow-card p-5">
              <h2 className="text-lg font-semibold text-navy mb-4">
                {lead.name || "Unknown"}
              </h2>

              <div className="space-y-3">
                <InfoRow icon={Phone} label="Phone" value={formatPhone(lead.phone)} />
                <InfoRow icon={Wrench} label="Service" value={lead.service_needed || "Not specified"} />
                <InfoRow
                  icon={AlertTriangle}
                  label="Urgency"
                  value={lead.urgency || "Unknown"}
                  highlight={lead.urgency === "emergency"}
                />
                <InfoRow icon={MapPin} label="Address" value={lead.address || "Not provided"} />
                <InfoRow icon={Clock} label="Preferred Time" value={lead.preferred_time || "Not specified"} />
                <InfoRow icon={User} label="Source" value={lead.source || "missed_call"} />
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2">
                <StatusBadge status={lead.status} variant="lead" />
                {(lead.estimated_value ?? 0) > 0 && (
                  <span className="text-sm text-ember font-medium">
                    Est. ${lead.estimated_value}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Conversation Timeline */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-card shadow-card p-5">
              <h3 className="text-lg font-semibold text-navy mb-4">
                Conversation
              </h3>

              {messages.length ? (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {messages.map((msg: Message) => (
                    <div
                      key={msg.id}
                      className={`flex ${
                        msg.direction === "outbound" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[75%] rounded-lg px-4 py-2.5 ${
                          msg.direction === "outbound"
                            ? msg.sender_type === "human"
                              ? "bg-purple-100 text-purple-900"
                              : "bg-ember/10 text-navy"
                            : "bg-gray-100 text-navy"
                        }`}
                      >
                        <p className="text-sm">{msg.body}</p>
                        <p className="text-xs mt-1 opacity-60">
                          {msg.sender_type === "human" ? "You" : msg.sender_type} -{" "}
                          {new Date(msg.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <MessageSquare className="h-8 w-8 text-slate-muted mx-auto mb-3" />
                  <p className="text-sm font-medium text-navy">No messages yet</p>
                  <p className="text-xs text-slate-muted mt-1">
                    Messages will appear here once the AI conversation begins.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
  highlight,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-start gap-2.5">
      <Icon className="h-4 w-4 text-slate-muted mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-xs text-slate-muted">{label}</p>
        <p className={`text-sm ${highlight ? "text-red-600 font-medium" : "text-navy"}`}>
          {value}
        </p>
      </div>
    </div>
  );
}
