import Link from "next/link";

import type { CompanySummary } from "@/lib/types";

const FOCUS_RING =
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded-sm";

export default function CompanyCard({ company }: { company: CompanySummary }) {
  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Company</p>
      <Link href={`/companies/${company.id}`} className={`mt-1 block text-base font-semibold text-foreground hover:underline ${FOCUS_RING}`}>
        {company.name}
      </Link>
      <div className="mt-2 flex flex-col gap-1 text-sm">
        {company.website_url && (
          <a
            href={company.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`text-muted-foreground hover:text-foreground hover:underline ${FOCUS_RING}`}
          >
            Company website ↗
          </a>
        )}
        <a
          href={company.career_url}
          target="_blank"
          rel="noopener noreferrer"
          className={`text-muted-foreground hover:text-foreground hover:underline ${FOCUS_RING}`}
        >
          Careers page ↗
        </a>
      </div>
    </div>
  );
}
