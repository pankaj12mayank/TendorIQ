'use client';

import { Scale } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { ImportantClausesData } from '../types';

interface ImportantClausesSectionProps {
  data: ImportantClausesData;
}

export function ImportantClausesSection({ data }: ImportantClausesSectionProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="rounded-lg bg-indigo-100 p-3">
          <Scale className="h-6 w-6 text-indigo-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold">Important clauses</h2>
          <p className="text-muted-foreground">Legal and commercial terms that need attention</p>
        </div>
      </div>

      {data.summary && (
        <p className="text-sm text-muted-foreground">{data.summary}</p>
      )}

      {data.clauses.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No clauses extracted yet. Run AI analysis after upload.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {data.clauses.map((clause) => (
            <Card key={clause.id}>
              <CardHeader className="pb-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle className="text-base">{clause.title}</CardTitle>
                  <Badge variant="outline" className="capitalize">
                    {clause.category}
                  </Badge>
                </div>
                {clause.impact && (
                  <CardDescription className="text-amber-700 dark:text-amber-400">
                    Impact: {clause.impact}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-wrap">{clause.excerpt}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
