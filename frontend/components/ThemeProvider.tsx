"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ComponentProps } from "react";

/** Thin re-export so app/layout.tsx (an async Server Component) can pass
 * its Server Component children through a Client Component boundary
 * without itself needing "use client". */
export default function ThemeProvider({ children, ...props }: ComponentProps<typeof NextThemesProvider>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
