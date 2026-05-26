'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  ShieldAlert, 
  CheckSquare, 
  FileEdit,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  BarChart3
} from 'lucide-react';

const demos = [
  {
    id: 'tender',
    icon: FileText,
    title: 'Tender Analysis',
    description: 'AI-powered extraction and analysis',
    color: 'from-blue-500 to-cyan-500',
    preview: {
      title: 'IT Infrastructure Services',
      summary: 'Government tender for comprehensive IT infrastructure upgrade...',
      keyPoints: ['Server hardware procurement', 'Network security implementation', 'Cloud migration services'],
      confidence: 94,
    },
  },
  {
    id: 'risk',
    icon: ShieldAlert,
    title: 'Risk Detection',
    description: 'Identify compliance and risk issues',
    color: 'from-red-500 to-orange-500',
    preview: {
      title: 'Risk Assessment Report',
      items: [
        { level: 'high', text: 'Missing insurance certificates required' },
        { level: 'medium', text: 'Timeline may conflict with holiday period' },
        { level: 'low', text: 'Budget slightly below industry average' },
      ],
    },
  },
  {
    id: 'checklist',
    icon: CheckSquare,
    title: 'Smart Checklist',
    description: 'Auto-generated compliance checklist',
    color: 'from-green-500 to-emerald-500',
    preview: {
      items: [
        { done: true, text: 'Company registration documents' },
        { done: true, text: 'Tax clearance certificates' },
        { done: false, text: 'Previous project references' },
        { done: false, text: 'Staff qualifications proof' },
        { done: false, text: 'Financial statements (last 3 years)' },
      ],
    },
  },
  {
    id: 'proposal',
    icon: FileEdit,
    title: 'Proposal Generator',
    description: 'AI-assisted proposal creation',
    color: 'from-purple-500 to-pink-500',
    preview: {
      sections: [
        { title: 'Executive Summary', progress: 100 },
        { title: 'Technical Approach', progress: 85 },
        { title: 'Implementation Plan', progress: 60 },
        { title: 'Pricing Proposal', progress: 45 },
      ],
    },
  },
];

export function DemoPreviewSection() {
  const [activeDemo, setActiveDemo] = useState(demos[0]);

  return (
    <section id="demo" className="scroll-mt-24 py-32 relative">
      {/* Background */}
      <div className="absolute inset-0 bg-muted/20" />
      
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-20"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 text-blue-500 text-sm font-medium mb-6">
            <BarChart3 className="w-4 h-4" />
            Live Previews
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            See It In Action
          </h2>
          
          <p className="text-xl text-muted-foreground">
            Explore how each feature transforms your tender workflow.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-12 gap-8">
          {/* Demo Selection */}
          <div className="lg:col-span-4 space-y-3">
            {demos.map((demo) => (
              <motion.button
                key={demo.id}
                whileHover={{ x: 5 }}
                onClick={() => setActiveDemo(demo)}
                className={`w-full text-left p-4 rounded-xl transition-all duration-300 ${
                  activeDemo.id === demo.id
                    ? 'bg-primary/10 border border-primary/30'
                    : 'bg-card dark:bg-card-dark border border-border hover:border-primary/30'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${demo.color} flex items-center justify-center`}>
                    <demo.icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <div className="font-semibold">{demo.title}</div>
                    <div className="text-sm text-muted-foreground">{demo.description}</div>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>

          {/* Demo Preview */}
          <div className="lg:col-span-8">
            <motion.div
              key={activeDemo.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative"
            >
              {/* Glow */}
              <div className={`absolute -inset-2 bg-gradient-to-r ${activeDemo.color} opacity-20 blur-2xl rounded-2xl`} />
              
              <div className="relative bg-card dark:bg-card-dark border border-border rounded-2xl p-8 min-h-[500px]">
                {/* Demo Content Based on Type */}
                {activeDemo.id === 'tender' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-bold mb-2">{activeDemo.preview.title}</h3>
                      <p className="text-muted-foreground">{activeDemo.preview.summary}</p>
                    </div>
                    
                    <div className="space-y-2">
                      <span className="text-sm font-medium">Key Requirements:</span>
                      {activeDemo.preview.keyPoints.map((point, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.2 }}
                          className="flex items-center gap-2 text-sm"
                        >
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          {point}
                        </motion.div>
                      ))}
                    </div>

                    <div className="p-4 bg-muted/30 rounded-xl">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">AI Confidence Score</span>
                        <span className="text-2xl font-bold text-primary">{activeDemo.preview.confidence}%</span>
                      </div>
                      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${activeDemo.preview.confidence}%` }}
                          className="h-full bg-primary rounded-full"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {activeDemo.id === 'risk' && (
                  <div className="space-y-4">
                    <h3 className="text-xl font-bold">{activeDemo.preview.title}</h3>
                    {activeDemo.preview.items.map((item, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.2 }}
                        className={`p-4 rounded-xl border ${
                          item.level === 'high' ? 'bg-red-500/10 border-red-500/30' :
                          item.level === 'medium' ? 'bg-yellow-500/10 border-yellow-500/30' :
                          'bg-blue-500/10 border-blue-500/30'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <AlertTriangle className={`w-5 h-5 ${
                            item.level === 'high' ? 'text-red-500' :
                            item.level === 'medium' ? 'text-yellow-500' :
                            'text-blue-500'
                          }`} />
                          <span className="text-sm">{item.text}</span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}

                {activeDemo.id === 'checklist' && (
                  <div className="space-y-3">
                    <h3 className="text-xl font-bold mb-4">Compliance Checklist</h3>
                    {activeDemo.preview.items.map((item, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.15 }}
                        className="flex items-center gap-3 p-3 rounded-lg bg-muted/30"
                      >
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                          item.done ? 'bg-green-500 border-green-500' : 'border-muted-foreground/30'
                        }`}>
                          {item.done && <CheckCircle className="w-3 h-3 text-white" />}
                        </div>
                        <span className={item.done ? 'text-muted-foreground line-through' : ''}>
                          {item.text}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                )}

                {activeDemo.id === 'proposal' && (
                  <div className="space-y-4">
                    <h3 className="text-xl font-bold">Proposal Progress</h3>
                    {activeDemo.preview.sections.map((section, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.15 }}
                        className="p-4 rounded-lg bg-muted/30"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{section.title}</span>
                          <span className="text-sm text-muted-foreground">{section.progress}%</span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${section.progress}%` }}
                            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                          />
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}

                {/* Learn More Link */}
                <div className="mt-8 pt-6 border-t border-border">
                  <button className="flex items-center gap-2 text-primary font-medium hover:underline">
                    Try this feature <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}