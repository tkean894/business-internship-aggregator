import type { InternshipOut } from "@/lib/types";

import InternshipCard from "./InternshipCard";

export default function InternshipList({ internships }: { internships: InternshipOut[] }) {
  return (
    <ul className="flex flex-col gap-3">
      {internships.map((internship) => (
        <li key={internship.id}>
          <InternshipCard internship={internship} />
        </li>
      ))}
    </ul>
  );
}
