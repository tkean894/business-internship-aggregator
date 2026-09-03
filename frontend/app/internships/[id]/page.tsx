import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { notFound } from "next/navigation";

import Badge from "@/components/Badge";
import CompanyCard from "@/components/CompanyCard";
import SaveButton from "@/components/SaveButton";
import { NotFoundError, getInternship } from "@/lib/api";
import { formatDate, freshnessLabel, isNewlyDiscovered } from "@/lib/format";

interface InternshipDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function InternshipDetailPage({ params }: InternshipDetailPageProps) {
  const { id } = await params;
  const internshipId = Number(id);
  if (!Number.isFinite(internshipId)) {
    notFound();
  }

  const { getToken } = await auth();
  const token = await getToken();

  const internship = await getInternship(internshipId, token).catch((err) => {
    if (err instanceof NotFoundError) notFound();
    throw err;
  });

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <Link
        href="/"
        className="rounded-sm text-sm font-medium text-muted-foreground hover:text-foreground hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        ← Back to search results
      </Link>

      <div className="mt-4 flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold text-foreground sm:text-3xl">{internship.title}</h1>
            {isNewlyDiscovered(internship.first_seen_at) && <Badge variant="new" />}
          </div>
          <p className="mt-1 text-muted-foreground">{internship.company.name}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {freshnessLabel(internship.posted_date, internship.first_seen_at)}
          </p>
        </div>
        <span className="shrink-0 rounded-full bg-muted px-3 py-1 text-sm font-medium text-foreground">
          {internship.category}
        </span>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-4 rounded-lg border border-border p-4 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">Location</dt>
          <dd className="mt-0.5 font-medium text-foreground">{internship.location ?? "Not specified"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Employment type</dt>
          <dd className="mt-0.5 font-medium text-foreground">{internship.employment_type}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Posted</dt>
          <dd className="mt-0.5 font-medium text-foreground">
            {internship.posted_date ? formatDate(internship.posted_date) : "Unknown"}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Application deadline</dt>
          <dd className="mt-0.5 font-medium text-foreground">
            {internship.application_deadline ? formatDate(internship.application_deadline) : "Not specified"}
          </dd>
        </div>
      </dl>

      <div className="mt-6">
        <div className="flex flex-wrap items-center gap-3">
          <a
            href={internship.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block rounded-md bg-accent-solid px-6 py-3 text-sm font-semibold text-accent-foreground hover:bg-accent-solid-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Apply on company site ↗
          </a>
          <SaveButton internshipId={internship.id} initialSaved={internship.is_saved} size="md" />
        </div>
        {!internship.is_active && (
          <p className="mt-2 text-sm text-warning">
            This posting is no longer active on the company&apos;s site. Historical record only.
          </p>
        )}
      </div>

      {internship.description && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-foreground">Description</h2>
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-foreground">{internship.description}</p>
        </div>
      )}

      <div className="mt-8">
        <CompanyCard company={internship.company} />
      </div>
    </main>
  );
}
