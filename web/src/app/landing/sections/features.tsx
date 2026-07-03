import { FileSearch, FileText, Shield, Upload } from 'lucide-react';

const features = [
  {
    icon: Upload,
    title: 'AI document analysis',
    description: 'Parse PDFs and DOCX with your OpenAI, Anthropic, Gemini, or Ollama key.',
  },
  {
    icon: Shield,
    title: 'Risk & deadlines',
    description: 'Surface compliance risks, important clauses, and submission dates.',
  },
  {
    icon: FileText,
    title: 'Proposal generator',
    description: 'Draft sections from analysis, then export a branded PDF.',
  },
  {
    icon: FileSearch,
    title: 'Monthly subscription',
    description: 'Use monthly plans with predictable limits and renewal.',
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="w-full py-20 bg-muted/30">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12">Everything you need</h2>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {features.map((f) => (
            <div key={f.title} className="rounded-xl border bg-card p-6 text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <f.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground">{f.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}