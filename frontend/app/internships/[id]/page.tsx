import Link from "next/link";
import { notFound } from "next/navigation";

import CompanyCard from "@/components/CompanyCard";
import { NotFoundError, getInternship } from "@/lib/api";
import { formatDate } from "@/lib/format";

interface InternshipDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function InternshipDetailPage({ params }: InternshipDetailPageProps) {
  const { id } = await params;
  const internshipId = Number(id);
  if (!Number.isFinite(internshipId)) {
    notFound();
  }

  const internship = await getInternship(internshipId).catch((err) => {
    if (err instanceof NotFoundError) notFound();
    throw err;
  });

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900 hover:underline">
        ← Back to search results
      </Link>

      <div className="mt-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{internship.title}</h1>
          <p className="mt-1 text-slate-600">{internship.company.name}</p>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
          {internship.category}
        </span>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-4 rounded-lg border border-slate-200 p-4 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-slate-500">Location</dt>
          <dd className="mt-0.5 font-medium text-slate-900">{internship.location ?? "Not specified"}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Employment type</dt>
          <dd className="mt-0.5 font-medium text-slate-900">{internship.employment_type}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Posted</dt>
          <dd className="mt-0.5 font-medium text-slate-900">
            {internship.posted_date ? formatDate(internship.posted_date) : "Unknown"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Application deadline</dt>
          <dd className="mt-0.5 font-medium text-slate-900">
            {internship.application_deadline ? formatDate(internship.application_deadline) : "Not specified"}
          </dd>
        </div>
      </dl>

      <div className="mt-6">
        <a
          href={internship.application_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block rounded-md bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-700"
        >
          Apply on company site ↗
        </a>
        {!internship.is_active && (
          <p className="mt-2 text-sm text-amber-600">
            This posting is no longer active on the company&apos;s site. Historical record only.
          </p>
        )}
      </div>

      {internship.description && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-slate-900">Description</h2>
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-700">{internship.description}</p>
        </div>
      )}

      <div className="mt-8">
        <CompanyCard company={internship.company} />
      </div>
    </main>
  );
}
