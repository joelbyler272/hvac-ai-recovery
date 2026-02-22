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
import { TrendingUp, Phone, Users, Calendar, DollarSign, AlertTriangle } from "lucide-react";

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
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setPeriod("weekly")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                period === "weekly"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Weekly
            </button>
            <button
              onClick={() => setPeriod("monthly")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                period === "monthly"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Monthly
            </button>
          </div>
        </div>

        {isError ? (
          <div className="bg-white rounded-lg border border-red-200 p-6 flex items-center gap-3 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <p className="text-sm">Failed to load report data. Please try refreshing.</p>
          </div>
        ) : report ? (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
              <SummaryCard icon={Phone} label="Total Calls" value={report.total_calls} />
              <SummaryCard icon={Phone} label="Recovered" value={report.recovered_calls} />
              <SummaryCard icon={Users} label="Leads" value={report.leads_captured} />
              <SummaryCard icon={Calendar} label="Appointments" value={report.appointments_booked} />
              <SummaryCard icon={DollarSign} label="Revenue" value={formatCurrency(report.estimated_revenue)} isText />
            </div>

            {/* ROI (monthly only) */}
            {period === "monthly" && report.roi_percentage !== undefined && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-8 flex items-center gap-3">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-800">
                    ROI: {report.roi_percentage}%
                  </p>
                  <p className="text-xs text-green-600">
                    Based on $497/mo subscription vs estimated revenue
                  </p>
                </div>
              </div>
            )}

            {/* Charts */}
            {report.daily_breakdown?.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-gray-200 p-5">
                  <h3 className="text-sm font-medium text-gray-900 mb-4">
                    Calls Overview
                  </h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={report.daily_breakdown}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="total_calls" fill="#3b82f6" name="Total" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="missed_calls" fill="#ef4444" name="Missed" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="recovered_calls" fill="#22c55e" name="Recovered" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-5">
                  <h3 className="text-sm font-medium text-gray-900 mb-4">
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
                        stroke="#f59e0b"
                        fill="#fef3c7"
                        name="Revenue"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <p className="text-gray-500 text-center">
              Reports will appear once you have call data.
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  isText,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  isText?: boolean;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-4 w-4 text-gray-400" />
        <p className="text-xs text-gray-500">{label}</p>
      </div>
      <p className="text-xl font-bold text-gray-900">
        {isText ? value : String(value)}
      </p>
    </div>
  );
}
