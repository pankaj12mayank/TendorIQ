'use client';

import React, { useState } from 'react';
import { useReviewStore } from '@/components/review/store';
import { useReviewSections } from '@/hooks/use-review';
import { useReviewApi, useApprovalWorkflow, useEditWorkflow } from '@/hooks/use-review';
import {
  ReviewSummary,
  EditableSection,
  ApprovalWorkflow,
  AuditLog,
  ChangeHistory,
  ReviewerComments,
} from '@/components/review';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  FileText,
  CheckCircle,
  Cpu,
  DollarSign,
  AlertTriangle,
  Clock,
  Folder,
  ChevronLeft,
  Save,
  RefreshCw,
} from 'lucide-react';
import Link from 'next/link';

const SECTION_ICONS = {
  summary: FileText,
  eligibility: CheckCircle,
  technical: Cpu,
  financial: DollarSign,
  risks: AlertTriangle,
  deadlines: Clock,
  mandatory_docs: Folder,
};

const SECTION_TITLES = {
  summary: 'Summary',
  eligibility: 'Eligibility',
  technical: 'Technical',
  financial: 'Financial',
  risks: 'Risks',
  deadlines: 'Deadlines',
  mandatory_docs: 'Documents',
};

export default function ReviewPage() {
  const { selectedSection, setSelectedSection, sections, getSectionStatus, getSectionProgress } = useReviewSections();
  const { session, regenerateSection, isLoading } = useReviewStore();
  const { submitApproval, requestChanges } = useApprovalWorkflow();
  const { editState, saveEdit, cancelEdit, isSaving } = useEditWorkflow();

  const [activeTab, setActiveTab] = useState<'content' | 'comments' | 'history' | 'audit'>('content');

  if (!session) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading review session...</p>
        </div>
      </div>
    );
  }

  const handleRegenerate = async (section: string) => {
    await regenerateSection({
      section: section as any,
      reason: 'Manual regeneration requested',
      includeChanges: true,
      priority: 'normal',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/tenders" className="p-2 hover:bg-muted rounded-lg">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">Human Review</h1>
              <Badge className={cn(
                session.workflow.status === 'approved' && 'bg-green-100 text-green-800',
                session.workflow.status === 'in_review' && 'bg-blue-100 text-blue-800',
                session.workflow.status === 'changes_requested' && 'bg-yellow-100 text-yellow-800'
              )}>
                {session.workflow.status.replace('_', ' ')}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              Review and approve tender analysis - {session.tenderId}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {editState.isEditing && (
            <>
              <Button variant="outline" onClick={cancelEdit} disabled={isSaving}>
                Cancel
              </Button>
              <Button onClick={saveEdit} disabled={isSaving}>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </>
          )}
          {!editState.isEditing && (
            <>
              <Button variant="outline">
                <RefreshCw className={cn('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
                Refresh
              </Button>
            </>
          )}
        </div>
      </div>

      <ReviewSummary />

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>Review Sections</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2 md:grid-cols-4 lg:grid-cols-7">
                {sections.map((section) => {
                  const Icon = SECTION_ICONS[section.id as keyof typeof SECTION_ICONS];
                  const status = getSectionStatus(section.id as any);
                  const progress = getSectionProgress(section.id as any);

                  return (
                    <button
                      key={section.id}
                      onClick={() => setSelectedSection(section.id as any)}
                      className={cn(
                        'flex flex-col items-center justify-center p-3 rounded-lg border transition-all',
                        selectedSection === section.id
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'bg-card hover:bg-muted'
                      )}
                    >
                      <Icon className="w-5 h-5 mb-2" />
                      <span className="text-xs font-medium">{section.label}</span>
                      <div className="w-full h-1 bg-muted rounded-full mt-2 overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            selectedSection === section.id ? 'bg-primary-foreground' : 'bg-primary'
                          )}
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </button>
                  );
                })}
              </div>

              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
                <TabsList>
                  <TabsTrigger value="content">Content</TabsTrigger>
                  <TabsTrigger value="comments">Comments</TabsTrigger>
                  <TabsTrigger value="history">History</TabsTrigger>
                  <TabsTrigger value="audit">Audit Log</TabsTrigger>
                </TabsList>

                <TabsContent value="content" className="space-y-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle>{SECTION_TITLES[selectedSection]}</CardTitle>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRegenerate(selectedSection)}
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Regenerate
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <EditableSection section={selectedSection} title={SECTION_TITLES[selectedSection]}>
                          <div className="p-8 text-center text-muted-foreground">
                            Section content for {selectedSection} would be rendered here.
                            This connects to the analysis components.
                          </div>
                        </EditableSection>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="comments">
                  <ReviewerComments sectionFilter={selectedSection} />
                </TabsContent>

                <TabsContent value="history">
                  <ChangeHistory />
                </TabsContent>

                <TabsContent value="audit">
                  <AuditLog />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <ApprovalWorkflow
            onApprove={(comments) => console.log('Approved with:', comments)}
            onReject={(comments) => console.log('Rejected with:', comments)}
            onRequestChanges={(sections, comments) => console.log('Changes requested:', sections, comments)}
          />

          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{session.comments.length}</div>
                  <div className="text-xs text-muted-foreground">Comments</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{session.changes.length}</div>
                  <div className="text-xs text-muted-foreground">Changes</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{session.reviewers.length}</div>
                  <div className="text-xs text-muted-foreground">Reviewers</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{session.auditLog.length}</div>
                  <div className="text-xs text-muted-foreground">Audit Entries</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}