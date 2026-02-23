import { cn } from "@/lib/utils";

const callStatusColors: Record<string, string> = {
  missed: "bg-red-50 text-red-700",
  answered: "bg-teal/10 text-teal",
  voicemail: "bg-amber-50 text-amber-700",
};

const leadStatusColors: Record<string, string> = {
  new: "bg-navy/10 text-navy",
  qualifying: "bg-amber-50 text-amber-700",
  qualified: "bg-teal/10 text-teal",
  booked: "bg-purple-50 text-purple-700",
  lost: "bg-red-50 text-red-700",
  converted: "bg-green-50 text-green-700",
};

const appointmentStatusColors: Record<string, string> = {
  scheduled: "bg-navy/10 text-navy",
  confirmed: "bg-teal/10 text-teal",
  completed: "bg-green-50 text-green-700",
  cancelled: "bg-red-50 text-red-700",
  no_show: "bg-amber-50 text-amber-700",
};

const variantMap: Record<string, Record<string, string>> = {
  call: callStatusColors,
  lead: leadStatusColors,
  appointment: appointmentStatusColors,
};

export function StatusBadge({
  status,
  variant = "call",
  className,
}: {
  status: string;
  variant?: "call" | "lead" | "appointment";
  className?: string;
}) {
  const colors = variantMap[variant]?.[status] || "bg-gray-100 text-gray-600";
  const label = status.replace(/_/g, " ");

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        colors,
        className
      )}
    >
      {label}
    </span>
  );
}
