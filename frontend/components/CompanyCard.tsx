import Link from "next/link";

import type { CompanySummary } from "@/lib/types";

export default function CompanyCard({ company }: { company: CompanySummary }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Company</p>
      <Link
        href={`/companies/${company.id}`}
        className="mt-1 block text-base font-semibold text-slate-900 hover:underline"
      >
        {company.name}
      </Link>
      <div className="mt-2 flex flex-col gap-1 text-sm">
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
    </div>
  );
}
