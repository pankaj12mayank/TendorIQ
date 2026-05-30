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
import { ImportantClausesSection } from './sections/important-clauses';
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
    const section: AnalysisSection = activeSection;
    switch (section) {
      case 'summary':
        return (
          <SummarySection
            data={analysis.summary}
            isEditing={editingSections.has('summary')}
            onEdit={() => handleEdit('summary')}
            onSave={() => handleSave('summary')}
          />
        );
      case 'eligibility':
        return (
          <EligibilitySection
            data={analysis.eligibility}
            isEditing={editingSections.has('eligibility')}
            onEdit={() => handleEdit('eligibility')}
            onSave={() => handleSave('eligibility')}
          />
        );
      case 'technical':
        return (
          <TechnicalSection
            data={analysis.technical}
            isEditing={editingSections.has('technical')}
            onEdit={() => handleEdit('technical')}
            onSave={() => handleSave('technical')}
          />
        );
      case 'financial':
        return (
          <FinancialSection
            data={analysis.financial}
            isEditing={editingSections.has('financial')}
            onEdit={() => handleEdit('financial')}
            onSave={() => handleSave('financial')}
          />
        );
      case 'risks':
        return (
          <RisksSection
            data={analysis.risks}
            isEditing={editingSections.has('risks')}
            onEdit={() => handleEdit('risks')}
            onSave={() => handleSave('risks')}
          />
        );
      case 'deadlines':
        return (
          <DeadlinesSection
            data={analysis.deadlines}
            isEditing={editingSections.has('deadlines')}
            onEdit={() => handleEdit('deadlines')}
            onSave={() => handleSave('deadlines')}
          />
        );
      case 'important_clauses':
        return <ImportantClausesSection data={analysis.importantClauses} />;
      case 'mandatory_docs':
        return (
          <MandatoryDocsSection
            data={analysis.mandatoryDocs}
            isEditing={editingSections.has('mandatory_docs')}
            onEdit={() => handleEdit('mandatory_docs')}
            onSave={() => handleSave('mandatory_docs')}
          />
        );
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