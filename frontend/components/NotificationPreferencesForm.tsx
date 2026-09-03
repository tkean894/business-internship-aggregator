"use client";

import { useAuth } from "@clerk/nextjs";
import { useState } from "react";

import { updateNotificationPreferences } from "@/lib/api";
import type { InternshipCategory, NotificationFrequency, NotificationPreferenceOut } from "@/lib/types";

const FREQUENCY_OPTIONS: { value: NotificationFrequency; label: string }[] = [
  { value: "off", label: "Off" },
  { value: "immediate", label: "Immediately (next scraper run, up to every 6 hours)" },
  { value: "daily", label: "Daily digest" },
  { value: "weekly", label: "Weekly digest" },
];

const FOCUS_RING =
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background";

interface NotificationPreferencesFormProps {
  initialPreferences: NotificationPreferenceOut;
  categories: string[];
  industries: string[];
}

export default function NotificationPreferencesForm({
  initialPreferences,
  categories,
  industries,
}: NotificationPreferencesFormProps) {
  const { getToken } = useAuth();
  const [emailEnabled, setEmailEnabled] = useState(initialPreferences.email_enabled);
  const [frequency, setFrequency] = useState<NotificationFrequency>(initialPreferences.frequency);
  const [selectedCategories, setSelectedCategories] = useState<string[]>(initialPreferences.categories);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>(initialPreferences.industries);
  const [locationsText, setLocationsText] = useState(initialPreferences.locations.join(", "));
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  function toggle(list: string[], value: string, setList: (v: string[]) => void) {
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("saving");
    const token = await getToken();
    if (!token) {
      setStatus("error");
      return;
    }
    const locations = locationsText
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      await updateNotificationPreferences(
        {
          email_enabled: emailEnabled,
          frequency,
          categories: selectedCategories as InternshipCategory[],
          industries: selectedIndustries,
          locations,
        },
        token,
      );
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <label className="flex items-center gap-2 text-sm font-medium text-foreground">
        <input
          type="checkbox"
          checked={emailEnabled}
          onChange={(e) => setEmailEnabled(e.target.checked)}
          className={`h-4 w-4 rounded border-border-strong text-accent-solid ${FOCUS_RING}`}
        />
        Email notifications enabled
      </label>

      <div>
        <label htmlFor="frequency" className="block text-sm font-medium text-foreground">
          Frequency
        </label>
        <select
          id="frequency"
          value={frequency}
          onChange={(e) => setFrequency(e.target.value as NotificationFrequency)}
          className={`mt-1 w-full rounded-md border border-border-strong bg-surface px-3 py-2 text-sm text-foreground sm:w-auto ${FOCUS_RING} focus-visible:border-accent`}
        >
          {FREQUENCY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <fieldset>
        <legend className="text-sm font-medium text-foreground">Categories (leave all unchecked for any category)</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {categories.map((category) => (
            <label
              key={category}
              className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition peer-focus-visible:ring-2 peer-focus-visible:ring-accent peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-background ${
                selectedCategories.includes(category)
                  ? "border-accent-solid bg-accent-solid text-accent-foreground"
                  : "border-border-strong bg-surface text-foreground hover:border-accent"
              }`}
            >
              <input
                type="checkbox"
                className="peer sr-only"
                checked={selectedCategories.includes(category)}
                onChange={() => toggle(selectedCategories, category, setSelectedCategories)}
              />
              {category}
            </label>
          ))}
        </div>
      </fieldset>

      {industries.length > 0 && (
        <fieldset>
          <legend className="text-sm font-medium text-foreground">Industries (leave all unchecked for any industry)</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {industries.map((industry) => (
              <label
                key={industry}
                className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition peer-focus-visible:ring-2 peer-focus-visible:ring-accent peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-background ${
                  selectedIndustries.includes(industry)
                    ? "border-accent-solid bg-accent-solid text-accent-foreground"
                    : "border-border-strong bg-surface text-foreground hover:border-accent"
                }`}
              >
                <input
                  type="checkbox"
                  className="peer sr-only"
                  checked={selectedIndustries.includes(industry)}
                  onChange={() => toggle(selectedIndustries, industry, setSelectedIndustries)}
                />
                {industry}
              </label>
            ))}
          </div>
        </fieldset>
      )}

      <div>
        <label htmlFor="locations" className="block text-sm font-medium text-foreground">
          Locations (optional, comma-separated - leave blank for any location)
        </label>
        <input
          id="locations"
          type="text"
          value={locationsText}
          onChange={(e) => setLocationsText(e.target.value)}
          placeholder="e.g. Austin, TX, Washington, DC"
          className={`mt-1 w-full rounded-md border border-border-strong px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground ${FOCUS_RING} focus-visible:border-accent`}
        />
      </div>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={status === "saving"}
          className={`rounded-md bg-accent-solid px-5 py-2.5 text-sm font-semibold text-accent-foreground hover:bg-accent-solid-hover disabled:opacity-60 ${FOCUS_RING}`}
        >
          {status === "saving" ? "Saving..." : "Save preferences"}
        </button>
        {status === "saved" && <span className="text-sm text-success">Saved.</span>}
        {status === "error" && <span className="text-sm text-danger">Something went wrong. Try again.</span>}
      </div>
    </form>
  );
}
