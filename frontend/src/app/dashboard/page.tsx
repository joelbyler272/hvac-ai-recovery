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

  const { data: stats, isError: statsError } = useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: () => getDashboardStats(token!),
    enabled: !!token,
    refetchInterval: 30000,
  });

  const { data: activityData, isError: activityError } = useQuery({
    queryKey: ["dashboard", "recent"],
    queryFn: () => getRecentActivity(token!),
    enabled: !!token,
    refetchInterval: 30000,
  });

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

        {(statsError || activityError) && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-800">
              Failed to load dashboard data. Please try refreshing.
            </p>
          </div>
        )}

        {/* Today's Stats */}
        <div className="mb-8">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Today
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Calls"
              value={stats?.today?.total_calls ?? 0}
              icon={Phone}
              color="blue"
            />
            <StatCard
              label="Missed Calls"
              value={stats?.today?.missed_calls ?? 0}
              icon={PhoneMissed}
              color="red"
            />
            <StatCard
              label="Recovered"
              value={stats?.today?.recovered_calls ?? 0}
              icon={PhoneForwarded}
              color="green"
            />
            <StatCard
              label="Est. Revenue"
              value={formatCurrency(stats?.today?.estimated_revenue ?? 0)}
              icon={DollarSign}
              color="amber"
              isText
            />
          </div>
        </div>

        {/* This Month */}
        <div className="mb-8">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            This Month
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Calls"
              value={stats?.this_month?.total_calls ?? 0}
              icon={Phone}
              color="blue"
            />
            <StatCard
              label="Missed Calls"
              value={stats?.this_month?.missed_calls ?? 0}
              icon={PhoneMissed}
              color="red"
            />
            <StatCard
              label="Recovered"
              value={stats?.this_month?.recovered_calls ?? 0}
              icon={PhoneForwarded}
              color="green"
            />
            <StatCard
              label="Est. Revenue"
              value={formatCurrency(stats?.this_month?.estimated_revenue ?? 0)}
              icon={DollarSign}
              color="amber"
              isText
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Recent Activity
          </h2>
          <div className="bg-white rounded-lg border border-gray-200">
            {activityData?.activities?.length ? (
              <ul className="divide-y divide-gray-100">
                {activityData.activities.map((activity: Activity, i: number) => (
                  <li key={i} className="px-4 py-3 flex items-center gap-3">
                    <ActivityIcon type={activity.type} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900">{activity.description}</p>
                      <p className="text-xs text-gray-500">{activity.time_ago}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No activity yet. Missed calls will appear here.
              </p>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

const colorMap: Record<string, string> = {
  blue: "bg-blue-50 text-blue-600",
  red: "bg-red-50 text-red-600",
  green: "bg-green-50 text-green-600",
  amber: "bg-amber-50 text-amber-600",
};

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  isText,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  isText?: boolean;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-4">
      <div className={`p-2.5 rounded-lg ${colorMap[color]}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">
          {isText ? value : String(value)}
        </p>
        <p className="text-sm text-gray-500">{label}</p>
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
    <div className="p-1.5 bg-gray-100 rounded-full">
      <Icon className="h-4 w-4 text-gray-500" />
    </div>
  );
}
