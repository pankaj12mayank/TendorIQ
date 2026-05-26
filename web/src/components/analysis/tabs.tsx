'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  FileText,
  CheckCircle,
  Cpu,
  DollarSign,
  AlertTriangle,
  Clock,
  Folder,
  Scale,
} from 'lucide-react';
import { AnalysisSection } from './types';
import { useAnalysisStore, useAnalysisSections } from './store';


const SECTION_ICONS = {
  summary: FileText,
  eligibility: CheckCircle,
  technical: Cpu,
  financial: DollarSign,
  risks: AlertTriangle,
  deadlines: Clock,
  important_clauses: Scale,
  mandatory_docs: Folder,
};

interface AnalysisTabsProps {
  className?: string;
}

export function AnalysisTabs({ className }: AnalysisTabsProps) {
  const { activeSection, setActiveSection, sections, getSectionProgress } = useAnalysisSections();

  return (
    <div className={cn('w-full', className)}>
      <Tabs 
        value={activeSection} 
        onValueChange={(v) => setActiveSection(v as AnalysisSection)}
        className="w-full"
      >
        <TabsList className="w-full grid grid-cols-4 md:grid-cols-8 h-auto bg-transparent p-0 gap-1">
          {sections.map((section) => {
            const Icon = SECTION_ICONS[section.id as keyof typeof SECTION_ICONS];
            const progress = getSectionProgress(section.id as AnalysisSection);
            
            return (
              <TabsTrigger
                key={section.id}
                value={section.id}
                className={cn(
                  'flex flex-col items-center justify-center p-3 h-auto gap-1 rounded-lg transition-all',
                  'data-[state=active]:bg-primary data-[state=active]:text-primary-foreground',
                  'data-[state=inactive]:bg-muted data-[state=inactive]:hover:bg-muted/80'
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="text-xs font-medium">{section.label}</span>
                <div className="w-full h-1 bg-muted rounded-full overflow-hidden mt-1">
                  <div 
                    className={cn(
                      'h-full rounded-full transition-all',
                      activeSection === section.id ? 'bg-primary-foreground' : 'bg-primary'
                    )}
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </TabsTrigger>
            );
          })}
        </TabsList>
      </Tabs>
    </div>
  );
}

export function AnalysisProgress() {
  const analysis = useAnalysisStore((s) => s.analysis);
  
  if (!analysis) return null;

  const sections = [
    { id: 'summary', label: 'Summary', score: analysis.summary.confidence.value },
    { id: 'eligibility', label: 'Eligibility', score: analysis.eligibility.overallScore },
    { id: 'technical', label: 'Technical', score: analysis.technical.complianceRate },
    { id: 'financial', label: 'Financial', score: 85 },
    { id: 'risks', label: 'Risks', score: 100 - analysis.risks.overallRiskScore },
    { id: 'deadlines', label: 'Deadlines', score: analysis.deadlines.deadlines.length > 0 ? 90 : 0 },
    { id: 'important_clauses', label: 'Clauses', score: analysis.importantClauses.clauses.length > 0 ? 88 : 0 },
    { id: 'mandatory_docs', label: 'Documents', score: analysis.mandatoryDocs.overallCompletion },
  ];

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium">Section Progress</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
        {sections.map((section) => (
          <div key={section.id} className="text-center p-2 bg-muted rounded-lg">
            <div className="text-lg font-bold">{section.score}%</div>
            <div className="text-xs text-muted-foreground">{section.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AnalysisTabs;