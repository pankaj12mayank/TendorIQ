const faqs = [
  {
    q: 'Do I need my own AI API key?',
    a: 'Yes. Connect OpenAI, Anthropic, Gemini, or Ollama in Settings → AI.',
  },
  {
    q: 'Do you offer monthly plans?',
    a: 'Yes. TenderIQ Lite supports monthly subscriptions.',
  },
  {
    q: 'What file formats are supported?',
    a: 'PDF, DOC, and DOCX files up to 25MB each.',
  },
  {
    q: 'Can I export proposals as PDF?',
    a: 'Yes. Generate proposals from AI analysis and export branded PDFs.',
  },
];

export function FaqSection() {
  return (
    <section id="faq" className="w-full py-20">
      <div className="container mx-auto px-4 max-w-2xl">
        <h2 className="text-3xl font-bold text-center mb-10">Frequently asked questions</h2>
        <div className="space-y-4">
          {faqs.map((faq) => (
            <details key={faq.q} className="rounded-lg border p-4">
              <summary className="font-medium cursor-pointer">{faq.q}</summary>
              <p className="mt-2 text-sm text-muted-foreground">{faq.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}