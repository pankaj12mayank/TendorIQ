'use client';

import { motion } from 'framer-motion';
import { CheckCircle2 } from 'lucide-react';

type WorkflowStep = {
  id?: string;
  title?: string;
  description?: string;
  image_url?: string;
};

type WorkflowTutorial = {
  title?: string;
  subtitle?: string;
  steps?: WorkflowStep[];
};

const fallbackSteps: WorkflowStep[] = [
  { title: 'Upload tender file', description: 'Upload PDF or DOCX and create a processing job.' },
  { title: 'Extract key requirements', description: 'TenderIQ extracts clauses and deadlines.' },
  { title: 'Run AI analysis', description: 'Detect risks and compliance concerns.' },
  { title: 'Review flagged items', description: 'Validate critical findings before drafting.' },
  { title: 'Generate proposal', description: 'Create and export a submission-ready proposal.' },
];

export function WorkflowTutorialSection({ content }: { content?: WorkflowTutorial }) {
  const steps = content?.steps?.length ? content.steps : fallbackSteps;

  return (
    <section id="workflow" className="scroll-mt-24 border-t border-white/5 py-24 md:py-32">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12 text-center"
        >
          <h2 className="cinematic-heading">{content?.title ?? 'Workflow Tutorial'}</h2>
          <p className="mt-3 text-lg text-muted-foreground">
            {content?.subtitle ?? 'Understand how your team moves from upload to proposal in minutes.'}
          </p>
        </motion.div>

        <div className="grid gap-4 md:grid-cols-2">
          {steps.map((step, index) => (
            <motion.article
              key={step.id ?? `${index}-${step.title ?? 'step'}`}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.06 }}
              className="glass-panel p-5"
            >
              <div className="mb-2 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span className="text-xs uppercase tracking-wide text-muted-foreground">
                  Step {index + 1}
                </span>
              </div>
              <h3 className="text-base font-semibold">{step.title ?? `Step ${index + 1}`}</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {step.description ?? 'Configure this step from CMS.'}
              </p>
              {step.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={step.image_url}
                  alt={step.title ?? `Workflow step ${index + 1}`}
                  className="mt-3 h-36 w-full rounded-md object-cover"
                  loading="lazy"
                />
              ) : null}
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
