import Link from "next/link";

export function EmptyState({
  icon: Icon,
  heading,
  description,
  actionLabel,
  actionHref,
}: {
  icon: React.ComponentType<{ className?: string }>;
  heading: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
}) {
  return (
    <div className="bg-white rounded-card shadow-card py-16 px-6 text-center">
      <div className="inline-flex items-center justify-center p-3 bg-navy/5 rounded-full mb-4">
        <Icon className="h-6 w-6 text-slate-muted" />
      </div>
      <h3 className="text-sm font-semibold text-navy mb-1">{heading}</h3>
      <p className="text-xs text-slate-muted max-w-sm mx-auto">{description}</p>
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          className="inline-flex items-center mt-4 px-4 py-2 text-sm font-medium text-white bg-ember hover:bg-ember-dark rounded-lg transition-colors"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
