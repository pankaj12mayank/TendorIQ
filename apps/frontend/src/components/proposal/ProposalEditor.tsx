import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Save, RefreshCw, Download, Plus, Trash2, Copy, Eye, Edit3, ChevronDown, ChevronUp, FileText, CheckCircle, Clock } from 'lucide-react';

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

interface ProposalEditorProps {
  proposalId: string;
  sections: Section[];
  onSectionUpdate: (sectionId: string, content: string) => void;
  onSectionRegenerate: (sectionId: string) => void;
  onAddSection: (sectionType: string, title: string) => void;
  onDeleteSection: (sectionId: string) => void;
  onDuplicateSection: (sectionId: string) => void;
  onExport: (format: string) => void;
}

export const ProposalEditor: React.FC<ProposalEditorProps> = ({
  proposalId,
  sections,
  onSectionUpdate,
  onSectionRegenerate,
  onAddSection,
  onDeleteSection,
  onDuplicateSection,
  onExport,
}) => {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [savingStates, setSavingStates] = useState<Record<string, boolean>>({});

  const sortedSections = [...sections].sort((a, b) => a.order - b.order);

  const handleContentChange = useCallback((sectionId: string, content: string) => {
    setSavingStates(prev => ({ ...prev, [sectionId]: true }));
    onSectionUpdate(sectionId, content);
    setTimeout(() => {
      setSavingStates(prev => ({ ...prev, [sectionId]: false }));
    }, 500);
  }, [onSectionUpdate]);

  return (
    <div className="flex h-full">
      <div className="w-64 border-r bg-gray-50">
        <div className="p-4 border-b">
          <h3 className="font-semibold text-gray-700">Sections</h3>
          <p className="text-xs text-gray-500 mt-1">{sections.length} sections</p>
        </div>
        <div className="overflow-y-auto h-full">
          {sortedSections.map((section, idx) => (
            <div
              key={section.section_id}
              className={`p-3 border-b cursor-pointer hover:bg-gray-100 ${
                activeSection === section.section_id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
              }`}
              onClick={() => setActiveSection(section.section_id)}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-sm">{idx + 1}. {section.title}</span>
                {section.is_edited && <span className="text-xs text-blue-600">edited</span>}
              </div>
              <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                <span>{section.word_count} words</span>
                {savingStates[section.section_id] && (
                  <span className="text-blue-600">saving...</span>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="p-4 border-t">
          <button className="w-full flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            <Plus className="w-4 h-4" />
            Add Section
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {activeSection ? (
          <SectionEditor
            section={sortedSections.find(s => s.section_id === activeSection)!}
            previewMode={previewMode}
            onTogglePreview={() => setPreviewMode(!previewMode)}
            onContentChange={(content) => handleContentChange(activeSection, content)}
            onRegenerate={() => onSectionRegenerate(activeSection)}
            onDelete={() => onDeleteSection(activeSection)}
            onDuplicate={() => onDuplicateSection(activeSection)}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a section to edit
          </div>
        )}
      </div>
    </div>
  );
};

interface SectionEditorProps {
  section: Section;
  previewMode: boolean;
  onTogglePreview: () => void;
  onContentChange: (content: string) => void;
  onRegenerate: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

const SectionEditor: React.FC<SectionEditorProps> = ({
  section,
  previewMode,
  onTogglePreview,
  onContentChange,
  onRegenerate,
  onDelete,
  onDuplicate,
}) => {
  const [content, setContent] = useState(section.content);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setContent(section.content);
  }, [section.content]);

  const handleChange = (newContent: string) => {
    setContent(newContent);
    onContentChange(newContent);
  };

  return (
    <div className="flex-1 flex flex-col">
      <div className="p-4 border-b flex items-center justify-between bg-white">
        <div>
          <h2 className="text-xl font-semibold">{section.title}</h2>
          <p className="text-sm text-gray-500">{section.word_count} words</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onTogglePreview}
            className={`px-3 py-2 rounded flex items-center gap-2 ${
              previewMode ? 'bg-blue-100 text-blue-700' : 'bg-gray-100'
            }`}
          >
            {previewMode ? <Edit3 className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {previewMode ? 'Edit' : 'Preview'}
          </button>
          <button
            onClick={onRegenerate}
            className="px-3 py-2 bg-green-600 text-white rounded flex items-center gap-2 hover:bg-green-700"
          >
            <RefreshCw className="w-4 h-4" />
            Regenerate
          </button>
          <button
            onClick={onDuplicate}
            className="px-3 py-2 bg-gray-100 rounded flex items-center gap-2 hover:bg-gray-200"
          >
            <Copy className="w-4 h-4" />
            Duplicate
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-2 bg-red-100 text-red-600 rounded flex items-center gap-2 hover:bg-red-200"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {previewMode ? (
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap">{content}</div>
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => handleChange(e.target.value)}
            className="w-full h-full min-h-[500px] p-4 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter section content here..."
          />
        )}
      </div>

      <div className="p-4 border-t bg-gray-50 flex items-center justify-between">
        <div className="text-sm text-gray-500">
          {content.split(/\s+/).filter(Boolean).length} words
        </div>
        <div className="flex items-center gap-2">
          <button className="px-4 py-2 bg-blue-600 text-white rounded flex items-center gap-2 hover:bg-blue-700">
            <Save className="w-4 h-4" />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

interface ProposalPreviewProps {
  proposalId: string;
  title: string;
  sections: Section[];
  status: string;
  totalWords: number;
  onExport: (format: string) => void;
}

export const ProposalPreview: React.FC<ProposalPreviewProps> = ({
  proposalId,
  title,
  sections,
  status,
  totalWords,
  onExport,
}) => {
  const sortedSections = [...sections].sort((a, b) => a.order - b.order);

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
            <span className="px-2 py-1 bg-blue-100 rounded">{status}</span>
            <span>{sortedSections.length} sections</span>
            <span>{totalWords} words</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onExport('markdown')}
            className="px-4 py-2 bg-gray-100 rounded flex items-center gap-2 hover:bg-gray-200"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      <div className="space-y-8">
        {sortedSections.map((section, idx) => (
          <div key={section.section_id} className="border-b pb-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm text-gray-500">{idx + 1}.</span>
              <h2 className="text-xl font-semibold">{section.title}</h2>
              {section.is_generated && (
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">AI Generated</span>
              )}
              {section.is_edited && (
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">Edited</span>
              )}
            </div>
            <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">
              {section.content}
            </div>
            <div className="mt-2 text-xs text-gray-400">
              {section.word_count} words
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface ProposalSummaryCardProps {
  proposalId: string;
  title: string;
  status: string;
  sectionsGenerated: number;
  totalSections: number;
  totalWords: number;
  lastModified: string;
  onView: () => void;
}

export const ProposalSummaryCard: React.FC<ProposalSummaryCardProps> = ({
  proposalId,
  title,
  status,
  sectionsGenerated,
  totalSections,
  totalWords,
  lastModified,
  onView,
}) => {
  const progress = totalSections > 0 ? (sectionsGenerated / totalSections) * 100 : 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-lg">{title}</h3>
          <p className="text-sm text-gray-500">ID: {proposalId.slice(0, 8)}...</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm ${
          status === 'completed' ? 'bg-green-100 text-green-700' :
          status === 'draft' ? 'bg-gray-100 text-gray-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {status}
        </span>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-600">Progress</span>
          <span className="font-medium">{progress.toFixed(0)}%</span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Sections</p>
          <p className="font-medium">{sectionsGenerated}/{totalSections}</p>
        </div>
        <div>
          <p className="text-gray-500">Words</p>
          <p className="font-medium">{totalWords}</p>
        </div>
        <div>
          <p className="text-gray-500">Modified</p>
          <p className="font-medium">{lastModified}</p>
        </div>
      </div>

      <button
        onClick={onView}
        className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        View Proposal
      </button>
    </div>
  );
};

export default {
  ProposalEditor,
  ProposalPreview,
  ProposalSummaryCard,
};