'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Edit3, 
  Save, 
  X, 
  RotateCcw,
  Check,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { ReviewSection } from '../types';
import { useReviewStore } from '../store';
import { cn } from '@/lib/utils';

interface EditableFieldProps {
  section: ReviewSection;
  field: string;
  label: string;
  value: string | number;
  type?: 'text' | 'number' | 'textarea';
  disabled?: boolean;
  className?: string;
}

export function EditableField({
  section,
  field,
  label,
  value,
  type = 'text',
  disabled = false,
  className,
}: EditableFieldProps) {
  const { editState, startEdit, updateEditValue, saveEdit, cancelEdit, isSaving } = useReviewStore();
  
  const isEditing = editState.section === section && editState.field === field;

  const handleStartEdit = () => {
    startEdit(section, field, value);
  };

  const handleSave = async () => {
    await saveEdit();
  };

  const renderInput = () => {
    if (!isEditing) {
      return (
        <div className="flex items-center gap-2">
          <span className={cn('flex-1', className)}>{value}</span>
          {!disabled && (
            <Button variant="ghost" size="sm" onClick={handleStartEdit}>
              <Edit3 className="w-4 h-4" />
            </Button>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {type === 'textarea' ? (
            <Textarea
              value={String(editState.currentValue || '')}
              onChange={(e) => updateEditValue(e.target.value)}
              className="min-h-[80px]"
            />
          ) : type === 'number' ? (
            <Input
              type="number"
              value={String(editState.currentValue || '')}
              onChange={(e) => updateEditValue(e.target.value)}
            />
          ) : (
            <Input
              type="text"
              value={String(editState.currentValue || '')}
              onChange={(e) => updateEditValue(e.target.value)}
            />
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" onClick={handleSave} disabled={isSaving}>
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            Save
          </Button>
          <Button size="sm" variant="ghost" onClick={cancelEdit}>
            <X className="w-4 h-4" />
            Cancel
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-muted-foreground">{label}</label>
      {renderInput()}
    </div>
  );
}

interface RegenerateSectionProps {
  section: ReviewSection;
  onRegenerate?: (section: ReviewSection) => void;
}

export function RegenerateSection({ section, onRegenerate }: RegenerateSectionProps) {
  const { regenerationState } = useReviewStore();
  const [showConfirm, setShowConfirm] = useState(false);
  const [reason, setReason] = useState('');

  const isRegenerating = regenerationState.isRegenerating && regenerationState.section === section;

  const handleRegenerate = () => {
    if (onRegenerate) {
      onRegenerate(section);
    }
  };

  return (
    <div className="space-y-2">
      {showConfirm ? (
        <div className="p-3 bg-muted rounded-lg space-y-2">
          <p className="text-sm font-medium">Regenerate {section}?</p>
          <Input
            placeholder="Reason for regeneration..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="text-sm"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleRegenerate} disabled={isRegenerating}>
              {isRegenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  {regenerationState.progress}%
                </>
              ) : (
                'Confirm'
              )}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setShowConfirm(false)} disabled={isRegenerating}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <Button variant="outline" size="sm" onClick={() => setShowConfirm(true)} disabled={isRegenerating}>
          <RotateCcw className="w-4 h-4 mr-2" />
          Regenerate
        </Button>
      )}
    </div>
  );
}

interface EditableSectionProps {
  section: ReviewSection;
  title: string;
  children: React.ReactNode;
  onRegenerate?: (section: ReviewSection) => void;
  className?: string;
}

export function EditableSection({ section, title, children, onRegenerate, className }: EditableSectionProps) {
  const { getSectionStatus } = useReviewStore();
  const status = getSectionStatus(section);

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <CardTitle>{title}</CardTitle>
          {status?.hasChanges && (
            <Badge variant="outline" className="text-yellow-600 border-yellow-300">
              Modified
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onRegenerate && <RegenerateSection section={section} onRegenerate={onRegenerate} />}
          <Badge
            className={cn(
              'text-xs',
              status?.approvalStatus === 'approved' && 'bg-green-100 text-green-800',
              status?.approvalStatus === 'pending' && 'bg-yellow-100 text-yellow-800',
              status?.approvalStatus === 'needs_revision' && 'bg-orange-100 text-orange-800'
            )}
          >
            {status?.approvalStatus.replace('_', ' ')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default EditableSection;