import { ClerkProvider, SignInButton, UserButton } from "@clerk/nextjs";
import { auth } from "@clerk/nextjs/server";
import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Business Internship Aggregator",
  description: "Search business internships across companies, functions, and locations.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Checked server-side (rather than the <SignedIn>/<SignedOut> client
  // components) so the nav renders correctly on first paint with no
  // client-side auth-state flash - also sidesteps a runtime
  // incompatibility those two components hit under the installed
  // Clerk version ("Core 3").
  const { userId } = await auth();

  return (
    <ClerkProvider afterSignOutUrl="/">
      <html lang="en">
        <body className="bg-slate-50 text-slate-900 antialiased">
          <div className="min-h-screen">
            <nav className="border-b border-slate-200 bg-white">
              <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
                <Link href="/" className="text-sm font-bold tracking-tight text-slate-900">
                  Business Internship Aggregator
                </Link>
                <div className="flex items-center gap-4">
                  <Link href="/companies" className="text-sm font-medium text-slate-600 hover:text-slate-900 hover:underline">
                    Companies
                  </Link>
                  {userId ? (
                    <>
                      <Link href="/saved" className="text-sm font-medium text-slate-600 hover:text-slate-900 hover:underline">
                        Saved
                      </Link>
                      <Link
                        href="/settings/notifications"
                        className="text-sm font-medium text-slate-600 hover:text-slate-900 hover:underline"
                      >
                        Notifications
                      </Link>
                      <UserButton />
                    </>
                  ) : (
                    <SignInButton mode="modal">
                      <button
                        type="button"
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Sign in
                      </button>
                    </SignInButton>
                  )}
                </div>
              </div>
            </nav>
            {children}
          </div>
        </body>
      </html>
    </ClerkProvider>
  );
}
