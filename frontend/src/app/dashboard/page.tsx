"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getDashboardStats, getRecentActivity, type Activity } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useRealtimeCalls } from "@/hooks/use-realtime";
import {
  AlertTriangle,
  Phone,
  PhoneMissed,
  PhoneForwarded,
  DollarSign,
  MessageSquare,
  UserPlus,
  Calendar,
} from "lucide-react";

export default function DashboardPage() {
  const { token } = useAuth();
  useRealtimeCalls();

  const { data: statsData, isError: statsError } = useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: () => getDashboardStats(token!),
    enabled: !!token,
    refetchInterval: 30000,
  });
  const stats = statsData?.stats;

  const { data: activityData, isError: activityError } = useQuery({
    queryKey: ["dashboard", "recent"],
    queryFn: () => getRecentActivity(token!),
    enabled: !!token,
    refetchInterval: 30000,
  });

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-navy mb-6">Dashboard</h1>

        {(statsError || activityError) && (
          <div className="mb-6 flex items-center gap-3 rounded-card border border-red-200 bg-red-50 p-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-800">
              Failed to load dashboard data. Please try refreshing.
            </p>
          </div>
        )}

        {/* Today's Stats */}
        <div className="mb-8">
          <h2 className="text-sm font-medium text-slate-muted uppercase tracking-wide mb-3">
            Today
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Calls"
              value={stats?.today?.total_calls ?? 0}
              icon={Phone}
              variant="default"
            />
            <StatCard
              label="Missed Calls"
              value={stats?.today?.missed_calls ?? 0}
              icon={PhoneMissed}
              variant="danger"
            />
            <StatCard
              label="Recovered"
              value={stats?.today?.recovered_calls ?? 0}
              icon={PhoneForwarded}
              variant="success"
            />
            <StatCard
              label="Est. Revenue"
              value={formatCurrency(stats?.today?.estimated_revenue ?? 0)}
              icon={DollarSign}
              variant="revenue"
              isText
            />
          </div>
        </div>

        {/* This Month */}
        <div className="mb-8">
          <h2 className="text-sm font-medium text-slate-muted uppercase tracking-wide mb-3">
            This Month
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Calls"
              value={stats?.this_month?.total_calls ?? 0}
              icon={Phone}
              variant="default"
            />
            <StatCard
              label="Missed Calls"
              value={stats?.this_month?.missed_calls ?? 0}
              icon={PhoneMissed}
              variant="danger"
            />
            <StatCard
              label="Recovered"
              value={stats?.this_month?.recovered_calls ?? 0}
              icon={PhoneForwarded}
              variant="success"
            />
            <StatCard
              label="Est. Revenue"
              value={formatCurrency(stats?.this_month?.estimated_revenue ?? 0)}
              icon={DollarSign}
              variant="revenue"
              isText
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-sm font-medium text-slate-muted uppercase tracking-wide mb-3">
            Recent Activity
          </h2>
          <div className="bg-white rounded-card shadow-card">
            {activityData?.activities?.length ? (
              <ul className="divide-y divide-gray-100">
                {activityData.activities.map((activity: Activity, i: number) => (
                  <li key={i} className="px-4 py-3 flex items-center gap-3">
                    <ActivityIcon type={activity.type} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-navy">{activity.description}</p>
                      <p className="text-xs text-slate-muted">{activity.time_ago}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-12">
                <Phone className="h-8 w-8 text-slate-muted mx-auto mb-3" />
                <p className="text-sm font-medium text-navy">No activity yet</p>
                <p className="text-xs text-slate-muted mt-1">
                  Missed calls will appear here as they come in.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

const variantMap: Record<string, { icon: string; value: string }> = {
  default: { icon: "bg-navy/10 text-navy", value: "text-navy" },
  danger: { icon: "bg-red-50 text-red-600", value: "text-navy" },
  success: { icon: "bg-teal/10 text-teal", value: "text-navy" },
  revenue: { icon: "bg-ember/10 text-ember", value: "text-ember" },
};

function StatCard({
  label,
  value,
  icon: Icon,
  variant,
  isText,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  variant: string;
  isText?: boolean;
}) {
  const styles = variantMap[variant] || variantMap.default;
  return (
    <div className="bg-white rounded-card shadow-card p-4 flex items-center gap-4 hover:shadow-card-hover transition-shadow">
      <div className={`p-2.5 rounded-lg ${styles.icon}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className={`text-2xl font-bold ${styles.value}`}>
          {isText ? value : String(value)}
        </p>
        <p className="text-sm text-slate-light">{label}</p>
      </div>
    </div>
  );
}

function ActivityIcon({ type }: { type: string }) {
  const icons: Record<string, React.ComponentType<{ className?: string }>> = {
    call: Phone,
    message: MessageSquare,
    lead: UserPlus,
    appointment: Calendar,
  };
  const Icon = icons[type] || Phone;
  return (
    <div className="p-1.5 bg-navy/5 rounded-full">
      <Icon className="h-4 w-4 text-slate-light" />
    </div>
  );
}
