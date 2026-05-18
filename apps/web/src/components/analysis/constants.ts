import { 
  TenderAnalysis, 
  SummaryData, 
  EligibilityData, 
  TechnicalData,
  FinancialData,
  RisksData,
  DeadlinesData,
  MandatoryDocsData 
} from './types';

export const MOCK_SUMMARY: SummaryData = {
  title: 'IT Infrastructure Modernization Project',
  referenceNumber: 'IIT-2026-001',
  organization: 'Department of Information Technology',
  category: 'IT Services',
  value: '$2,500,000',
  description: 'Comprehensive modernization of enterprise IT infrastructure including cloud migration, network upgrades, and security enhancements for government agencies.',
  confidence: {
    value: 92,
    label: 'High Confidence',
    factors: [
      'Complete document provided',
      'Clear specifications',
      'Standard evaluation criteria'
    ]
  },
  keyHighlights: [
    'Multi-year contract opportunity',
    'Government guaranteed payment',
    'Clear technical roadmap',
    'Established compliance requirements'
  ],
  concerns: [
    'Tight implementation timeline',
    'Complex integration requirements',
    'Limited vendor pre-qualification period'
  ]
};

export const MOCK_ELIGIBILITY: EligibilityData = {
  overallScore: 78,
  overallConfidence: { value: 85, label: 'High Confidence', factors: ['Standard criteria', 'Verifiable requirements'] },
  criteria: [
    { id: '1', criterion: 'ISO 27001 Certification', requirement: 'Valid ISO 27001:2022 certification required', isMet: true, notes: 'Certification verified up to 2027', confidence: 95 },
    { id: '2', criterion: 'Minimum Experience', requirement: '5+ years in government IT projects', isMet: true, notes: 'Company has 12 years experience', confidence: 90 },
    { id: '3', criterion: 'Financial Stability', requirement: 'Minimum annual turnover of $1M', isMet: true, confidence: 88 },
    { id: '4', criterion: 'Local Office', requirement: 'Operational office in target region', isMet: null, notes: 'Requires verification', confidence: 60 },
    { id: '5', criterion: 'Insurance Coverage', requirement: 'Professional liability insurance minimum $2M', isMet: true, confidence: 95 },
    { id: '6', criterion: 'Team Qualifications', requirement: 'PMP certified project manager', isMet: true, confidence: 92 }
  ],
  summary: 'Your organization meets 5 out of 6 eligibility criteria. The local office requirement needs verification.'
};

export const MOCK_TECHNICAL: TechnicalData = {
  overallScore: 72,
  overallConfidence: { value: 88, label: 'High Confidence', factors: ['Detailed specifications', 'Clear compliance matrix'] },
  requirements: [
    { id: '1', name: 'Cloud Platform', specification: 'AWS or Azure certified', isCompliant: true, weight: 15, notes: 'AWS Advanced Partner' },
    { id: '2', name: 'Security Standards', specification: 'FedRAMP Moderate equivalent', isCompliant: true, weight: 20, notes: 'SOC 2 Type II certified' },
    { id: '3', name: 'Data Migration', specification: 'Zero-downtime migration capability', isCompliant: null, weight: 18, notes: 'Requires demonstration' },
    { id: '4', name: 'Integration API', specification: 'RESTful APIs with OpenAPI 3.0', isCompliant: true, weight: 12 },
    { id: '5', name: 'Disaster Recovery', specification: 'RPO < 4 hours, RTO < 8 hours', isCompliant: true, weight: 15 },
    { id: '6', name: 'Scalability', specification: 'Support 10x current load', isCompliant: null, weight: 10, notes: 'Needs capacity planning' },
    { id: '7', name: 'Compliance Reporting', specification: 'Automated audit trails', isCompliant: true, weight: 10 }
  ],
  complianceRate: 71,
  summary: 'Strong technical foundation with 5/7 requirements fully met. Two items need additional documentation.'
};

export const MOCK_FINANCIAL: FinancialData = {
  totalValue: '$2,500,000',
  currency: 'USD',
  breakdown: [
    { item: 'Cloud Infrastructure', amount: 850000, unit: 'lump', quantity: 1, total: 850000 },
    { item: 'Migration Services', amount: 450000, unit: 'hourly', quantity: 2000, total: 450000 },
    { item: 'Training & Support', amount: 200000, unit: 'lump', quantity: 1, total: 200000 },
    { item: 'Software Licenses', amount: 300000, unit: 'annual', quantity: 3, total: 900000 },
    { item: 'Contingency', amount: 100000, unit: 'lump', quantity: 1, total: 100000 }
  ],
  paymentTerms: 'Monthly progress payments based on milestones',
  advances: [
    { type: 'Mobilization', percentage: 15 },
    { type: 'Equipment', percentage: 10 }
  ],
  overallConfidence: { value: 90, label: 'High Confidence', factors: ['Detailed cost breakdown', 'Standard payment terms'] },
  summary: 'Budget allocation is reasonable with 15% mobilization advance available.'
};

export const MOCK_RISKS: RisksData = {
  overallRiskScore: 45,
  overallConfidence: { value: 82, label: 'High Confidence', factors: ['Comprehensive risk assessment', 'Clear mitigation plans'] },
  risks: [
    {
      id: '1',
      title: 'Integration Complexity',
      description: 'Legacy system integration may require additional development time',
      severity: 'high',
      probability: 70,
      impact: 'Potential 20% timeline extension',
      mitigation: 'Early engagement with legacy system owners; phased integration approach'
    },
    {
      id: '2',
      title: 'Resource Availability',
      description: 'Limited availability of certified cloud architects in region',
      severity: 'medium',
      probability: 50,
      impact: 'Slower deployment but manageable',
      mitigation: 'Partner with staffing agency; remote team options'
    },
    {
      id: '3',
      title: 'Scope Creep',
      description: 'Unclear requirements may lead to change requests',
      severity: 'medium',
      probability: 60,
      impact: 'Budget impact of 10-15%',
      mitigation: 'Detailed scope documentation; formal change request process'
    },
    {
      id: '4',
      title: 'Data Security Breach',
      description: 'Risk during migration phase when data is in transit',
      severity: 'critical',
      probability: 15,
      impact: 'Regulatory penalties and reputational damage',
      mitigation: 'End-to-end encryption; SOC 2 compliance; regular security audits'
    },
    {
      id: '5',
      title: 'Vendor Lock-in',
      description: 'Dependence on specific cloud provider may limit future flexibility',
      severity: 'low',
      probability: 40,
      impact: 'Long-term cost implications',
      mitigation: 'Multi-cloud strategy; portable architecture design'
    }
  ],
  summary: '5 risks identified with 1 critical (data security) and 1 high (integration complexity). Mitigation plans in place.'
};

export const MOCK_DEADLINES: DeadlinesData = {
  deadlines: [
    { id: '1', name: 'Proposal Submission', date: '2026-06-15', type: 'submission', isMet: null, daysRemaining: 28 },
    { id: '2', name: 'Technical Demonstration', date: '2026-06-10', type: 'presentation', isMet: true, daysRemaining: 23 },
    { id: '3', name: 'Clarification Request Deadline', date: '2026-05-25', type: 'clarification', isMet: null, daysRemaining: 7 },
    { id: '4', name: 'Contract Award', date: '2026-07-01', type: 'contract', isMet: null, daysRemaining: 44 },
    { id: '5', name: 'Project Kickoff', date: '2026-07-15', type: 'other', isMet: null, daysRemaining: 58 }
  ],
  earliestDeadline: '2026-05-25',
  overallConfidence: { value: 95, label: 'Very High Confidence', factors: ['Official deadline schedule', 'Consistent formatting'] },
  summary: '5 key deadlines identified. Clarification request due in 7 days - act soon!'
};

export const MOCK_MANDATORY_DOCS: MandatoryDocsData = {
  overallCompletion: 65,
  overallConfidence: { value: 88, label: 'High Confidence', factors: ['Clear document list', 'Standard requirements'] },
  documents: [
    { id: '1', name: 'Company Registration', description: 'Valid business registration certificate', isRequired: true, isSubmitted: true, submittedDate: '2026-05-10', documentType: 'certificate' },
    { id: '2', name: 'Tax Clearance', description: 'Tax clearance certificate from tax authority', isRequired: true, isSubmitted: true, submittedDate: '2026-05-12', documentType: 'certificate' },
    { id: '3', name: 'Experience Portfolio', description: 'List of similar projects with references', isRequired: true, isSubmitted: true, submittedDate: '2026-05-14', documentType: 'report' },
    { id: '4', name: 'Technical Proposal', description: 'Detailed technical solution document', isRequired: true, isSubmitted: null, documentType: 'document', pageLimit: 50 },
    { id: '5', name: 'Financial Proposal', description: 'Price schedule and cost breakdown', isRequired: true, isSubmitted: null, documentType: 'spreadsheet' },
    { id: '6', name: 'Team CVs', description: 'Resume of key team members', isRequired: true, isSubmitted: false, documentType: 'pdf', pageLimit: 2 },
    { id: '7', name: 'ISO Certifications', description: 'Quality and security certifications', isRequired: true, isSubmitted: true, submittedDate: '2026-05-08', documentType: 'certificate' },
    { id: '8', name: 'Insurance Certificate', description: 'Professional liability insurance', isRequired: true, isSubmitted: true, submittedDate: '2026-05-15', documentType: 'certificate' }
  ],
  summary: '5 of 8 documents submitted. Technical and Financial proposals are pending.'
};

export const MOCK_ANALYSIS: TenderAnalysis = {
  tenderId: 'IIT-2026-001',
  summary: MOCK_SUMMARY,
  eligibility: MOCK_ELIGIBILITY,
  technical: MOCK_TECHNICAL,
  financial: MOCK_FINANCIAL,
  risks: MOCK_RISKS,
  deadlines: MOCK_DEADLINES,
  mandatoryDocs: MOCK_MANDATORY_DOCS,
  createdAt: '2026-05-18T10:00:00Z',
  updatedAt: '2026-05-18T14:30:00Z',
  status: 'completed'
};

export const ANALYSIS_TABS = [
  { id: 'summary', label: 'Summary', icon: 'file-text' },
  { id: 'eligibility', label: 'Eligibility', icon: 'check-circle' },
  { id: 'technical', label: 'Technical', icon: 'cpu' },
  { id: 'financial', label: 'Financial', icon: 'dollar-sign' },
  { id: 'risks', label: 'Risks', icon: 'alert-triangle' },
  { id: 'deadlines', label: 'Deadlines', icon: 'clock' },
  { id: 'mandatory_docs', label: 'Documents', icon: 'folder' }
] as const;