'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import {
  MessageSquare,
  Send,
  CheckCircle,
  Reply,
  MoreHorizontal,
  Filter,
  Clock
} from 'lucide-react';
import { ReviewComment, ReviewSection } from '../types';
import { useReviewStore } from '../store';
import { cn } from '@/lib/utils';

interface ReviewerCommentsProps {
  sectionFilter?: ReviewSection;
  className?: string;
}

export function ReviewerComments({ sectionFilter, className }: ReviewerCommentsProps) {
  const { session, addComment, resolveComment, addReply } = useReviewStore();
  const [newComment, setNewComment] = useState('');
  const [selectedSection, setSelectedSection] = useState<ReviewSection | undefined>(sectionFilter);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [showResolved, setShowResolved] = useState(false);

  if (!session) return null;

  let comments = selectedSection
    ? session.comments.filter(c => c.section === selectedSection)
    : session.comments;

  if (!showResolved) {
    comments = comments.filter(c => !c.isResolved);
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const handleAddComment = () => {
    if (!newComment.trim()) return;

    addComment({
      reviewerId: 'current-user',
      reviewerName: 'Current User',
      reviewerRole: 'Reviewer',
      section: selectedSection,
      content: newComment,
    });

    setNewComment('');
  };

  const handleReply = (commentId: string) => {
    if (!replyContent.trim()) return;

    addReply(commentId, {
      reviewerId: 'current-user',
      reviewerName: 'Current User',
      reviewerRole: 'Reviewer',
      content: replyContent,
    });

    setReplyContent('');
    setReplyingTo(null);
  };

  const handleResolve = (commentId: string) => {
    resolveComment(commentId);
  };

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Reviewer Comments
        </CardTitle>
        <CardDescription>
          Discussion and feedback on sections
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <select
            className="h-10 px-3 rounded-md border bg-background text-sm flex-1"
            value={selectedSection || ''}
            onChange={(e) => setSelectedSection(e.target.value as ReviewSection || undefined)}
          >
            <option value="">All Sections</option>
            <option value="summary">Summary</option>
            <option value="eligibility">Eligibility</option>
            <option value="technical">Technical</option>
            <option value="financial">Financial</option>
            <option value="risks">Risks</option>
            <option value="deadlines">Deadlines</option>
            <option value="mandatory_docs">Documents</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowResolved(!showResolved)}
          >
            {showResolved ? 'Hide Resolved' : 'Show Resolved'}
          </Button>
        </div>

        <div className="space-y-4 max-h-[400px] overflow-y-auto">
          {comments.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No comments yet
            </div>
          ) : (
            comments.map((comment) => (
              <div
                key={comment.id}
                className={cn(
                  'p-4 rounded-lg border',
                  comment.isResolved && 'bg-muted/50 opacity-75'
                )}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Avatar className="w-8 h-8 bg-primary text-primary-foreground">
                      {comment.reviewerName.charAt(0)}
                    </Avatar>
                    <div>
                      <p className="font-medium text-sm">{comment.reviewerName}</p>
                      <p className="text-xs text-muted-foreground">{comment.reviewerRole}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {comment.section && (
                      <Badge variant="outline" className="text-xs capitalize">
                        {comment.section.replace('_', ' ')}
                      </Badge>
                    )}
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(comment.createdAt)}
                    </span>
                    {comment.isResolved && (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                </div>

                <p className="text-sm mb-3">{comment.content}</p>

                <div className="flex items-center gap-2">
                  {!comment.isResolved && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setReplyingTo(comment.id)}
                      >
                        <Reply className="w-4 h-4 mr-1" />
                        Reply
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleResolve(comment.id)}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Resolve
                      </Button>
                    </>
                  )}
                </div>

                {replyingTo === comment.id && (
                  <div className="mt-3 p-3 bg-muted rounded-lg space-y-2">
                    <Textarea
                      placeholder="Write a reply..."
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                      className="min-h-[60px] text-sm"
                    />
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleReply(comment.id)}>
                        <Send className="w-4 h-4 mr-1" />
                        Send
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setReplyingTo(null);
                          setReplyContent('');
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {comment.replies && comment.replies.length > 0 && (
                  <div className="mt-3 space-y-2 pl-4 border-l-2 border-muted">
                    {comment.replies.map((reply) => (
                      <div key={reply.id} className="p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Avatar className="w-6 h-6 bg-secondary text-secondary-foreground text-xs">
                            {reply.reviewerName.charAt(0)}
                          </Avatar>
                          <span className="text-sm font-medium">{reply.reviewerName}</span>
                          <span className="text-xs text-muted-foreground">
                            {formatTimestamp(reply.createdAt)}
                          </span>
                        </div>
                        <p className="text-sm">{reply.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="pt-4 border-t space-y-2">
          <Textarea
            placeholder="Add a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            className="min-h-[80px]"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              Commenting on: {selectedSection || 'All sections'}
            </span>
            <Button onClick={handleAddComment} disabled={!newComment.trim()}>
              <Send className="w-4 h-4 mr-2" />
              Post Comment
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ReviewerComments;