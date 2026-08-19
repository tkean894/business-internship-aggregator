import Link from "next/link";

import { freshnessLabel, isNewlyDiscovered } from "@/lib/format";
import type { InternshipOut } from "@/lib/types";

import SaveButton from "./SaveButton";

export default function InternshipCard({ internship }: { internship: InternshipOut }) {
  return (
    <div className="relative rounded-lg border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            {/* "Stretched link" pattern: the ::after pseudo-element fills
                the whole card, so the card is clickable everywhere, while
                SaveButton (given z-10 + relative in its own component)
                stays independently clickable without nesting a <button>
                inside this <a> - avoids an invalid/inaccessible nested
                interactive element. */}
            <Link
              href={`/internships/${internship.id}`}
              className="text-base font-semibold text-slate-900 after:absolute after:inset-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            >
              {internship.title}
            </Link>
            {isNewlyDiscovered(internship.first_seen_at) && (
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                New
              </span>
            )}
            {!internship.is_active && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">
                No longer active
              </span>
            )}
          </div>
          <p className="mt-0.5 text-sm text-slate-600">{internship.company.name}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
            {internship.category}
          </span>
          <SaveButton internshipId={internship.id} initialSaved={internship.is_saved} />
        </div>
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
        <div>
          <dt className="sr-only">Freshness</dt>
          <dd>{freshnessLabel(internship.posted_date, internship.first_seen_at)}</dd>
        </div>
      </dl>
    </div>
  );
}
