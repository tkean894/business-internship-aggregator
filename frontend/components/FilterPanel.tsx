"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

interface FilterPanelProps {
  categories: string[];
  companies: string[];
  industries: string[];
  selectedCategory?: string;
  selectedCompany?: string;
  selectedLocation?: string;
  selectedIndustry?: string;
}

export default function FilterPanel({
  categories,
  companies,
  industries,
  selectedCategory,
  selectedCompany,
  selectedLocation,
  selectedIndustry,
}: FilterPanelProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  function updateParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.delete("page");
    startTransition(() => {
      router.push(`${pathname}?${params.toString()}`);
    });
  }

  function clearFilters() {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("category");
    params.delete("company");
    params.delete("location");
    params.delete("industry");
    params.delete("page");
    startTransition(() => {
      router.push(`${pathname}?${params.toString()}`);
    });
  }

  const hasActiveFilters = Boolean(selectedCategory || selectedCompany || selectedLocation || selectedIndustry);

  return (
    <div className={`flex flex-wrap items-center gap-3 ${isPending ? "opacity-60" : ""}`}>
      <div>
        <label htmlFor="filter-category" className="sr-only">
          Category
        </label>
        <select
          id="filter-category"
          value={selectedCategory ?? ""}
          onChange={(e) => updateParam("category", e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>

      {industries.length > 0 && (
        <div>
          <label htmlFor="filter-industry" className="sr-only">
            Industry
          </label>
          <select
            id="filter-industry"
            value={selectedIndustry ?? ""}
            onChange={(e) => updateParam("industry", e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
          >
            <option value="">All industries</option>
            {industries.map((industry) => (
              <option key={industry} value={industry}>
                {industry}
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label htmlFor="filter-company" className="sr-only">
          Company
        </label>
        <select
          id="filter-company"
          value={selectedCompany ?? ""}
          onChange={(e) => updateParam("company", e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
        >
          <option value="">All companies</option>
          {companies.map((company) => (
            <option key={company} value={company}>
              {company}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="filter-location" className="sr-only">
          Location
        </label>
        <input
          id="filter-location"
          type="text"
          defaultValue={selectedLocation ?? ""}
          placeholder="Location"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              updateParam("location", (e.target as HTMLInputElement).value);
            }
          }}
          onBlur={(e) => updateParam("location", e.target.value)}
          className="w-36 rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
        />
      </div>

      {hasActiveFilters && (
        <button
          type="button"
          onClick={clearFilters}
          className="text-sm font-medium text-slate-500 underline-offset-2 hover:text-slate-900 hover:underline"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
