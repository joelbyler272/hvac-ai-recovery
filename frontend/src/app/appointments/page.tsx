"use client";

export default function AppointmentsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Appointments</h1>
      {/* TODO: Appointment calendar/list view */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-500 text-center">No appointments scheduled.</p>
      </div>
    </div>
  );
}
