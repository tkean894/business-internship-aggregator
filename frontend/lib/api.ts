import type {
  CategoriesResponse,
  CompanyDetail,
  CompanyListResponse,
  InternshipCategory,
  InternshipListResponse,
  InternshipOut,
  InternshipSort,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class NotFoundError extends Error {}

export interface InternshipQuery {
  search?: string;
  category?: InternshipCategory;
  company?: string;
  location?: string;
  industry?: string;
  active?: boolean;
  sort?: InternshipSort;
  page?: number;
  page_size?: number;
}

function buildQueryString(params: Record<string, string | number | boolean | undefined>): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  }
  const qs = searchParams.toString();
  return qs ? `?${qs}` : "";
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    // Internship data changes as scrapers run - never serve a stale cached page.
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 404) {
      throw new NotFoundError(`Not found: ${path}`);
    }
    throw new Error(`API request to ${path} failed with status ${res.status}`);
  }
  return (await res.json()) as T;
}

export function getInternships(query: InternshipQuery): Promise<InternshipListResponse> {
  return apiFetch<InternshipListResponse>(`/internships${buildQueryString({ ...query })}`);
}

const FETCH_ALL_PAGE_SIZE = 100; // backend's MAX_PAGE_SIZE
const FETCH_ALL_SAFETY_CAP = 5; // stop after 500 items regardless of `total`

/**
 * Fetch every internship matching a query (ignoring `page`/`page_size`),
 * across as many backend pages as needed. Exists for the homepage's
 * USA-only display filter (see lib/location.ts): filtering a single
 * fetched page of results client-side can leave a page looking empty
 * even though later pages have real matches (a real bug reported after
 * shipping the page-at-a-time version - see git history). Pagination
 * has to run over the *filtered* set, which means having the whole
 * matching set in hand first.
 *
 * This is only safe at the platform's current scale (~100-200 active
 * internships, confirmed sub-second responses) - if the active dataset
 * grows into the thousands, replace this (and the client-side location
 * filter it supports) with a real backend-level location/country
 * filter instead of fetching everything per request.
 */
export async function getAllInternships(query: Omit<InternshipQuery, "page" | "page_size">): Promise<InternshipOut[]> {
  const items: InternshipOut[] = [];
  for (let page = 1; page <= FETCH_ALL_SAFETY_CAP; page++) {
    const res = await getInternships({ ...query, page, page_size: FETCH_ALL_PAGE_SIZE });
    items.push(...res.items);
    if (items.length >= res.total || res.items.length === 0) break;
  }
  return items;
}

export function getInternship(id: number): Promise<InternshipOut> {
  return apiFetch<InternshipOut>(`/internships/${id}`);
}

export function getCompanies(): Promise<CompanyListResponse> {
  return apiFetch<CompanyListResponse>(`/companies`);
}

export function getCompany(id: number): Promise<CompanyDetail> {
  return apiFetch<CompanyDetail>(`/companies/${id}`);
}

export function getCategories(): Promise<CategoriesResponse> {
  return apiFetch<CategoriesResponse>(`/categories`);
}
