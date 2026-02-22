"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getLead, type Message } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { useRealtimeMessages } from "@/hooks/use-realtime";
import Link from "next/link";
import {
  ArrowLeft,
  Phone,
  MapPin,
  Wrench,
  AlertTriangle,
  Clock,
  User,
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

  // Subscribe to realtime message updates
  const convoId = data?.conversations?.[0]?.id;
  useRealtimeMessages(convoId);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="p-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        </div>
      </DashboardLayout>
    );
  }

  if (isError) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
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
          <p className="text-gray-500">Lead not found.</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        <Link
          href="/leads"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Leads
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lead Info Card */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
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

              <div className="mt-4 pt-4 border-t border-gray-100">
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    lead.status === "qualified"
                      ? "bg-green-50 text-green-700"
                      : lead.status === "booked"
                      ? "bg-purple-50 text-purple-700"
                      : "bg-blue-50 text-blue-700"
                  }`}
                >
                  {lead.status}
                </span>
                {lead.estimated_value > 0 && (
                  <span className="ml-2 text-sm text-gray-500">
                    Est. ${lead.estimated_value}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Conversation Timeline */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
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
                              : "bg-brand-100 text-brand-900"
                            : "bg-gray-100 text-gray-900"
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
                <p className="text-gray-500 text-center py-8">
                  No messages yet.
                </p>
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
      <Icon className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-xs text-gray-500">{label}</p>
        <p className={`text-sm ${highlight ? "text-red-600 font-medium" : "text-gray-900"}`}>
          {value}
        </p>
      </div>
    </div>
  );
}
