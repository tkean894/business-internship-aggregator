export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return dateString;
  return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

/**
 * "Posted today" / "Posted 2 days ago" / "Posted 3 weeks ago", etc.
 * Caller decides which timestamp to describe (see freshnessLabel below) -
 * this only knows how to phrase a relative distance, not which field
 * that distance should come from.
 */
function relativeDaysPhrase(daysAgo: number): string {
  if (daysAgo <= 0) return "today";
  if (daysAgo === 1) return "1 day ago";
  if (daysAgo < 7) return `${daysAgo} days ago`;
  const weeks = Math.floor(daysAgo / 7);
  if (weeks === 1) return "1 week ago";
  if (weeks < 5) return `${weeks} weeks ago`;
  const months = Math.floor(daysAgo / 30);
  if (months <= 1) return "1 month ago";
  return `${months} months ago`;
}

function daysSince(dateString: string): number {
  const then = new Date(dateString).getTime();
  if (Number.isNaN(then)) return NaN;
  return Math.floor((Date.now() - then) / (1000 * 60 * 60 * 24));
}

/**
 * Freshness copy for an internship card/detail page. Never invents a
 * posting date: if the source (`posted_date`) provided one, that's what
 * gets described as "Posted ...". If it didn't, freshness is described
 * from `first_seen_at` - when THIS aggregator discovered the listing -
 * phrased as "Discovered ..." so it's never confused with the source's
 * own posting date (see docs/architecture.md "Freshness").
 */
export function freshnessLabel(posted_date: string | null, first_seen_at: string): string {
  if (posted_date) {
    return `Posted ${relativeDaysPhrase(daysSince(posted_date))}`;
  }
  return `Discovered ${relativeDaysPhrase(daysSince(first_seen_at))}`;
}

const NEW_THRESHOLD_DAYS = 7;

/**
 * Whether to show a "New" badge. Deliberately based on `first_seen_at`
 * (when this aggregator first observed the listing) rather than
 * `posted_date`, since not every source provides a posting date, and
 * "new to this platform" is the one freshness signal every listing
 * always has (see docs/architecture.md "Freshness").
 */
export function isNewlyDiscovered(first_seen_at: string): boolean {
  const days = daysSince(first_seen_at);
  return !Number.isNaN(days) && days <= NEW_THRESHOLD_DAYS;
}
