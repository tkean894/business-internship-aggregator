import Link from "next/link";
import { notFound } from "next/navigation";

import { NotFoundError, getCompany } from "@/lib/api";
import { freshnessLabel, isNewlyDiscovered } from "@/lib/format";

interface CompanyDetailPageProps {
  params: Promise<{ id: string }>;
}

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
      <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900 hover:underline">
        ← Back to search results
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-slate-900 sm:text-3xl">{company.name}</h1>
      {company.industry && (
        <p className="mt-1 text-sm font-medium uppercase tracking-wide text-slate-500">{company.industry}</p>
      )}
      <div className="mt-2 flex flex-wrap gap-4 text-sm">
        {company.website_url && (
          <a
            href={company.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-600 hover:text-slate-900 hover:underline"
          >
            Company website ↗
          </a>
        )}
        <a
          href={company.career_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-600 hover:text-slate-900 hover:underline"
        >
          Careers page ↗
        </a>
      </div>

      <h2 className="mt-8 text-lg font-semibold text-slate-900">
        Active internships ({company.active_internship_count})
      </h2>
      <div className="mt-3">
        {company.internships.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center text-sm text-slate-500">
            No active internships from this company right now. Check back later.
          </p>
        ) : (
          <ul className="flex flex-col gap-3">
            {company.internships.map((internship) => (
              <li key={internship.id}>
                <Link
                  href={`/internships/${internship.id}`}
                  className="block rounded-lg border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-base font-semibold text-slate-900">{internship.title}</h3>
                      {isNewlyDiscovered(internship.first_seen_at) && (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                          New
                        </span>
                      )}
                    </div>
                    <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                      {internship.category}
                    </span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-x-3 text-sm text-slate-500">
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
