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
// so this can safely share the same lookup/matching logic.
const CA_PROVINCE_ABBREVIATIONS = new Set([
  "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT",
]);

const NORTH_AMERICA_ABBREVIATIONS = new Set([
  ...US_STATE_ABBREVIATIONS,
  ...CA_PROVINCE_ABBREVIATIONS,
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

const NORTH_AMERICA_STATE_NAME_RE = new RegExp(
  `,\\s*(?:${[...US_STATE_NAMES, ...CA_PROVINCE_NAMES].join("|")})\\b`,
  "i",
);

const STATE_SUFFIX_RE = /,\s*([A-Za-z]{2})\b/g;

// PwC's Workday board (Phase 10 Step 2) exports many offices as a bare
// city name with no comma, province, or country at all - "Toronto",
// "Calgary", "Vancouver", "Montreal", "Ottawa" alongside equally bare
// "Milan", "Singapore", "Jakarta", etc. There's no general, reliable way
// to resolve an arbitrary bare city name to a country without a real
// gazetteer (out of scope here), but these five are real, recurring,
// unambiguous major-office cities actually observed in production data
// and internationally recognized enough that a bare mention of one
// (exact match, not substring) overwhelmingly means the Canadian city -
// e.g. "Vancouver" alone is Vancouver, BC in international business
// usage, not the much smaller Vancouver, WA. Deliberately a short,
// evidence-based list, not a general-purpose city lookup.
const BARE_CANADIAN_CITIES = new Set(["toronto", "calgary", "vancouver", "montreal", "ottawa"]);

/**
 * Best-effort classification of a scraped location string as US- or
 * Canada-based. Location text is free-form and varies wildly by ATS
 * (Greenhouse: "Austin, TX" / "London, United Kingdom"; Workday:
 * "United States - Illinois - Waukegan" / "Kuala Lumpur, AIA Digital+
 * Malaysia" / "Toronto, Ontario"; Lever: "Glendale, CA; Irvine, CA") -
 * there is no structured country field to filter on, so this is
 * necessarily a heuristic, not a guarantee.
 *
 * Included: a recognized "City, ST"/"City, Province" US or Canadian
 * abbreviation anywhere in the string, an explicit "United States" or
 * "Canada" mention, an exact bare match on one of a short list of
 * unambiguous major Canadian cities (see BARE_CANADIAN_CITIES), or a
 * bare "Remote" with no country qualifier (ambiguous, but deliberately
 * given the benefit of the doubt rather than hidden - see README). A
 * missing location is also included for the same reason.
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
  if (!location || !location.trim()) return true;

  const trimmed = location.trim();

  if (/^remote$/i.test(trimmed)) return true;
  if (/united states|canada|(?:^|[^a-z])usa(?:[^a-z]|$)/i.test(trimmed)) return true;
  if (NORTH_AMERICA_STATE_NAME_RE.test(trimmed)) return true;
  if (BARE_CANADIAN_CITIES.has(trimmed.toLowerCase())) return true;

  for (const match of trimmed.matchAll(STATE_SUFFIX_RE)) {
    if (NORTH_AMERICA_ABBREVIATIONS.has(match[1].toUpperCase())) return true;
  }

  return false;
}
