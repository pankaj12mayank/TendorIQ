import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, Plus, Clock, CheckCircle, RefreshCw, Loader2, Download, Save } from 'lucide-react';
import { ProposalEditor, ProposalPreview, ProposalSummaryCard } from '../../components/proposal/ProposalEditor';

interface Section {
  section_id: string;
  section_type: string;
  title: string;
  content: string;
  order: number;
  is_generated: boolean;
  is_edited: boolean;
  word_count: number;
}

interface ProposalData {
  proposal_id: string;
  title: string;
  status: string;
  sections: Section[];
  total_words: number;
  estimated_pages: number;
}

interface ProposalPageProps {
  tenderId?: string;
  documentId?: string;
  documentText?: string;
}

const ProposalPage: React.FC<ProposalPageProps> = ({ tenderId, documentId, documentText }) => {
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [proposal, setProposal] = useState<ProposalData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'edit' | 'preview'>('edit');

  const generateProposal = async () => {
    if (!documentText || documentText.length < 100) {
      setError('Document text is too short');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/proposal/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tender_id: tenderId,
          document_id: documentId,
          document_text: documentText,
          style: 'professional',
        }),
      });

      if (!response.ok) throw new Error('Generation failed');

      const result = await response.json();
      const proposalId = result.proposal_id;

      const proposalResponse = await fetch(`/api/v1/proposal/${proposalId}`);
      const proposalData = await proposalResponse.json();
      setProposal(proposalData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSectionUpdate = async (sectionId: string, content: string) => {
    if (!proposal) return;

    try {
      await fetch(`/api/v1/proposal/${proposal.proposal_id}/sections/${sectionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, edited_by: 'user' }),
      });

      setProposal(prev => prev ? {
        ...prev,
        sections: prev.sections.map(s =>
          s.section_id === sectionId
            ? { ...s, content, is_edited: true, word_count: content.split(/\s+/).filter(Boolean).length }
            : s
        ),
      } : null);
    } catch (err) {
      console.error('Failed to save section:', err);
    }
  };

  const handleSectionRegenerate = async (sectionId: string) => {
    if (!proposal) return;

    try {
      const response = await fetch(`/api/v1/proposal/${proposal.proposal_id}/sections/${sectionId}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keep_existing_content: false, style: 'professional' }),
      });

      const updatedSection = await response.json();

      setProposal(prev => prev ? {
        ...prev,
        sections: prev.sections.map(s =>
          s.section_id === sectionId ? updatedSection : s
        ),
      } : null);
    } catch (err) {
      console.error('Failed to regenerate section:', err);
    }
  };

  const handleAddSection = async (sectionType: string, title: string) => {
    if (!proposal) return;

    try {
      const response = await fetch(`/api/v1/proposal/${proposal.proposal_id}/sections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section_type: sectionType, title, content: '' }),
      });

      const newSection = await response.json();

      setProposal(prev => prev ? {
        ...prev,
        sections: [...prev.sections, newSection],
      } : null);
    } catch (err) {
      console.error('Failed to add section:', err);
    }
  };

  const handleDeleteSection = async (sectionId: string) => {
    if (!proposal) return;

    try {
      await fetch(`/api/v1/proposal/${proposal.proposal_id}/sections/${sectionId}`, {
        method: 'DELETE',
      });

      setProposal(prev => prev ? {
        ...prev,
        sections: prev.sections.filter(s => s.section_id !== sectionId),
      } : null);
    } catch (err) {
      console.error('Failed to delete section:', err);
    }
  };

  const handleDuplicateSection = async (sectionId: string) => {
    if (!proposal) return;

    try {
      const response = await fetch(`/api/v1/proposal/${proposal.proposal_id}/sections/${sectionId}/duplicate`, {
        method: 'POST',
      });

      const newSection = await response.json();

      setProposal(prev => prev ? {
        ...prev,
        sections: [...prev.sections, newSection],
      } : null);
    } catch (err) {
      console.error('Failed to duplicate section:', err);
    }
  };

  const handleExport = async (format: string) => {
    if (!proposal) return;

    try {
      const response = await fetch(`/api/v1/proposal/${proposal.proposal_id}/export?format=${format}`, {
        method: 'POST',
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${proposal.title}.${format}`;
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
              <div className="p-3 bg-purple-100 rounded-lg">
                <FileText className="w-8 h-8 text-purple-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Proposal Generator</h1>
                <p className="text-gray-600">AI-powered tender proposal creation</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {proposal && (
                <>
                  <div className="flex items-center gap-1 border rounded-lg">
                    <button
                      onClick={() => setViewMode('edit')}
                      className={`px-4 py-2 ${viewMode === 'edit' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setViewMode('preview')}
                      className={`px-4 py-2 ${viewMode === 'preview' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
                    >
                      Preview
                    </button>
                  </div>
                  <button
                    onClick={() => handleExport('markdown')}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    <Download className="w-5 h-5" />
                    Export
                  </button>
                </>
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
        {!proposal ? (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                <FileText className="w-8 h-8 text-purple-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Generate Proposal
              </h2>
              <p className="text-gray-600 max-w-lg mx-auto">
                Our AI will analyze your tender document and generate a complete proposal
                with all required sections including executive summary, company profile,
                technical approach, and more.
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            <div className="flex justify-center">
              <button
                onClick={generateProposal}
                disabled={isGenerating || !documentText}
                className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Plus className="w-5 h-5" />
                    Generate Proposal
                  </>
                )}
              </button>
            </div>
          </div>
        ) : viewMode === 'edit' ? (
          <ProposalEditor
            proposalId={proposal.proposal_id}
            sections={proposal.sections}
            onSectionUpdate={handleSectionUpdate}
            onSectionRegenerate={handleSectionRegenerate}
            onAddSection={handleAddSection}
            onDeleteSection={handleDeleteSection}
            onDuplicateSection={handleDuplicateSection}
            onExport={handleExport}
          />
        ) : (
          <ProposalPreview
            proposalId={proposal.proposal_id}
            title={proposal.title}
            sections={proposal.sections}
            status={proposal.status}
            totalWords={proposal.total_words}
            onExport={handleExport}
          />
        )}
      </div>
    </div>
  );
};

export default ProposalPage;