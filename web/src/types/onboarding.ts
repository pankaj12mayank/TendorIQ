export interface Plan {
  id: string;
  name: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  features: { name: string; included: boolean; limit?: string }[];
  recommended: boolean;
}

export interface ExpertiseCategory {
  expertise_areas: string[];
  industries: string[];
  company_sizes: string[];
  annual_tender_volumes: string[];
  average_contract_values: string[];
  target_regions: { id: string; name: string }[];
  certifications: string[];
}
