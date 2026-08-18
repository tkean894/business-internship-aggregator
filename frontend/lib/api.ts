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
