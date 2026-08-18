import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Business Internship Aggregator",
  description: "Search business internships across companies, functions, and locations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased">
        <div className="min-h-screen">
          <nav className="border-b border-slate-200 bg-white">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
              <Link href="/" className="text-sm font-bold tracking-tight text-slate-900">
                Business Internship Aggregator
              </Link>
            </div>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
