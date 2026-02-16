"use client";

export default function LeadsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Leads</h1>
      {/* TODO: Implement lead pipeline view (new, qualifying, qualified, booked) */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-500 text-center">No leads captured yet.</p>
      </div>
    </div>
  );
}
