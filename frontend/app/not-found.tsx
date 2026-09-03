import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col items-center gap-4 px-4 py-24 text-center">
      <h1 className="text-xl font-semibold text-foreground">Not found</h1>
      <p className="text-muted-foreground">We couldn&apos;t find what you were looking for.</p>
      <Link
        href="/"
        className="rounded-md bg-accent-solid px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent-solid-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        Back to search
      </Link>
    </main>
  );
}
