"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: "posted_date_desc", label: "Newest posted" },
  { value: "first_seen_desc", label: "Recently discovered" },
  { value: "last_seen_desc", label: "Recently updated" },
  { value: "company_name_asc", label: "Company name (A-Z)" },
  { value: "title_asc", label: "Title (A-Z)" },
];

export default function SortSelect({ value }: { value: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function handleChange(next: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("sort", next);
    params.delete("page");
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div>
      <label htmlFor="sort-select" className="sr-only">
        Sort by
      </label>
      <select
        id="sort-select"
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        className="rounded-md border border-border-strong bg-surface px-3 py-2 text-sm text-foreground focus:outline-none focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        {SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
