const steps = [
  { id: 'upload', title: 'Upload tender file', description: 'Upload PDF/DOCX and let the pipeline register the document job.' },
  { id: 'extract', title: 'Extract requirements', description: 'System parses sections, deadlines, and qualification criteria.' },
  { id: 'analyze', title: 'Run AI processing', description: 'AI analyzes compliance, scoring, and potential risk flags.' },
  { id: 'review', title: 'Review risk insights', description: 'Validate extracted risks and mark items requiring manual review.' },
  { id: 'propose', title: 'Generate proposal', description: 'Generate proposal draft and export PDF for submission.' },
];

export function HowItWorksSection() {
  return (
    <section className="w-full py-20">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-4">How it works</h2>
        <p className="text-center text-muted-foreground mb-12 max-w-xl mx-auto">
          Follow this 5-step workflow from upload to proposal export.
        </p>
        <div className="grid gap-6 md:grid-cols-5">
          {steps.map((step, i) => (
            <div key={step.id} className="relative text-center">
              <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold text-sm">
                {i + 1}
              </div>
              <h3 className="font-semibold text-sm mb-1">{step.title}</h3>
              <p className="text-xs text-muted-foreground">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}