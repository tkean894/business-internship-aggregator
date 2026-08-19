import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <main className="mx-auto flex max-w-5xl justify-center px-4 py-12">
      <SignUp />
    </main>
  );
}
