"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { getWeeklyReport, getMonthlyReport } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { TrendingUp, Phone, Users, Calendar, DollarSign, AlertTriangle, BarChart3 } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

// Chart colors per brand
const CHART_COLORS = {
  total: "#1B2A4A",    // navy
  missed: "#ef4444",   // red
  recovered: "#38B2AC", // teal
  revenue: "#E86A2A",  // ember
  revenueFill: "rgba(232, 106, 42, 0.1)",
};

export default function ReportsPage() {
  const { token } = useAuth();
  const [period, setPeriod] = useState<"weekly" | "monthly">("weekly");

  const { data: weeklyData, isError: weeklyError } = useQuery({
    queryKey: ["reports", "weekly"],
    queryFn: () => getWeeklyReport(token!),
    enabled: !!token && period === "weekly",
  });

  const { data: monthlyData, isError: monthlyError } = useQuery({
    queryKey: ["reports", "monthly"],
    queryFn: () => getMonthlyReport(token!),
    enabled: !!token && period === "monthly",
  });

  const isError = (period === "weekly" && weeklyError) || (period === "monthly" && monthlyError);

  const report = period === "weekly" ? weeklyData?.report : monthlyData?.report;

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-navy">Reports</h1>
          <div className="flex gap-1 bg-navy/5 p-1 rounded-lg">
            <button
              onClick={() => setPeriod("weekly")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                period === "weekly"
                  ? "bg-white text-navy shadow-card"
                  : "text-slate-light hover:text-navy"
              }`}
            >
              Weekly
            </button>
            <button
              onClick={() => setPeriod("monthly")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                period === "monthly"
                  ? "bg-white text-navy shadow-card"
                  : "text-slate-light hover:text-navy"
              }`}
            >
              Monthly
            </button>
          </div>
        </div>

        {isError ? (
          <div className="bg-white rounded-card shadow-card p-6 flex items-center gap-3 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <p className="text-sm">Failed to load report data. Please try refreshing.</p>
          </div>
        ) : report ? (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
              <SummaryCard icon={Phone} label="Total Calls" value={report.total_calls} />
              <SummaryCard icon={Phone} label="Recovered" value={report.recovered_calls} variant="success" />
              <SummaryCard icon={Users} label="Leads" value={report.leads_captured} />
              <SummaryCard icon={Calendar} label="Appointments" value={report.appointments_booked} />
              <SummaryCard icon={DollarSign} label="Revenue" value={formatCurrency(report.estimated_revenue)} variant="revenue" isText />
            </div>

            {/* ROI (monthly only) */}
            {period === "monthly" && report.roi_percentage !== undefined && (
              <div className="bg-teal/10 border border-teal/20 rounded-card p-4 mb-8 flex items-center gap-3">
                <TrendingUp className="h-5 w-5 text-teal" />
                <div>
                  <p className="text-sm font-medium text-navy">
                    ROI: {report.roi_percentage}%
                  </p>
                  <p className="text-xs text-slate-light">
                    Based on $497/mo subscription vs estimated revenue
                  </p>
                </div>
              </div>
            )}

            {/* Charts */}
            {report.daily_breakdown?.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-card shadow-card p-5">
                  <h3 className="text-sm font-medium text-navy mb-4">
                    Calls Overview
                  </h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={report.daily_breakdown}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="total_calls" fill={CHART_COLORS.total} name="Total" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="missed_calls" fill={CHART_COLORS.missed} name="Missed" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="recovered_calls" fill={CHART_COLORS.recovered} name="Recovered" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white rounded-card shadow-card p-5">
                  <h3 className="text-sm font-medium text-navy mb-4">
                    Estimated Revenue
                  </h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={report.daily_breakdown}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="estimated_revenue"
                        stroke={CHART_COLORS.revenue}
                        fill={CHART_COLORS.revenueFill}
                        name="Revenue"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        ) : (
          <EmptyState
            icon={BarChart3}
            heading="No report data yet"
            description="Reports will appear once you have call data. Check back after your first missed calls are recovered."
          />
        )}
      </div>
    </DashboardLayout>
  );
}

const variantStyles: Record<string, { icon: string; value: string }> = {
  default: { icon: "text-slate-muted", value: "text-navy" },
  success: { icon: "text-teal", value: "text-navy" },
  revenue: { icon: "text-ember", value: "text-ember" },
};

function SummaryCard({
  icon: Icon,
  label,
  value,
  variant = "default",
  isText,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  variant?: string;
  isText?: boolean;
}) {
  const styles = variantStyles[variant] || variantStyles.default;
  return (
    <div className="bg-white rounded-card shadow-card p-4 hover:shadow-card-hover transition-shadow">
      <div className="flex items-center gap-2 mb-1">
        <Icon className={`h-4 w-4 ${styles.icon}`} />
        <p className="text-xs text-slate-muted">{label}</p>
      </div>
      <p className={`text-xl font-bold ${styles.value}`}>
        {isText ? value : String(value)}
      </p>
    </div>
  );
}
