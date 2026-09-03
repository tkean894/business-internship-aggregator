import Link from "next/link";

import { getCompanies } from "@/lib/api";

export default async function CompaniesPage() {
  const companiesRes = await getCompanies();
  const companies = [...companiesRes.items].sort((a, b) => b.active_internship_count - a.active_internship_count);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
      <Link
        href="/"
        className="rounded-sm text-sm font-medium text-muted-foreground hover:text-foreground hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        ← Back to search results
      </Link>

      <header className="mt-4 mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">Companies</h1>
        <p className="mt-2 text-muted-foreground">
          {companiesRes.total} compan{companiesRes.total === 1 ? "y" : "ies"} currently monitored for business internships.
        </p>
      </header>

      {companies.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border-strong px-6 py-16 text-center text-sm text-muted-foreground">
          No companies available right now.
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {companies.map((company) => (
            <li key={company.id}>
              <Link
                href={`/companies/${company.id}`}
                className="block h-full rounded-lg border border-border bg-surface p-5 transition hover:border-border-strong hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                <div className="flex items-start justify-between gap-4">
                  <h2 className="text-base font-semibold text-foreground">{company.name}</h2>
                  <span className="shrink-0 rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-foreground">
                    {company.active_internship_count} active
                  </span>
                </div>
                {company.industry && <p className="mt-1 text-sm text-muted-foreground">{company.industry}</p>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
