"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition } from "react";

export default function SearchBar({ defaultValue }: { defaultValue: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [value, setValue] = useState(defaultValue);
  const [isPending, startTransition] = useTransition();

  function submit() {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set("search", value);
    } else {
      params.delete("search");
    }
    params.delete("page"); // a new search always starts back at page 1
    startTransition(() => {
      router.push(`${pathname}?${params.toString()}`);
    });
  }

  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      className="flex gap-2"
    >
      <label htmlFor="internship-search" className="sr-only">
        Search internships
      </label>
      <input
        id="internship-search"
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Search by title, company, or keyword..."
        className="w-full rounded-md border border-border-strong bg-surface px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      />
      <button
        type="submit"
        disabled={isPending}
        className="shrink-0 rounded-md bg-accent-solid px-5 py-2.5 text-sm font-medium text-accent-foreground hover:bg-accent-solid-hover disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        Search
      </button>
    </form>
  );
}
