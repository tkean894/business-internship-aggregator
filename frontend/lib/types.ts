// Mirrors backend/api/schemas/*.py. Keep in sync with the FastAPI response models.

export type InternshipCategory =
  | "Product Management"
  | "Business Analytics"
  | "Finance"
  | "Accounting"
  | "Consulting"
  | "Marketing"
  | "Operations"
  | "Supply Chain"
  | "Strategy"
  | "Human Resources"
  | "Sales"
  | "Other";

export type InternshipSort = "posted_date_desc" | "last_seen_desc" | "company_name_asc" | "title_asc";

export interface CompanySummary {
  id: number;
  name: string;
  slug: string;
  career_url: string;
  website_url: string | null;
}

export interface CompanyOut {
  id: number;
  name: string;
  slug: string;
  career_url: string;
  website_url: string | null;
  is_active: boolean;
  active_internship_count: number;
}

export interface CompanyListResponse {
  items: CompanyOut[];
  total: number;
}

export interface InternshipBrief {
  id: number;
  title: string;
  category: InternshipCategory;
  location: string | null;
  employment_type: string;
  application_url: string;
  posted_date: string | null;
  is_active: boolean;
}

export interface CompanyDetail extends CompanyOut {
  internships: InternshipBrief[];
}

export interface InternshipOut {
  id: number;
  company: CompanySummary;
  title: string;
  description: string | null;
  category: InternshipCategory;
  location: string | null;
  employment_type: string;
  application_url: string;
  source_url: string;
  posted_date: string | null;
  application_deadline: string | null;
  first_seen_at: string;
  last_seen_at: string;
  is_active: boolean;
}

export interface InternshipListResponse {
  items: InternshipOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface CategoriesResponse {
  categories: string[];
}
