import Link from "next/link";

export default function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 px-6 py-16 text-center">
      <p className="text-base font-medium text-slate-900">No internships found.</p>
      <p className="mt-1 text-sm text-slate-500">Try a different search term or clear your filters.</p>
      <Link
        href="/"
        className="mt-4 inline-block rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
      >
        Clear filters
      </Link>
    </div>
  );
}
