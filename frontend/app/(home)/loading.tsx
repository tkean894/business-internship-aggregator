export default function Loading() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
      <div className="mb-2 h-9 w-80 animate-pulse rounded bg-stone-200 dark:bg-stone-800" />
      <div className="mb-8 h-5 w-96 animate-pulse rounded bg-stone-200 dark:bg-stone-800" />
      <div className="mb-6 h-11 w-full animate-pulse rounded-md bg-stone-200 dark:bg-stone-800" />
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-lg bg-stone-100 dark:bg-stone-700" />
        ))}
      </div>
    </main>
  );
}
