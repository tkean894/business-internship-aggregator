import Link from "next/link";

import { formatDate } from "@/lib/format";
import type { InternshipOut } from "@/lib/types";

export default function InternshipCard({ internship }: { internship: InternshipOut }) {
  return (
    <Link
      href={`/internships/${internship.id}`}
      className="block rounded-lg border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">{internship.title}</h2>
          <p className="mt-0.5 text-sm text-slate-600">{internship.company.name}</p>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
          {internship.category}
        </span>
      </div>
      <dl className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
        {internship.location && (
          <div>
            <dt className="sr-only">Location</dt>
            <dd>{internship.location}</dd>
          </div>
        )}
        <div>
          <dt className="sr-only">Employment type</dt>
          <dd>{internship.employment_type}</dd>
        </div>
        {internship.posted_date && (
          <div>
            <dt className="sr-only">Posted date</dt>
            <dd>Posted {formatDate(internship.posted_date)}</dd>
          </div>
        )}
      </dl>
    </Link>
  );
}
