"use client";

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Lead Detail</h1>
      {/* TODO: Lead detail with full conversation, timeline, and actions */}
      <p className="text-gray-500">Lead ID: {params.id}</p>
    </div>
  );
}
