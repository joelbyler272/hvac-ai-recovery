"use client";

export default function CallsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Call Log</h1>
      {/* TODO: Implement call log with filters (all, missed, answered, date range) */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-500 text-center">No calls recorded yet.</p>
      </div>
    </div>
  );
}
