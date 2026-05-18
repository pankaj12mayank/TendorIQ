export interface ConfidenceScore {
  value: number;
  label: string;
  factors: string[];
}

export interface SummaryData {
  title: string;
  referenceNumber: string;
  organization: string;
  category: string;
  value: string;
  description: string;
  confidence: ConfidenceScore;
  keyHighlights: string[];
  concerns: string[];
}

export interface EligibilityCriteria {
  id: string;
  criterion: string;
  requirement: string;
  isMet: boolean | null;
  notes?: string;
  confidence: number;
}

export interface EligibilityData {
  overallScore: number;
  overallConfidence: ConfidenceScore;
  criteria: EligibilityCriteria[];
  summary: string;
}

export interface TechnicalRequirement {
  id: string;
  name: string;
  specification: string;
  isCompliant: boolean | null;
  notes?: string;
  weight: number;
}

export interface TechnicalData {
  overallScore: number;
  overallConfidence: ConfidenceScore;
  requirements: TechnicalRequirement[];
  complianceRate: number;
  summary: string;
}

export interface CostBreakdown {
  item: string;
  amount: number;
  unit: string;
  quantity: number;
  total: number;
}

export interface FinancialData {
  totalValue: string;
  currency: string;
  breakdown: CostBreakdown[];
  paymentTerms: string;
  advances: { type: string; percentage: number }[];
  overallConfidence: ConfidenceScore;
  summary: string;
}

export interface RiskItem {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  probability: number;
  impact: string;
  mitigation: string;
  owner?: string;
}

export interface RisksData {
  overallRiskScore: number;
  risks: RiskItem[];
  overallConfidence: ConfidenceScore;
  summary: string;
}

export interface DeadlineItem {
  id: string;
  name: string;
  date: string;
  type: 'submission' | 'clarification' | 'presentation' | 'contract' | 'other';
  isMet: boolean | null;
  daysRemaining: number;
  notes?: string;
}

export interface DeadlinesData {
  deadlines: DeadlineItem[];
  earliestDeadline: string;
  overallConfidence: ConfidenceScore;
  summary: string;
}

export interface DocumentRequirement {
  id: string;
  name: string;
  description: string;
  isRequired: boolean;
  isSubmitted: boolean | null;
  submittedDate?: string;
  documentType: string;
  pageLimit?: number;
  notes?: string;
  confidence: number;
}

export interface MandatoryDocsData {
  overallCompletion: number;
  documents: DocumentRequirement[];
  overallConfidence: ConfidenceScore;
  summary: string;
}

export interface TenderAnalysis {
  tenderId: string;
  summary: SummaryData;
  eligibility: EligibilityData;
  technical: TechnicalData;
  financial: FinancialData;
  risks: RisksData;
  deadlines: DeadlinesData;
  mandatoryDocs: MandatoryDocsData;
  createdAt: string;
  updatedAt: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export type AnalysisSection = 
  | 'summary' 
  | 'eligibility' 
  | 'technical' 
  | 'financial' 
  | 'risks' 
  | 'deadlines' 
  | 'mandatory_docs';

export interface EditState {
  section: AnalysisSection | null;
  fieldId: string | null;
  originalValue: unknown;
  newValue: unknown;
}

export interface ExportOptions {
  format: 'pdf' | 'docx' | 'json' | 'csv';
  includeSections: AnalysisSection[];
  includeMetadata: boolean;
  includeConfidence: boolean;
}