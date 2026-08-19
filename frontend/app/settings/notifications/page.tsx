import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

import NotificationPreferencesForm from "@/components/NotificationPreferencesForm";
import { getCategories, getCompanies, getNotificationPreferences } from "@/lib/api";

export default async function NotificationSettingsPage() {
  const { userId, getToken } = await auth();
  if (!userId) {
    redirect("/sign-in");
  }
  const token = await getToken();
  if (!token) {
    redirect("/sign-in");
  }

  const [preferences, categoriesRes, companiesRes] = await Promise.all([
    getNotificationPreferences(token),
    getCategories(),
    getCompanies(),
  ]);
  const industries = Array.from(
    new Set(companiesRes.items.map((c) => c.industry).filter((i): i is string => Boolean(i))),
  ).sort();

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Notification Preferences</h1>
        <p className="mt-2 text-slate-600">
          Get emailed when a new internship matches your interests, or when a saved internship closes.
        </p>
      </header>

      <NotificationPreferencesForm initialPreferences={preferences} categories={categoriesRes.categories} industries={industries} />
    </main>
  );
}
