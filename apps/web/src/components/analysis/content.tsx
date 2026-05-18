'use client';

import React, { useState } from 'react';
import { useAnalysisStore, useAnalysisSections } from './store';
import { AnalysisSection } from './types';

import { SummarySection } from './sections/summary';
import { EligibilitySection } from './sections/eligibility';
import { TechnicalSection } from './sections/technical';
import { FinancialSection } from './sections/financial';
import { RisksSection } from './sections/risks';
import { DeadlinesSection } from './sections/deadlines';
import { MandatoryDocsSection } from './sections/mandatory-docs';
import { AnalysisTabs, AnalysisProgress } from './tabs';

interface AnalysisContentProps {
  className?: string;
}

export function AnalysisContent({ className }: AnalysisContentProps) {
  const { analysis } = useAnalysisStore();
  const { activeSection } = useAnalysisSections();
  const [editingSections, setEditingSections] = useState<Set<AnalysisSection>>(new Set());

  if (!analysis) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">No analysis data available</p>
      </div>
    );
  }

  const handleEdit = (section: AnalysisSection) => {
    setEditingSections((prev) => new Set([...prev, section]));
  };

  const handleSave = (section: AnalysisSection) => {
    setEditingSections((prev) => {
      const next = new Set(prev);
      next.delete(section);
      return next;
    });
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'summary':
        return <SummarySection data={analysis.summary} isEditing={editingSections.has('summary')} />;
      case 'eligibility':
        return <EligibilitySection data={analysis.eligibility} isEditing={editingSections.has('eligibility')} />;
      case 'technical':
        return <TechnicalSection data={analysis.technical} isEditing={editingSections.has('technical')} />;
      case 'financial':
        return <FinancialSection data={analysis.financial} isEditing={editingSections.has('financial')} />;
      case 'risks':
        return <RisksSection data={analysis.risks} isEditing={editingSections.has('risks')} />;
      case 'deadlines':
        return <DeadlinesSection data={analysis.deadlines} isEditing={editingSections.has('deadlines')} />;
      case 'mandatory_docs':
        return <MandatoryDocsSection data={analysis.mandatoryDocs} isEditing={editingSections.has('mandatory_docs')} />;
      default:
        return null;
    }
  };

  return (
    <div className={className}>
      <AnalysisTabs className="mb-6" />
      <AnalysisProgress />
      <div className="mt-6">
        {renderSection()}
      </div>
    </div>
  );
}

export default AnalysisContent;