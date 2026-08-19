import { clerkMiddleware } from "@clerk/nextjs/server";

// No routes are forced through Clerk's own auth gate here - anonymous
// browsing must keep working everywhere (Phase 9 requirement). This
// middleware only makes auth state available to server components/
// route handlers; actual protection happens per-endpoint in FastAPI
// (see backend/api/auth.py) and per-page in the frontend (redirecting
// signed-out users away from /saved and /settings/notifications).
export default clerkMiddleware();

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/(api|trpc)(.*)"],
};
