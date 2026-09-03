import Link from "next/link";

interface EmptyStateProps {
  /** Context-specific message, e.g. "for Finance" or "at Cloudflare". Falls
   * back to a generic message when no filters are active. */
  context?: string;
}

export default function EmptyState({ context }: EmptyStateProps) {
  const message = context
    ? `No internships currently available ${context}.`
    : "No internships match your search.";

  return (
    <div className="rounded-lg border border-dashed border-border-strong px-6 py-16 text-center">
      <p className="text-base font-medium text-foreground">{message}</p>
      <p className="mt-1 text-sm text-muted-foreground">Try a different search term or clear your filters.</p>
      <Link
        href="/"
        className="mt-4 inline-block rounded-md bg-accent-solid px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent-solid-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        Clear filters
      </Link>
    </div>
  );
}
