import { cn } from "@/lib/utils";

export function SkeletonLine({ className }: { className?: string }) {
  return (
    <div
      className={cn("h-4 bg-navy/5 animate-pulse rounded", className)}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-card shadow-card p-4 flex items-center gap-4">
      <div className="h-10 w-10 bg-navy/5 animate-pulse rounded-lg" />
      <div className="flex-1 space-y-2">
        <div className="h-6 w-16 bg-navy/5 animate-pulse rounded" />
        <div className="h-3 w-24 bg-navy/5 animate-pulse rounded" />
      </div>
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="px-4 py-3 flex items-center gap-4">
      <div className="h-4 w-24 bg-navy/5 animate-pulse rounded" />
      <div className="h-4 w-32 bg-navy/5 animate-pulse rounded" />
      <div className="h-4 w-20 bg-navy/5 animate-pulse rounded" />
      <div className="flex-1" />
      <div className="h-5 w-16 bg-navy/5 animate-pulse rounded-full" />
    </div>
  );
}

export function SkeletonList({ rows = 5 }: { rows?: number }) {
  return (
    <div className="bg-white rounded-card shadow-card divide-y divide-gray-100">
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonRow key={i} />
      ))}
    </div>
  );
}
