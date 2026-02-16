"use client";

export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Today's Stats */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
          Today
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Calls" value="0" />
          <StatCard label="Missed" value="0" />
          <StatCard label="Recovered" value="0" />
          <StatCard label="Est. Revenue" value="$0" />
        </div>
      </div>

      {/* This Month */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
          This Month
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Calls" value="0" />
          <StatCard label="Missed" value="0" />
          <StatCard label="Recovered" value="0" />
          <StatCard label="Est. Revenue" value="$0" />
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
          Recent Activity
        </h2>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-gray-500 text-center">
            No activity yet. Missed calls will appear here.
          </p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  );
}
