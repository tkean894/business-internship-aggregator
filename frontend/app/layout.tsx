import { ClerkProvider, SignInButton, UserButton } from "@clerk/nextjs";
import { auth } from "@clerk/nextjs/server";
import type { Metadata } from "next";
import Link from "next/link";

import ThemeProvider from "@/components/ThemeProvider";
import ThemeToggle from "@/components/ThemeToggle";

import "./globals.css";

export const metadata: Metadata = {
  title: "Business Internship Aggregator",
  description: "Search business internships across companies, functions, and locations.",
};

const NAV_LINK =
  "text-sm font-medium text-muted-foreground hover:text-foreground hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded-sm";

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Checked server-side (rather than the <SignedIn>/<SignedOut> client
  // components) so the nav renders correctly on first paint with no
  // client-side auth-state flash - also sidesteps a runtime
  // incompatibility those two components hit under the installed
  // Clerk version ("Core 3").
  const { userId } = await auth();

  return (
    <ClerkProvider
      afterSignOutUrl="/"
      appearance={{
        variables: {
          colorPrimary: "#0d9488",
          colorForeground: "#1c1917",
          colorBackground: "#ffffff",
          colorInput: "#ffffff",
          colorInputForeground: "#1c1917",
          borderRadius: "0.375rem",
        },
        elements: {
          formButtonPrimary: "bg-accent-solid hover:bg-accent-solid-hover text-accent-foreground",
          footerActionLink: "text-accent hover:text-accent-solid",
          card: "shadow-sm border border-border",
        },
      }}
    >
      <html lang="en" suppressHydrationWarning>
        <body className="bg-background text-foreground antialiased">
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <div className="min-h-screen">
              <nav className="border-b border-border bg-surface">
                <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
                  <Link
                    href="/"
                    className="rounded-sm text-sm font-bold tracking-tight text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  >
                    Business Internship Aggregator
                  </Link>
                  <div className="flex items-center gap-4">
                    <Link href="/companies" className={NAV_LINK}>
                      Companies
                    </Link>
                    {userId ? (
                      <>
                        <Link href="/saved" className={NAV_LINK}>
                          Saved
                        </Link>
                        <Link href="/settings/notifications" className={NAV_LINK}>
                          Notifications
                        </Link>
                        <ThemeToggle />
                        <UserButton />
                      </>
                    ) : (
                      <>
                        <ThemeToggle />
                        <SignInButton mode="modal">
                          <button
                            type="button"
                            className="rounded-md border border-border-strong px-3 py-1.5 text-sm font-medium text-foreground hover:bg-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                          >
                            Sign in
                          </button>
                        </SignInButton>
                      </>
                    )}
                  </div>
                </div>
              </nav>
              {children}
            </div>
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
