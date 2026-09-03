import Link from "next/link";

import { freshnessLabel, isNewlyDiscovered } from "@/lib/format";
import type { InternshipOut } from "@/lib/types";

import Badge from "./Badge";
import SaveButton from "./SaveButton";

export default function InternshipCard({ internship }: { internship: InternshipOut }) {
  return (
    <div className="relative rounded-lg border border-border bg-surface p-5 transition hover:border-border-strong hover:shadow-sm">
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
              className="text-base font-semibold text-foreground after:absolute after:inset-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              {internship.title}
            </Link>
            {isNewlyDiscovered(internship.first_seen_at) && <Badge variant="new" />}
            {!internship.is_active && <Badge variant="inactive" />}
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{internship.company.name}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-foreground">
            {internship.category}
          </span>
          <SaveButton internshipId={internship.id} initialSaved={internship.is_saved} />
        </div>
      </div>
      <dl className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
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
