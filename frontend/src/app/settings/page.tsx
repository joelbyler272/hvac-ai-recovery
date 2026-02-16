"use client";

export default function SettingsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
      {/* TODO: Business hours, AI greeting, notification prefs, billing */}
      <div className="space-y-6">
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Business Hours
          </h2>
          <p className="text-gray-500">Coming soon</p>
        </section>

        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            AI Greeting Message
          </h2>
          <p className="text-gray-500">Coming soon</p>
        </section>

        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Notifications
          </h2>
          <p className="text-gray-500">Coming soon</p>
        </section>
      </div>
    </div>
  );
}
