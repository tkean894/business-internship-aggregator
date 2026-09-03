import { isPostedWithinOneDay } from "@/lib/format";
import type { InternshipOut } from "@/lib/types";

import CompanyStack from "./CompanyStack";
import InternshipCard from "./InternshipCard";

type RenderItem =
  | { kind: "single"; key: string; internship: InternshipOut }
  | { kind: "stack"; key: string; companyName: string; items: InternshipOut[] };

/**
 * Groups postings from the same company into a single collapsed stack
 * when 2+ of them are all visible in `internships` (the current page's
 * filtered/sorted results), so a company with many open roles doesn't
 * dominate the list. Any listing first seen within the last day breaks
 * out as its own card instead of disappearing into a stack (see
 * lib/format.ts `isPostedWithinOneDay`), so a brand-new posting is never
 * buried. A company with only one non-fresh posting isn't wrapped in a
 * stack at all - there's nothing to collapse.
 *
 * Order is otherwise preserved: each render item takes the position of
 * its first occurrence in `internships`, so the current sort order
 * (including the order postings appear inside an expanded stack) is
 * unaffected.
 */
function buildRenderItems(internships: InternshipOut[]): RenderItem[] {
  const stackableByCompany = new Map<number, InternshipOut[]>();
  for (const internship of internships) {
    if (isPostedWithinOneDay(internship.first_seen_at)) continue;
    const list = stackableByCompany.get(internship.company.id) ?? [];
    list.push(internship);
    stackableByCompany.set(internship.company.id, list);
  }

  const renderItems: RenderItem[] = [];
  const stackedCompanyIds = new Set<number>();

  for (const internship of internships) {
    if (isPostedWithinOneDay(internship.first_seen_at)) {
      renderItems.push({ kind: "single", key: `internship-${internship.id}`, internship });
      continue;
    }

    const stackable = stackableByCompany.get(internship.company.id)!;
    if (stackable.length < 2) {
      renderItems.push({ kind: "single", key: `internship-${internship.id}`, internship });
      continue;
    }

    if (stackedCompanyIds.has(internship.company.id)) continue; // already rendered as part of the stack

    stackedCompanyIds.add(internship.company.id);
    renderItems.push({
      kind: "stack",
      key: `stack-${internship.company.id}`,
      companyName: internship.company.name,
      items: stackable,
    });
  }

  return renderItems;
}

export default function InternshipList({ internships }: { internships: InternshipOut[] }) {
  const renderItems = buildRenderItems(internships);

  return (
    <ul className="flex flex-col gap-3">
      {renderItems.map((item) => (
        <li key={item.key}>
          {item.kind === "single" ? (
            <InternshipCard internship={item.internship} />
          ) : (
            <CompanyStack companyName={item.companyName} items={item.items} />
          )}
        </li>
      ))}
    </ul>
  );
}
