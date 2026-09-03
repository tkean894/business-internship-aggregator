import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { redirect } from "next/navigation";

import InternshipList from "@/components/InternshipList";
import { getSavedInternships } from "@/lib/api";

export default async function SavedInternshipsPage() {
  const { userId, getToken } = await auth();
  if (!userId) {
    redirect("/sign-in");
  }
  const token = await getToken();
  if (!token) {
    redirect("/sign-in");
  }

  const saved = await getSavedInternships(token);
  const internships = saved.items.map((item) => item.internship);
  const inactiveCount = internships.filter((i) => !i.is_active).length;

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">Saved Internships</h1>
        <p className="mt-2 text-muted-foreground">
          {saved.total} saved internship{saved.total === 1 ? "" : "s"}
          {inactiveCount > 0 && ` (${inactiveCount} no longer active)`}.
        </p>
      </header>

      {internships.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border-strong px-6 py-16 text-center">
          <p className="text-base font-medium text-foreground">You haven&apos;t saved any internships yet.</p>
          <p className="mt-1 text-sm text-muted-foreground">Browse internships and click Save to keep track of ones you like.</p>
          <Link
            href="/"
            className="mt-4 inline-block rounded-md bg-accent-solid px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent-solid-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Browse internships
          </Link>
        </div>
      ) : (
        <InternshipList internships={internships} />
      )}
    </main>
  );
}
