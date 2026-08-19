import Link from "next/link";

import { getCompanies } from "@/lib/api";

export default async function CompaniesPage() {
  const companiesRes = await getCompanies();
  const companies = [...companiesRes.items].sort((a, b) => b.active_internship_count - a.active_internship_count);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
      <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900 hover:underline">
        ← Back to search results
      </Link>

      <header className="mt-4 mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Companies</h1>
        <p className="mt-2 text-slate-600">
          {companiesRes.total} compan{companiesRes.total === 1 ? "y" : "ies"} currently monitored for business internships.
        </p>
      </header>

      {companies.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-300 px-6 py-16 text-center text-sm text-slate-500">
          No companies available right now.
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {companies.map((company) => (
            <li key={company.id}>
              <Link
                href={`/companies/${company.id}`}
                className="block h-full rounded-lg border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
              >
                <div className="flex items-start justify-between gap-4">
                  <h2 className="text-base font-semibold text-slate-900">{company.name}</h2>
                  <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                    {company.active_internship_count} active
                  </span>
                </div>
                {company.industry && <p className="mt-1 text-sm text-slate-500">{company.industry}</p>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
