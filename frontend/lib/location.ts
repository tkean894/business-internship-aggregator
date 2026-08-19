// Every US state (plus DC and the major territories) as they appear
// abbreviated in "City, ST" style location strings, e.g. "Austin, TX".
const US_STATE_ABBREVIATIONS = new Set([
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
  "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
  "VA", "WA", "WV", "WI", "WY", "DC", "PR", "VI", "GU",
]);

// Some ATS exports spell the state out in full instead of abbreviating
// it (Workday in particular - e.g. "New York, New York", "Atlanta,
// Georgia" - found via real production data, not every "City, State"
// pair uses a two-letter code). Required to immediately follow a comma
// (like STATE_SUFFIX_RE below), NOT just appear as a bare word anywhere -
// a plain `\bCalifornia\b` check would wrongly match "Tijuana, Baja
// California, Mexico" (a real observed location - Baja California is a
// Mexican state, not the US one), since "Baja" sits between the comma
// and the word "California" there.
const US_STATE_NAMES = [
  "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
  "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
  "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
  "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
  "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
  "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
  "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
  "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
];
const STATE_NAME_RE = new RegExp(`,\\s*(?:${US_STATE_NAMES.join("|")})\\b`, "i");

const STATE_SUFFIX_RE = /,\s*([A-Za-z]{2})\b/g;

/**
 * Best-effort classification of a scraped location string as US-based.
 * Location text is free-form and varies wildly by ATS (Greenhouse:
 * "Austin, TX" / "London, United Kingdom"; Workday: "United States -
 * Illinois - Waukegan" / "Kuala Lumpur, AIA Digital+ Malaysia"; Lever:
 * "Glendale, CA; Irvine, CA") - there is no structured country field to
 * filter on, so this is necessarily a heuristic, not a guarantee.
 *
 * Included: a recognized "City, ST" US state/territory abbreviation
 * anywhere in the string, an explicit "United States" mention, or a
 * bare "Remote" with no country qualifier (ambiguous, but deliberately
 * given the benefit of the doubt rather than hidden - see README).
 * A missing location is also included for the same reason.
 * Excluded: everything else, including locations that are ambiguous in
 * a different way (e.g. "RL Headquarters", no recognizable signal at
 * all) - only the two cases above get the benefit of the doubt.
 *
 * Known false-positive risk: "Georgia" is both a US state and a
 * country (e.g. a hypothetical "Tbilisi, Georgia" would be misread as
 * US). Not currently present in this platform's data - if it ever is,
 * this heuristic will need a real disambiguation strategy, not a
 * one-off exclusion for that one city.
 */
export function isUsLocation(location: string | null | undefined): boolean {
  if (!location || !location.trim()) return true;

  const trimmed = location.trim();

  if (/^remote$/i.test(trimmed)) return true;
  if (/united states|(?:^|[^a-z])usa(?:[^a-z]|$)/i.test(trimmed)) return true;
  if (STATE_NAME_RE.test(trimmed)) return true;

  for (const match of trimmed.matchAll(STATE_SUFFIX_RE)) {
    if (US_STATE_ABBREVIATIONS.has(match[1].toUpperCase())) return true;
  }

  return false;
}
