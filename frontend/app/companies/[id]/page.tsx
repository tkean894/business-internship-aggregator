import Link from "next/link";
import { notFound } from "next/navigation";

import Badge from "@/components/Badge";
import { NotFoundError, getCompany } from "@/lib/api";
import { freshnessLabel, isNewlyDiscovered } from "@/lib/format";

interface CompanyDetailPageProps {
  params: Promise<{ id: string }>;
}

const FOCUS_RING =
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded-sm";

export default async function CompanyDetailPage({ params }: CompanyDetailPageProps) {
  const { id } = await params;
  const companyId = Number(id);
  if (!Number.isFinite(companyId)) {
    notFound();
  }

  const company = await getCompany(companyId).catch((err) => {
    if (err instanceof NotFoundError) notFound();
    throw err;
  });

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <Link href="/" className={`text-sm font-medium text-muted-foreground hover:text-foreground hover:underline ${FOCUS_RING}`}>
        ← Back to search results
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-foreground sm:text-3xl">{company.name}</h1>
      {company.industry && (
        <p className="mt-1 text-sm font-medium uppercase tracking-wide text-muted-foreground">{company.industry}</p>
      )}
      <div className="mt-2 flex flex-wrap gap-4 text-sm">
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

      <h2 className="mt-8 text-lg font-semibold text-foreground">
        Active internships ({company.active_internship_count})
      </h2>
      <div className="mt-3">
        {company.internships.length === 0 ? (
          <p className="rounded-lg border border-dashed border-border-strong px-6 py-10 text-center text-sm text-muted-foreground">
            No active internships from this company right now. Check back later.
          </p>
        ) : (
          <ul className="flex flex-col gap-3">
            {company.internships.map((internship) => (
              <li key={internship.id}>
                <Link
                  href={`/internships/${internship.id}`}
                  className={`block rounded-lg border border-border bg-surface p-5 transition hover:border-border-strong hover:shadow-sm ${FOCUS_RING}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-base font-semibold text-foreground">{internship.title}</h3>
                      {isNewlyDiscovered(internship.first_seen_at) && <Badge variant="new" />}
                    </div>
                    <span className="shrink-0 rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-foreground">
                      {internship.category}
                    </span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-x-3 text-sm text-muted-foreground">
                    {internship.location && <span>{internship.location}</span>}
                    <span>{freshnessLabel(internship.posted_date, internship.first_seen_at)}</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
