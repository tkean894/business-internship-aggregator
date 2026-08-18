import EmptyState from "@/components/EmptyState";
import FilterPanel from "@/components/FilterPanel";
import InternshipList from "@/components/InternshipList";
import Pagination from "@/components/Pagination";
import SearchBar from "@/components/SearchBar";
import SortSelect from "@/components/SortSelect";
import { getCategories, getCompanies, getInternships } from "@/lib/api";
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
  const sort = (first(rawParams.sort) as InternshipSort | undefined) ?? "posted_date_desc";
  const page = Number(first(rawParams.page) ?? "1") || 1;

  const [internshipsRes, categoriesRes, companiesRes] = await Promise.all([
    getInternships({ search, category, company, location, sort, page, page_size: PAGE_SIZE, active: true }),
    getCategories(),
    getCompanies(),
  ]);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Find Business Internships</h1>
        <p className="mt-2 text-slate-600">Search internships across companies, functions, and locations.</p>
      </header>

      <div className="mb-6 flex flex-col gap-4">
        <SearchBar defaultValue={search ?? ""} />
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <FilterPanel
            categories={categoriesRes.categories}
            companies={companiesRes.items.map((c) => c.name)}
            selectedCategory={category}
            selectedCompany={company}
            selectedLocation={location}
          />
          <SortSelect value={sort} />
        </div>
      </div>

      <p className="mb-4 text-sm text-slate-500">
        {internshipsRes.total} internship{internshipsRes.total === 1 ? "" : "s"} found
      </p>

      {internshipsRes.items.length === 0 ? (
        <EmptyState />
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
