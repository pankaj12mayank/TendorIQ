'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Upload, 
  FileSearch, 
  Brain, 
  ShieldAlert, 
  FileCheck, 
  Send,
  ArrowRight,
  CheckCircle2,
  Loader2
} from 'lucide-react';

const steps = [
  { icon: Upload, label: 'Upload', description: 'Upload tender documents' },
  { icon: FileSearch, label: 'Extract', description: 'AI extracts key data' },
  { icon: Brain, label: 'Analyze', description: 'ML analyzes requirements' },
  { icon: ShieldAlert, label: 'Risk Score', description: 'Identify potential risks' },
  { icon: FileCheck, label: 'Checklist', description: 'Generate compliance' },
  { icon: Send, label: 'Submit', description: 'Ready to submit' },
];

export function AIWorkflowSection() {
  const [activeStep, setActiveStep] = useState(0);
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev >= steps.length - 1) {
          setIsProcessing(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1500);

    return () => clearInterval(interval);
  }, [isProcessing]);

  const handleRestart = () => {
    setActiveStep(0);
    setIsProcessing(true);
  };

  return (
    <section
      id="workflow"
      className="scroll-mt-24 py-32 bg-gradient-to-b from-background to-muted/20"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-20"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 text-purple-500 text-sm font-medium mb-6">
            <Brain className="w-4 h-4" />
            AI Workflow
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Watch AI Process Your Tenders
          </h2>
          
          <p className="text-xl text-muted-foreground">
            Our intelligent workflow handles everything from document upload to submission preparation.
          </p>
        </motion.div>

        {/* Workflow Visualization */}
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Steps Timeline */}
          <div className="space-y-4">
            {steps.map((step, index) => (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-center gap-4 p-4 rounded-xl transition-all duration-300 ${
                  activeStep >= index
                    ? 'bg-primary/10 border border-primary/30'
                    : 'bg-muted/20 border border-transparent'
                }`}
              >
                <div className={`
                  w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300
                  ${activeStep >= index 
                    ? 'bg-primary text-white' 
                    : 'bg-muted text-muted-foreground'}
                `}>
                  {activeStep > index ? (
                    <CheckCircle2 className="w-6 h-6" />
                  ) : activeStep === index ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <step.icon className="w-6 h-6" />
                  )}
                </div>
                
                <div className="flex-1">
                  <div className={`font-semibold ${
                    activeStep >= index ? 'text-foreground' : 'text-muted-foreground'
                  }`}>
                    {step.label}
                  </div>
                  <div className="text-sm text-muted-foreground">{step.description}</div>
                </div>

                {activeStep > index && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="text-primary"
                  >
                    <CheckCircle2 className="w-5 h-5" />
                  </motion.div>
                )}
              </motion.div>
            ))}

            {/* Restart Button */}
            {!isProcessing && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={handleRestart}
                className="mt-4 text-sm text-primary hover:underline flex items-center gap-1"
              >
                <ArrowRight className="w-4 h-4 rotate-180" />
                Restart Demo
              </motion.button>
            )}
          </div>

          {/* Live Processing Preview */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative"
          >
            {/* Glow Effect */}
            <div className="absolute -inset-4 bg-gradient-to-r from-purple-500/20 via-primary/20 to-blue-500/20 blur-3xl rounded-3xl" />
            
            <div className="relative bg-card dark:bg-card-dark border border-border rounded-2xl p-8 min-h-[500px]">
              {/* Processing Indicator */}
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-sm font-medium">Processing tender...</span>
                </div>
                <span className="text-sm text-muted-foreground">
                  {Math.round((activeStep / (steps.length - 1)) * 100)}%
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-muted rounded-full mb-8 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 via-primary to-blue-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${(activeStep / (steps.length - 1)) * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>

              {/* Processing Steps Display */}
              <div className="space-y-4">
                {[
                  { label: 'Uploading document', status: activeStep >= 0 ? 'completed' : 'pending' },
                  { label: 'Extracting text with OCR', status: activeStep >= 1 ? (activeStep === 1 ? 'processing' : 'completed') : 'pending' },
                  { label: 'Analyzing requirements', status: activeStep >= 2 ? (activeStep === 2 ? 'processing' : 'completed') : 'pending' },
                  { label: 'Detecting risk factors', status: activeStep >= 3 ? (activeStep === 3 ? 'processing' : 'completed') : 'pending' },
                  { label: 'Generating compliance checklist', status: activeStep >= 4 ? (activeStep === 4 ? 'processing' : 'completed') : 'pending' },
                  { label: 'Preparing submission package', status: activeStep >= 5 ? (activeStep === 5 ? 'processing' : 'completed') : 'pending' },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center gap-3 p-3 rounded-lg bg-muted/30"
                  >
                    {item.status === 'completed' && (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    )}
                    {item.status === 'processing' && (
                      <Loader2 className="w-5 h-5 text-primary animate-spin" />
                    )}
                    {item.status === 'pending' && (
                      <div className="w-5 h-5 rounded-full border-2 border-muted-foreground/30" />
                    )}
                    <span className={`text-sm ${
                      item.status === 'completed' ? 'text-foreground' :
                      item.status === 'processing' ? 'text-primary font-medium' :
                      'text-muted-foreground'
                    }`}>
                      {item.label}
                    </span>
                  </motion.div>
                ))}
              </div>

              {/* Result Preview (appears at end) */}
              {activeStep === steps.length - 1 && !isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 p-4 bg-green-500/10 border border-green-500/30 rounded-xl"
                >
                  <div className="flex items-center gap-2 text-green-500 font-medium mb-2">
                    <CheckCircle2 className="w-5 h-5" />
                    Processing Complete!
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Ready to review and submit your tender response.
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}