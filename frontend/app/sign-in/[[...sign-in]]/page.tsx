import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <main className="mx-auto flex max-w-5xl justify-center px-4 py-12">
      <SignIn />
    </main>
  );
}
