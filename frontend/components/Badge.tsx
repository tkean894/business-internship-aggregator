type BadgeVariant = "new" | "inactive";

const VARIANT_STYLES: Record<BadgeVariant, string> = {
  new: "bg-success-bg text-success",
  inactive: "bg-warning-bg text-warning",
};

const VARIANT_LABEL: Record<BadgeVariant, string> = {
  new: "New",
  inactive: "No longer active",
};

/** Shared "New"/"No longer active" status pill - previously duplicated
 * verbatim across InternshipCard, CompanyStack, and the company/
 * internship detail pages. */
export default function Badge({ variant }: { variant: BadgeVariant }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${VARIANT_STYLES[variant]}`}>
      {VARIANT_LABEL[variant]}
    </span>
  );
}
