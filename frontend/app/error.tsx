"use client";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="mx-auto flex max-w-2xl flex-col items-center gap-4 px-4 py-24 text-center">
      <h1 className="text-xl font-semibold text-foreground">Unable to load internships</h1>
      <p className="text-muted-foreground">Something went wrong talking to the server. Please try again.</p>
      <button
        type="button"
        onClick={() => reset()}
        className="rounded-md bg-accent-solid px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent-solid-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        Try again
      </button>
    </main>
  );
}
