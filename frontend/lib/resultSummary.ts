import type { InternshipOut } from "./types";

export interface ResultSummary {
  count: number;
  companyCount: number;
  categoryCount: number;
}

/**
 * Summarizes an already-filtered list of internships for display (the
 * "X internships across Y companies and Z categories" hero stat on the
 * homepage - see app/(home)/page.tsx). Deliberately takes the complete
 * filtered result set, not a paginated page of it - callers must pass
 * the full array (e.g. `naInternships`, computed before pagination
 * slicing) so pagination and sort order never affect these counts:
 * `.slice()` changes which items appear in a page but not this
 * function's input, and Set-based distinct counting is order-independent.
 *
 * Deliberately NOT a second, separate filtering pass - it only counts
 * what's already been filtered upstream (backend query + the client-side
 * US/Canada geography heuristic in lib/location.ts), so this can never
 * disagree with what the results list actually shows.
 */
export function summarizeInternships(internships: InternshipOut[]): ResultSummary {
  const companyIds = new Set(internships.map((i) => i.company.id));
  const categories = new Set(internships.map((i) => i.category));
  return {
    count: internships.length,
    companyCount: companyIds.size,
    categoryCount: categories.size,
  };
}
