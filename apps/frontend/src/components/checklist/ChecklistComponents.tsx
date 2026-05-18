import React, { useState } from 'react';
import { CheckCircle2, Circle, Clock, AlertTriangle, Download, FileText, ChevronDown, ChevronRight, FileCheck } from 'lucide-react';

interface ChecklistItemType {
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
}

interface ChecklistSectionType {
  section_id: string;
  name: string;
  description?: string;
  items: ChecklistItemType[];
  progress_percent: number;
  completed_count: number;
  mandatory_count: number;
}

interface ChecklistProgressProps {
  totalItems: number;
  completedItems: number;
  mandatoryItems: number;
  score: number;
  missingItems: number;
}

export const ChecklistProgress: React.FC<ChecklistProgressProps> = ({
  totalItems,
  completedItems,
  mandatoryItems,
  score,
  missingItems,
}) => {
  const percentage = totalItems > 0 ? (completedItems / totalItems) * 100 : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div className="bg-blue-50 rounded-lg p-4 text-center">
        <p className="text-sm text-gray-600">Total Items</p>
        <p className="text-2xl font-bold text-blue-600">{totalItems}</p>
      </div>
      <div className="bg-green-50 rounded-lg p-4 text-center">
        <p className="text-sm text-gray-600">Completed</p>
        <p className="text-2xl font-bold text-green-600">{completedItems}</p>
      </div>
      <div className="bg-purple-50 rounded-lg p-4 text-center">
        <p className="text-sm text-gray-600">Mandatory</p>
        <p className="text-2xl font-bold text-purple-600">{mandatoryItems}</p>
      </div>
      <div className="bg-yellow-50 rounded-lg p-4 text-center">
        <p className="text-sm text-gray-600">Score</p>
        <p className="text-2xl font-bold text-yellow-600">{score.toFixed(0)}%</p>
      </div>
      <div className="bg-red-50 rounded-lg p-4 text-center">
        <p className="text-sm text-gray-600">Missing</p>
        <p className="text-2xl font-bold text-red-600">{missingItems}</p>
      </div>
    </div>
  );
};

interface ChecklistItemCardProps {
  item: ChecklistItemType;
  onStatusChange: (itemId: string, status: string) => void;
  onNotesChange: (itemId: string, notes: string) => void;
}

export const ChecklistItemCard: React.FC<ChecklistItemCardProps> = ({ item, onStatusChange, onNotesChange }) => {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState(item.notes || '');

  const getStatusColor = () => {
    switch (item.status) {
      case 'submitted': return 'text-green-600 bg-green-100';
      case 'ready': return 'text-blue-600 bg-blue-100';
      case 'preparing': return 'text-yellow-600 bg-yellow-100';
      case 'collecting': return 'text-orange-600 bg-orange-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getProgressBar = () => {
    const color = item.progress_percent === 100 ? 'bg-green-500' : item.progress_percent > 50 ? 'bg-blue-500' : 'bg-gray-300';
    return (
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={color} style={{ width: `${item.progress_percent}%` }} />
      </div>
    );
  };

  return (
    <div className={`border rounded-lg p-4 ${item.is_mandatory ? 'border-blue-200' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <button
            onClick={() => onStatusChange(item.item_id, item.is_submitted ? 'not_started' : 'submitted')}
            className="mt-1"
          >
            {item.is_submitted ? (
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            ) : (
              <Circle className="w-6 h-6 text-gray-400" />
            )}
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-medium">{item.name}</h4>
              {item.is_mandatory && (
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">Required</span>
              )}
            </div>
            {item.description && (
              <p className="text-sm text-gray-600 mt-1">{item.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-1 rounded ${getStatusColor()}`}>
            {item.status.replace('_', ' ')}
          </span>
          {item.days_remaining !== null && item.days_remaining !== undefined && (
            <span className={`text-xs flex items-center gap-1 ${item.days_remaining < 3 ? 'text-red-600' : 'text-gray-600'}`}>
              <Clock className="w-4 h-4" />
              {item.days_remaining}d left
            </span>
          )}
          <button onClick={() => setExpanded(!expanded)} className="p-1 hover:bg-gray-100 rounded">
            {expanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {getProgressBar()}

      {expanded && (
        <div className="mt-4 pt-4 border-t space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              onBlur={() => onNotesChange(item.item_id, notes)}
              className="w-full mt-1 p-2 border rounded-lg text-sm"
              rows={2}
              placeholder="Add notes..."
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onStatusChange(item.item_id, 'collecting')}
              className={`px-3 py-1 text-sm rounded ${item.status === 'collecting' ? 'bg-orange-500 text-white' : 'bg-gray-100'}`}
            >
              Collecting
            </button>
            <button
              onClick={() => onStatusChange(item.item_id, 'preparing')}
              className={`px-3 py-1 text-sm rounded ${item.status === 'preparing' ? 'bg-yellow-500 text-white' : 'bg-gray-100'}`}
            >
              Preparing
            </button>
            <button
              onClick={() => onStatusChange(item.item_id, 'submitted')}
              className={`px-3 py-1 text-sm rounded ${item.status === 'submitted' ? 'bg-green-500 text-white' : 'bg-gray-100'}`}
            >
              Submitted
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

interface ChecklistSectionAccordionProps {
  section: ChecklistSectionType;
  onItemStatusChange: (itemId: string, status: string) => void;
  onItemNotesChange: (itemId: string, notes: string) => void;
  defaultExpanded?: boolean;
}

export const ChecklistSectionAccordion: React.FC<ChecklistSectionAccordionProps> = ({
  section,
  onItemStatusChange,
  onItemNotesChange,
  defaultExpanded = true,
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const completed = section.items.filter(i => i.is_submitted).length;
  const total = section.items.length;
  const progress = total > 0 ? (completed / total) * 100 : 0;

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100"
      >
        <div className="flex items-center gap-3">
          {expanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          <div className="text-left">
            <h3 className="font-semibold">{section.name}</h3>
            <p className="text-sm text-gray-600">{section.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">{completed}/{total} completed</span>
          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="bg-green-500 h-full" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </button>

      {expanded && (
        <div className="p-4 space-y-3">
          {section.items.map(item => (
            <ChecklistItemCard
              key={item.item_id}
              item={item}
              onStatusChange={onItemStatusChange}
              onNotesChange={onItemNotesChange}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface MissingItemsAlertProps {
  items: Array<{
    item_name: string;
    days_remaining?: number;
    severity: string;
  }>;
}

export const MissingItemsAlert: React.FC<MissingItemsAlertProps> = ({ items }) => {
  if (items.length === 0) return null;

  const criticalItems = items.filter(i => i.severity === 'critical' || i.severity === 'high');

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle className="w-5 h-5 text-red-600" />
        <h3 className="font-semibold text-red-800">
          Missing Items ({items.length})
        </h3>
      </div>
      <div className="space-y-2">
        {criticalItems.slice(0, 5).map((item, idx) => (
          <div key={idx} className="flex items-center justify-between text-sm">
            <span className="text-red-700">{item.item_name}</span>
            {item.days_remaining !== undefined && (
              <span className="text-red-600 flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {item.days_remaining} days left
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

interface ExportButtonProps {
  onExport: (format: string) => void;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ onExport }) => {
  const [showMenu, setShowMenu] = useState(false);

  const formats = [
    { format: 'json', label: 'JSON', icon: '📄' },
    { format: 'csv', label: 'CSV', icon: '📊' },
    { format: 'markdown', label: 'Markdown', icon: '📝' },
    { format: 'html', label: 'HTML', icon: '🌐' },
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
      >
        <Download className="w-5 h-5" />
        Export
      </button>
      {showMenu && (
        <div className="absolute right-0 mt-2 w-40 bg-white border rounded-lg shadow-lg z-10">
          {formats.map(({ format, label, icon }) => (
            <button
              key={format}
              onClick={() => {
                onExport(format);
                setShowMenu(false);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2"
            >
              <span>{icon}</span>
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default {
  ChecklistProgress,
  ChecklistItemCard,
  ChecklistSectionAccordion,
  MissingItemsAlert,
  ExportButton,
};