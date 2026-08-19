import type {
  CategoriesResponse,
  CompanyDetail,
  CompanyListResponse,
  InternshipCategory,
  InternshipListResponse,
  InternshipOut,
  InternshipSort,
  NotificationPreferenceOut,
  NotificationPreferenceUpdate,
  SavedInternshipListResponse,
  UserOut,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class NotFoundError extends Error {}
export class UnauthorizedError extends Error {}

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

interface ApiFetchOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  /** Clerk session token - server components get this via `auth().getToken()`,
   * client components via the `useAuth()` hook. Omitted entirely for
   * anonymous requests, which is a normal, expected state (Phase 9). */
  token?: string | null;
}

async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T | null> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token) headers["Authorization"] = `Bearer ${options.token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    // Internship/user data changes frequently - never serve a stale cached page.
    cache: "no-store",
  });

  if (!res.ok) {
    if (res.status === 404) throw new NotFoundError(`Not found: ${path}`);
    if (res.status === 401) throw new UnauthorizedError(`Unauthorized: ${path}`);
    throw new Error(`API request to ${path} failed with status ${res.status}`);
  }
  if (res.status === 204) return null;
  return (await res.json()) as T;
}

export function getInternships(query: InternshipQuery, token?: string | null): Promise<InternshipListResponse> {
  return apiFetch<InternshipListResponse>(`/internships${buildQueryString({ ...query })}`, { token }) as Promise<InternshipListResponse>;
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
export async function getAllInternships(
  query: Omit<InternshipQuery, "page" | "page_size">,
  token?: string | null,
): Promise<InternshipOut[]> {
  const items: InternshipOut[] = [];
  for (let page = 1; page <= FETCH_ALL_SAFETY_CAP; page++) {
    const res = await getInternships({ ...query, page, page_size: FETCH_ALL_PAGE_SIZE }, token);
    items.push(...res.items);
    if (items.length >= res.total || res.items.length === 0) break;
  }
  return items;
}

export function getInternship(id: number, token?: string | null): Promise<InternshipOut> {
  return apiFetch<InternshipOut>(`/internships/${id}`, { token }) as Promise<InternshipOut>;
}

export function saveInternship(id: number, token: string): Promise<void> {
  return apiFetch(`/internships/${id}/save`, { method: "POST", token }) as Promise<void>;
}

export function unsaveInternship(id: number, token: string): Promise<void> {
  return apiFetch(`/internships/${id}/save`, { method: "DELETE", token }) as Promise<void>;
}

export function getCompanies(): Promise<CompanyListResponse> {
  return apiFetch<CompanyListResponse>(`/companies`) as Promise<CompanyListResponse>;
}

export function getCompany(id: number): Promise<CompanyDetail> {
  return apiFetch<CompanyDetail>(`/companies/${id}`) as Promise<CompanyDetail>;
}

export function getCategories(): Promise<CategoriesResponse> {
  return apiFetch<CategoriesResponse>(`/categories`) as Promise<CategoriesResponse>;
}

export function getMe(token: string): Promise<UserOut> {
  return apiFetch<UserOut>(`/me`, { token }) as Promise<UserOut>;
}

export function getSavedInternships(token: string): Promise<SavedInternshipListResponse> {
  return apiFetch<SavedInternshipListResponse>(`/me/saved`, { token }) as Promise<SavedInternshipListResponse>;
}

export function getNotificationPreferences(token: string): Promise<NotificationPreferenceOut> {
  return apiFetch<NotificationPreferenceOut>(`/me/notification-preferences`, { token }) as Promise<NotificationPreferenceOut>;
}

export function updateNotificationPreferences(
  update: NotificationPreferenceUpdate,
  token: string,
): Promise<NotificationPreferenceOut> {
  return apiFetch<NotificationPreferenceOut>(`/me/notification-preferences`, {
    method: "PUT",
    body: update,
    token,
  }) as Promise<NotificationPreferenceOut>;
}
