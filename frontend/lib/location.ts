// Every US state (plus DC and the major territories) as they appear
// abbreviated in "City, ST" style location strings, e.g. "Austin, TX".
const US_STATE_ABBREVIATIONS = new Set([
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
  "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
  "VA", "WA", "WV", "WI", "WY", "DC", "PR", "VI", "GU",
]);

// Every Canadian province/territory abbreviation, same "City, XX" style
// (e.g. "Toronto, ON"). Added alongside US states so the platform can
// show both countries' internships together, per explicit product
// request - no overlap with the US set above (confirmed by inspection),
// so the two can be told apart by a plain Set lookup.
const CA_PROVINCE_ABBREVIATIONS = new Set([
  "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT",
]);

// Some ATS exports spell the state/province out in full instead of
// abbreviating it (Workday in particular - e.g. "New York, New York",
// "Atlanta, Georgia" - found via real production data, not every "City,
// State" pair uses a two-letter code). Required to immediately follow a
// comma (like STATE_SUFFIX_RE below), NOT just appear as a bare word
// anywhere - a plain `\bCalifornia\b` check would wrongly match
// "Tijuana, Baja California, Mexico" (a real observed location - Baja
// California is a Mexican state, not the US one), since "Baja" sits
// between the comma and the word "California" there.
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

// Canadian provinces/territories spelled out in full, same rationale as
// US_STATE_NAMES above (e.g. Workday's "Toronto, Ontario"). No name
// overlaps with a US state.
const CA_PROVINCE_NAMES = [
  "Alberta", "British Columbia", "Manitoba", "New Brunswick",
  "Newfoundland and Labrador", "Northwest Territories", "Nova Scotia", "Nunavut",
  "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Yukon",
];

const US_STATE_NAME_RE = new RegExp(`,\\s*(?:${US_STATE_NAMES.join("|")})\\b`, "i");
const CA_PROVINCE_NAME_RE = new RegExp(`,\\s*(?:${CA_PROVINCE_NAMES.join("|")})\\b`, "i");

const STATE_SUFFIX_RE = /,\s*([A-Za-z]{2})\b/g;

// Several ATS boards (PwC and GE Aerospace on Workday especially) export
// many offices as just a city name with no state/province/country at
// all - "Toronto", "Evendale", "Pittsburgh" - alongside equally bare
// "Milan", "Singapore", "Jakarta". A minority also pair a real city with
// a non-state suffix Workday couldn't be matched against above, e.g.
// Barclays' "New York, 745 7th Avenue" or "Toronto, Bay Wellington
// Tower L47" (a street address / building name, not a state code).
// There's no general, reliable way to resolve an arbitrary bare city
// name to a country without a real gazetteer (out of scope here), but
// these are real, recurring, unambiguous major-office cities actually
// observed in production data (verified against which company posted
// each - see this phase's completion report) and internationally
// recognized enough that a bare mention of one overwhelmingly means the
// city listed here, not a same-named smaller place - e.g. "Vancouver"
// alone is Vancouver, BC in international business usage, not the much
// smaller Vancouver, WA. Deliberately short, evidence-based lists, not
// a general-purpose city lookup - matched against the first comma-
// delimited segment (or the whole string if there's no comma), so both
// the bare and "City, non-state-suffix" forms are covered by one check.
const BARE_US_CITIES = new Set([
  "new york", "pittsburgh", "atlanta", "asheville", "livonia", "evendale", "springdale",
]);
const BARE_CANADIAN_CITIES = new Set(["toronto", "calgary", "vancouver", "montreal", "ottawa", "halifax"]);

function firstSegment(trimmed: string): string {
  const commaIndex = trimmed.indexOf(",");
  return (commaIndex === -1 ? trimmed : trimmed.slice(0, commaIndex)).trim().toLowerCase();
}

// A bare "Remote" with no country qualifier, or a missing location
// entirely, is genuinely ambiguous - could be either country (or
// neither). Given the benefit of the doubt for both individual-country
// checks below, not just the combined one, rather than hidden - see
// README and isUsOrCanadaLocation's own docstring for the general
// policy this follows.
function isAmbiguousButIncluded(trimmed: string): boolean {
  return trimmed === "" || /^remote$/i.test(trimmed);
}

/**
 * Best-effort classification of a scraped location string as US-based
 * specifically (see isCanadaLocation for the Canada-only equivalent,
 * and isUsOrCanadaLocation for their union - the general "show both
 * countries" display filter used across most of the platform). Exists
 * so the location filter dropdown can offer a "United States" / "Canada"
 * option in addition to specific cities/states (see
 * US_LOCATION_FILTER_VALUE / CANADA_LOCATION_FILTER_VALUE below).
 */
export function isUsLocation(location: string | null | undefined): boolean {
  const trimmed = (location ?? "").trim();
  if (isAmbiguousButIncluded(trimmed)) return true;

  if (/united states|(?:^|[^a-z])usa(?:[^a-z]|$)/i.test(trimmed)) return true;
  if (US_STATE_NAME_RE.test(trimmed)) return true;
  if (BARE_US_CITIES.has(firstSegment(trimmed))) return true;

  for (const match of trimmed.matchAll(STATE_SUFFIX_RE)) {
    if (US_STATE_ABBREVIATIONS.has(match[1].toUpperCase())) return true;
  }

  return false;
}

/** Canada-only equivalent of isUsLocation - see its docstring. */
export function isCanadaLocation(location: string | null | undefined): boolean {
  const trimmed = (location ?? "").trim();
  if (isAmbiguousButIncluded(trimmed)) return true;

  if (/canada/i.test(trimmed)) return true;
  if (CA_PROVINCE_NAME_RE.test(trimmed)) return true;
  if (BARE_CANADIAN_CITIES.has(firstSegment(trimmed))) return true;

  for (const match of trimmed.matchAll(STATE_SUFFIX_RE)) {
    if (CA_PROVINCE_ABBREVIATIONS.has(match[1].toUpperCase())) return true;
  }

  return false;
}

/**
 * Best-effort classification of a scraped location string as US- or
 * Canada-based. Location text is free-form and varies wildly by ATS
 * (Greenhouse: "Austin, TX" / "London, United Kingdom"; Workday:
 * "United States - Illinois - Waukegan" / "Kuala Lumpur, AIA Digital+
 * Malaysia" / "Toronto, Ontario"; Lever: "Glendale, CA; Irvine, CA") -
 * there is no structured country field to filter on, so this is
 * necessarily a heuristic, not a guarantee.
 *
 * Included: anything isUsLocation or isCanadaLocation individually
 * would include (a recognized "City, ST"/"City, Province" abbreviation
 * anywhere in the string, an explicit "United States"/"USA"/"Canada"
 * mention, a match on one of a short list of unambiguous major US/
 * Canadian cities (BARE_US_CITIES/BARE_CANADIAN_CITIES), or a bare
 * "Remote"/missing location).
 * Excluded: everything else, including locations that are ambiguous in
 * a different way (e.g. "RL Headquarters", no recognizable signal at
 * all) - only the cases above get the benefit of the doubt.
 *
 * Known false-positive risk: "Georgia" is both a US state and a
 * country (e.g. a hypothetical "Tbilisi, Georgia" would be misread as
 * US). Not currently present in this platform's data - if it ever is,
 * this heuristic will need a real disambiguation strategy, not a
 * one-off exclusion for that one city.
 */
export function isUsOrCanadaLocation(location: string | null | undefined): boolean {
  return isUsLocation(location) || isCanadaLocation(location);
}

// Reserved sentinel values for the location filter dropdown's "United
// States" / "Canada" options (FilterPanel.tsx), distinct from any real
// scraped location string so they can never collide with one (confirmed
// no current data is literally just "United States" or "Canada" with
// nothing else, but a reserved token is correct regardless of today's
// data). The homepage (app/(home)/page.tsx) recognizes these and
// applies isUsLocation/isCanadaLocation instead of an exact-match
// backend query when one is selected.
export const US_LOCATION_FILTER_VALUE = "__country_us__";
export const CANADA_LOCATION_FILTER_VALUE = "__country_ca__";

const LOCATION_FILTER_LABELS: Record<string, string> = {
  [US_LOCATION_FILTER_VALUE]: "United States",
  [CANADA_LOCATION_FILTER_VALUE]: "Canada",
};

/** Human-readable label for a location filter value - a real location
 * string as-is, or the friendly country name for a sentinel value. */
export function locationFilterLabel(location: string): string {
  return LOCATION_FILTER_LABELS[location] ?? location;
}
