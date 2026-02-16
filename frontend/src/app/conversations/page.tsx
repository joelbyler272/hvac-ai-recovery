"use client";

export default function ConversationsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Conversations</h1>
      {/* TODO: Active conversations list with takeover option */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-500 text-center">No active conversations.</p>
      </div>
    </div>
  );
}
