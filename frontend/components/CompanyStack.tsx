"use client";

import { useState } from "react";

import type { InternshipOut } from "@/lib/types";

import InternshipCard from "./InternshipCard";

/**
 * Collapsed group of same-company postings (see InternshipList.tsx for
 * when this is used instead of individual cards). `items` is already in
 * the page's current sort order - the expanded dropdown just renders it
 * as-is rather than re-sorting.
 */
export default function CompanyStack({ companyName, items }: { companyName: string; items: InternshipOut[] }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        className="flex w-full items-center justify-between gap-4 p-5 text-left transition hover:bg-slate-50"
      >
        <div>
          <p className="text-base font-semibold text-slate-900">{companyName}</p>
          <p className="mt-0.5 text-sm text-slate-600">{items.length} open internships</p>
        </div>
        <span className="shrink-0 text-sm font-medium text-slate-500">{expanded ? "Hide" : "Show"} all</span>
      </button>
      {expanded && (
        <ul className="flex flex-col gap-3 border-t border-slate-200 p-3">
          {items.map((internship) => (
            <li key={internship.id}>
              <InternshipCard internship={internship} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
