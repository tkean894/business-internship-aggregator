import Link from "next/link";

import EmptyState from "@/components/EmptyState";
import FilterPanel from "@/components/FilterPanel";
import InternshipList from "@/components/InternshipList";
import Pagination from "@/components/Pagination";
import SearchBar from "@/components/SearchBar";
import SortSelect from "@/components/SortSelect";
import { getCategories, getCompanies, getInternships } from "@/lib/api";
import type { InternshipCategory, InternshipSort } from "@/lib/types";

const PAGE_SIZE = 12;
const RECENTLY_ADDED_COUNT = 5;

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

  const hasActiveFilters = Boolean(search || category || company || location || industry);

  const [internshipsRes, categoriesRes, companiesRes] = await Promise.all([
    getInternships({ search, category, company, location, industry, sort, page, page_size: PAGE_SIZE, active: true }),
    getCategories(),
    getCompanies(),
  ]);

  // Only fetched on the unfiltered homepage view - "Recently Added" is a
  // discovery feature, not needed (or worth the extra request) while the
  // user is already deep in a filtered search.
  const recentRes = hasActiveFilters
    ? null
    : await getInternships({ sort: "first_seen_desc", page: 1, page_size: RECENTLY_ADDED_COUNT, active: true });

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

      {recentRes && recentRes.items.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Recently Added</h2>
          <InternshipList internships={recentRes.items} />
        </section>
      )}

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
        {internshipsRes.total} internship{internshipsRes.total === 1 ? "" : "s"} found
      </p>

      {internshipsRes.items.length === 0 ? (
        <EmptyState context={emptyStateContext} />
      ) : (
        <>
          <InternshipList internships={internshipsRes.items} />
          <Pagination
            total={internshipsRes.total}
            page={internshipsRes.page}
            pageSize={internshipsRes.page_size}
            currentParams={rawParams}
          />
        </>
      )}
    </main>
  );
}
