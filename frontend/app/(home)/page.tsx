import Link from "next/link";

import EmptyState from "@/components/EmptyState";
import FilterPanel from "@/components/FilterPanel";
import InternshipList from "@/components/InternshipList";
import Pagination from "@/components/Pagination";
import SearchBar from "@/components/SearchBar";
import SortSelect from "@/components/SortSelect";
import { getAllInternships, getCategories, getCompanies } from "@/lib/api";
import { isUsLocation } from "@/lib/location";
import type { InternshipCategory, InternshipSort } from "@/lib/types";

const PAGE_SIZE = 12;

type RawSearchParams = Record<string, string | string[] | undefined>;

interface HomePageProps {
  searchParams: Promise<RawSearchParams>;
}

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const rawParams = await searchParams;

  const search = first(rawParams.search);
  const category = first(rawParams.category) as InternshipCategory | undefined;
  const company = first(rawParams.company);
  const location = first(rawParams.location);
  const industry = first(rawParams.industry);
  const sort = (first(rawParams.sort) as InternshipSort | undefined) ?? "posted_date_desc";
  const page = Number(first(rawParams.page) ?? "1") || 1;

  const [allMatchingInternships, categoriesRes, companiesRes] = await Promise.all([
    getAllInternships({ search, category, company, location, industry, sort, active: true }),
    getCategories(),
    getCompanies(),
  ]);

  // USA-only display filter (see lib/location.ts). Pagination has to run
  // over the *filtered* set, not a raw API page filtered after the fact -
  // otherwise a page whose raw results happen to be mostly/all non-US
  // would look completely empty even though later pages have real
  // matches (a real bug: see git history). getAllInternships() fetches
  // every internship matching the current search/filters up front so
  // filtering and pagination can both be computed correctly here.
  const usInternships = allMatchingInternships.filter((item) => isUsLocation(item.location));
  const totalUsInternships = usInternships.length;
  const visibleItems = usInternships.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Derived from data already fetched for the filter panel - no extra
  // API request needed for the hero stat.
  const totalActiveInternships = companiesRes.items.reduce((sum, c) => sum + c.active_internship_count, 0);
  const industries = Array.from(new Set(companiesRes.items.map((c) => c.industry).filter((i): i is string => Boolean(i)))).sort();

  const emptyStateContext = category
    ? `for ${category}`
    : company
      ? `at ${company}`
      : industry
        ? `in ${industry}`
        : undefined;

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Business internships, all in one place.
        </h1>
        <p className="mt-2 text-slate-600">
          Search internships across finance, consulting, marketing, analytics, operations, product, and more.
        </p>
        <p className="mt-3 text-sm text-slate-500">
          {totalActiveInternships} active internship{totalActiveInternships === 1 ? "" : "s"} across{" "}
          {companiesRes.total} compan{companiesRes.total === 1 ? "y" : "ies"} and {categoriesRes.categories.length}{" "}
          categories.
        </p>
      </header>

      <div className="mb-6 flex flex-wrap gap-2">
        {categoriesRes.categories.map((cat) => (
          <Link
            key={cat}
            href={`/?category=${encodeURIComponent(cat)}`}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
              category === cat
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
            }`}
          >
            {cat}
          </Link>
        ))}
      </div>

      <div className="mb-6 flex flex-col gap-4">
        <SearchBar defaultValue={search ?? ""} />
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <FilterPanel
            categories={categoriesRes.categories}
            companies={companiesRes.items.map((c) => c.name)}
            industries={industries}
            selectedCategory={category}
            selectedCompany={company}
            selectedLocation={location}
            selectedIndustry={industry}
          />
          <SortSelect value={sort} />
        </div>
      </div>

      <p className="mb-4 text-sm text-slate-500">
        {totalUsInternships} US-based internship{totalUsInternships === 1 ? "" : "s"} found
      </p>

      {visibleItems.length === 0 ? (
        <EmptyState context={emptyStateContext} />
      ) : (
        <>
          <InternshipList internships={visibleItems} />
          <Pagination total={totalUsInternships} page={page} pageSize={PAGE_SIZE} currentParams={rawParams} />
        </>
      )}
    </main>
  );
}
