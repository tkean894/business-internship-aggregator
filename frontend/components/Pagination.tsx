import Link from "next/link";

interface PaginationProps {
  total: number;
  page: number;
  pageSize: number;
  currentParams: Record<string, string | string[] | undefined>;
}

function hrefForPage(currentParams: Record<string, string | string[] | undefined>, page: number): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(currentParams)) {
    if (key === "page") continue;
    if (typeof value === "string" && value) params.set(key, value);
  }
  if (page > 1) params.set("page", String(page));
  const qs = params.toString();
  return qs ? `/?${qs}` : "/";
}

function getPageWindow(current: number, total: number): (number | "gap")[] {
  const pages: (number | "gap")[] = [];
  for (let p = 1; p <= total; p++) {
    if (p === 1 || p === total || Math.abs(p - current) <= 1) {
      pages.push(p);
    } else if (pages[pages.length - 1] !== "gap") {
      pages.push("gap");
    }
  }
  return pages;
}

export default function Pagination({ total, page, pageSize, currentParams }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  const pageWindow = getPageWindow(page, totalPages);

  return (
    <nav aria-label="Pagination" className="mt-8 flex items-center justify-center gap-1">
      <Link
        href={hrefForPage(currentParams, Math.max(1, page - 1))}
        aria-disabled={page === 1}
        tabIndex={page === 1 ? -1 : undefined}
        className={`rounded-md px-3 py-2 text-sm font-medium ${
          page === 1 ? "pointer-events-none text-slate-300" : "text-slate-700 hover:bg-slate-100"
        }`}
      >
        Previous
      </Link>

      {pageWindow.map((entry, idx) =>
        entry === "gap" ? (
          <span key={`gap-${idx}`} className="px-2 text-slate-400" aria-hidden="true">
            …
          </span>
        ) : (
          <Link
            key={entry}
            href={hrefForPage(currentParams, entry)}
            aria-current={entry === page ? "page" : undefined}
            className={`rounded-md px-3 py-2 text-sm font-medium ${
              entry === page ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            {entry}
          </Link>
        ),
      )}

      <Link
        href={hrefForPage(currentParams, Math.min(totalPages, page + 1))}
        aria-disabled={page === totalPages}
        tabIndex={page === totalPages ? -1 : undefined}
        className={`rounded-md px-3 py-2 text-sm font-medium ${
          page === totalPages ? "pointer-events-none text-slate-300" : "text-slate-700 hover:bg-slate-100"
        }`}
      >
        Next
      </Link>
    </nav>
  );
}
