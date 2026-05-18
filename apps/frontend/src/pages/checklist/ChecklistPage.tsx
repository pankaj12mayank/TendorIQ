import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, FileText, Download, RefreshCw, AlertTriangle, Loader2, ChevronRight } from 'lucide-react';
import {
  ChecklistProgress,
  ChecklistSectionAccordion,
  MissingItemsAlert,
  ExportButton,
} from '../../components/checklist/ChecklistComponents';

interface ChecklistData {
  checklist_id: string;
  name: string;
  description?: string;
  status: string;
  completion_percentage: number;
  overall_progress: number;
  total_items: number;
  mandatory_items: number;
  optional_items: number;
  completed_items: number;
  sections: Array<{
    section_id: string;
    name: string;
    description?: string;
    items: Array<{
      item_id: string;
      name: string;
      description?: string;
      is_mandatory: boolean;
      is_submitted: boolean;
      status: string;
      progress_percent: number;
      due_date?: string;
      days_remaining?: number;
      notes?: string;
    }>;
    completed_count: number;
    mandatory_count: number;
    progress_percent: number;
  }>;
  submission_steps: Array<{
    step_id: string;
    name: string;
    description?: string;
    order: number;
    instructions: string[];
    is_completed: boolean;
    estimated_duration_minutes?: number;
  }>;
  score: {
    overall_score: number;
    mandatory_score: number;
    compliance_percentage: number;
    risk_level: string;
    submission_probability: number;
    missing_items: number;
  };
  missing_items: Array<{
    item_name: string;
    days_remaining?: number;
    severity: string;
  }>;
}

interface ChecklistPageProps {
  documentId?: string;
  documentText?: string;
}

const ChecklistPage: React.FC<ChecklistPageProps> = ({ documentId, documentText }) => {
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [checklist, setChecklist] = useState<ChecklistData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generateChecklist = async () => {
    if (!documentText || documentText.length < 100) {
      setError('Document text is too short');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/checklist/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: documentId || crypto.randomUUID(),
          document_text: documentText,
          include_optional_items: true,
        }),
      });

      if (!response.ok) throw new Error('Generation failed');

      const data = await response.json();
      setChecklist(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleItemStatusChange = (itemId: string, status: string) => {
    if (!checklist) return;

    const updatedSections = checklist.sections.map(section => ({
      ...section,
      items: section.items.map(item =>
        item.item_id === itemId
          ? {
              ...item,
              status,
              is_submitted: status === 'submitted',
              progress_percent: status === 'submitted' ? 100 : status === 'preparing' ? 75 : status === 'collecting' ? 50 : 0,
            }
          : item
      ),
    }));

    const completedCount = updatedSections.reduce(
      (acc, section) => acc + section.items.filter(i => i.is_submitted).length,
      0
    );
    const totalCount = updatedSections.reduce((acc, section) => acc + section.items.length, 0);

    setChecklist({
      ...checklist,
      sections: updatedSections,
      completed_items: completedCount,
      completion_percentage: totalCount > 0 ? (completedCount / totalCount) * 100 : 0,
    });
  };

  const handleItemNotesChange = (itemId: string, notes: string) => {
    if (!checklist) return;

    const updatedSections = checklist.sections.map(section => ({
      ...section,
      items: section.items.map(item =>
        item.item_id === itemId ? { ...item, notes } : item
      ),
    }));

    setChecklist({ ...checklist, sections: updatedSections });
  };

  const handleExport = async (format: string) => {
    if (!documentText) return;

    try {
      const response = await fetch(`/api/v1/checklist/checklist-{id}/export?format=${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_text: documentText }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `checklist.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <CheckCircle2 className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Compliance Checklist</h1>
                <p className="text-gray-600">Document submission readiness tracker</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {checklist && (
                <ExportButton onExport={handleExport} />
              )}
              <button
                onClick={() => navigate(-1)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Back
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {!checklist ? (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Generate Compliance Checklist
              </h2>
              <p className="text-gray-600 max-w-lg mx-auto">
                Our AI will analyze your tender document and generate a comprehensive 
                compliance checklist with required documents, deadlines, and submission steps.
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            <div className="flex justify-center">
              <button
                onClick={generateChecklist}
                disabled={isGenerating || !documentText}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-5 h-5" />
                    Generate Checklist
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold">{checklist.name}</h2>
                  <p className="text-gray-600">{checklist.description}</p>
                </div>
                <button
                  onClick={generateChecklist}
                  className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                >
                  <RefreshCw className="w-5 h-5" />
                  Regenerate
                </button>
              </div>

              <ChecklistProgress
                totalItems={checklist.total_items}
                completedItems={checklist.completed_items}
                mandatoryItems={checklist.mandatory_items}
                score={checklist.score.overall_score}
                missingItems={checklist.score.missing_items}
              />
            </div>

            {checklist.missing_items.length > 0 && (
              <MissingItemsAlert items={checklist.missing_items} />
            )}

            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold">Checklist Items</h3>
              </div>
              <div className="divide-y">
                {checklist.sections.map(section => (
                  <ChecklistSectionAccordion
                    key={section.section_id}
                    section={section}
                    onItemStatusChange={handleItemStatusChange}
                    onItemNotesChange={handleItemNotesChange}
                    defaultExpanded={section.section_id === checklist.sections[0]?.section_id}
                  />
                ))}
              </div>
            </div>

            {checklist.submission_steps.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Submission Steps</h3>
                <div className="space-y-4">
                  {checklist.submission_steps.map((step, idx) => (
                    <div key={step.step_id} className="flex items-start gap-4">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        step.is_completed ? 'bg-green-100 text-green-600' : 'bg-gray-100'
                      }`}>
                        {step.is_completed ? '✓' : idx + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">{step.name}</h4>
                          {step.estimated_duration_minutes && (
                            <span className="text-sm text-gray-500">
                              ~{step.estimated_duration_minutes} min
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{step.description}</p>
                        {step.instructions.length > 0 && (
                          <ul className="mt-2 space-y-1">
                            {step.instructions.map((instruction, i) => (
                              <li key={i} className="text-sm text-gray-500 flex items-start gap-2">
                                <span className="text-blue-500">•</span>
                                {instruction}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChecklistPage;