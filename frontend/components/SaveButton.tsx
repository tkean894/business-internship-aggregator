"use client";

import { useClerk, useAuth } from "@clerk/nextjs";
import { useState, useTransition } from "react";

import { saveInternship, unsaveInternship } from "@/lib/api";

interface SaveButtonProps {
  internshipId: number;
  initialSaved: boolean;
  /** Small variant for cards in a list; a slightly larger one is used
   * on the detail page. Always deliberately less visually prominent
   * than the Apply button (Phase 9, Step 5) - outline style, never
   * the solid dark treatment Apply uses. */
  size?: "sm" | "md";
}

export default function SaveButton({ internshipId, initialSaved, size = "sm" }: SaveButtonProps) {
  const { isSignedIn, getToken } = useAuth();
  const { openSignIn } = useClerk();
  const [saved, setSaved] = useState(initialSaved);
  const [isPending, startTransition] = useTransition();

  function handleClick(e: React.MouseEvent) {
    // The button sits inside a card whose title is a "stretched link"
    // (see InternshipCard.tsx) - stop the click from also triggering
    // navigation to the detail page.
    e.preventDefault();
    e.stopPropagation();

    if (!isSignedIn) {
      openSignIn();
      return;
    }

    startTransition(async () => {
      const token = await getToken();
      if (!token) return;
      if (saved) {
        await unsaveInternship(internshipId, token);
        setSaved(false);
      } else {
        await saveInternship(internshipId, token);
        setSaved(true);
      }
    });
  }

  const sizeClasses = size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm";

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      aria-pressed={saved}
      className={`relative z-10 shrink-0 rounded-md border font-medium transition disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background ${sizeClasses} ${
        saved
          ? "border-border-strong bg-muted text-foreground hover:bg-border"
          : "border-border-strong bg-surface text-muted-foreground hover:bg-muted"
      }`}
    >
      {saved ? "Saved" : "Save"}
    </button>
  );
}
