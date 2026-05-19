'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Save, 
  Eye, 
  Edit3, 
  Image, 
  Type, 
  DollarSign,
  MessageSquare,
  Settings,
  RefreshCw
} from 'lucide-react';

type Tab = 'hero' | 'features' | 'pricing' | 'testimonials' | 'faq' | 'seo';

const tabs = [
  { id: 'hero', label: 'Hero Section', icon: Image },
  { id: 'features', label: 'Features', icon: Edit3 },
  { id: 'pricing', label: 'Pricing', icon: DollarSign },
  { id: 'testimonials', label: 'Testimonials', icon: MessageSquare },
  { id: 'faq', label: 'FAQ', icon: Settings },
  { id: 'seo', label: 'SEO', icon: Settings },
];

interface ContentEditorProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ContentEditor({ isOpen, onClose }: ContentEditorProps) {
  const [activeTab, setActiveTab] = useState<Tab>('hero');
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // State for each section
  const [heroContent, setHeroContent] = useState({
    title: 'AI-Powered Tender Management',
    subtitle: 'Streamline your tender process with intelligent automation, risk analysis, and proposal generation.',
    cta_primary: 'Start Free',
    cta_secondary: 'Book Demo',
  });

  const [features, setFeatures] = useState([
    { id: '1', title: 'AI Extraction', description: 'Extract key data from documents automatically' },
    { id: '2', title: 'Risk Analysis', description: 'Identify and assess tender risks instantly' },
    { id: '3', title: 'Smart Checklists', description: 'Generate compliance checklists automatically' },
    { id: '4', title: 'Proposal Builder', description: 'Create winning proposals in minutes' },
    { id: '5', title: 'Analytics', description: 'Track performance and insights' },
    { id: '6', title: 'Team Collaboration', description: 'Work together seamlessly' },
  ]);

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    setHasChanges(false);
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      className="fixed right-0 top-0 bottom-0 w-[500px] bg-background border-l border-border shadow-2xl z-50 overflow-y-auto"
    >
      {/* Header */}
      <div className="sticky top-0 bg-background border-b border-border p-4 flex items-center justify-between z-10">
        <h2 className="text-lg font-bold">Website Content Editor</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-lg"
          >
            ×
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as Tab)}
            className={`flex items-center gap-2 px-4 py-3 text-sm whitespace-nowrap border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'hero' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Hero Title</label>
              <input
                type="text"
                value={heroContent.title}
                onChange={(e) => {
                  setHeroContent({ ...heroContent, title: e.target.value });
                  setHasChanges(true);
                }}
                className="w-full p-3 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Subtitle</label>
              <textarea
                value={heroContent.subtitle}
                onChange={(e) => {
                  setHeroContent({ ...heroContent, subtitle: e.target.value });
                  setHasChanges(true);
                }}
                rows={3}
                className="w-full p-3 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Primary CTA</label>
                <input
                  type="text"
                  value={heroContent.cta_primary}
                  onChange={(e) => {
                    setHeroContent({ ...heroContent, cta_primary: e.target.value });
                    setHasChanges(true);
                  }}
                  className="w-full p-3 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Secondary CTA</label>
                <input
                  type="text"
                  value={heroContent.cta_secondary}
                  onChange={(e) => {
                    setHeroContent({ ...heroContent, cta_secondary: e.target.value });
                    setHasChanges(true);
                  }}
                  className="w-full p-3 bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'features' && (
          <div className="space-y-4">
            {features.map((feature, index) => (
              <div key={feature.id} className="p-4 bg-muted rounded-lg border border-border">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium">Feature {index + 1}</span>
                </div>
                <input
                  type="text"
                  value={feature.title}
                  onChange={(e) => {
                    const newFeatures = [...features];
                    newFeatures[index].title = e.target.value;
                    setFeatures(newFeatures);
                    setHasChanges(true);
                  }}
                  placeholder="Feature title"
                  className="w-full p-2 mb-2 bg-background rounded border border-border"
                />
                <textarea
                  value={feature.description}
                  onChange={(e) => {
                    const newFeatures = [...features];
                    newFeatures[index].description = e.target.value;
                    setFeatures(newFeatures);
                    setHasChanges(true);
                  }}
                  placeholder="Feature description"
                  rows={2}
                  className="w-full p-2 bg-background rounded border border-border"
                />
              </div>
            ))}
          </div>
        )}

        {activeTab === 'pricing' && (
          <div className="space-y-6">
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-4">Starter Plan</h4>
              <input
                type="text"
                defaultValue="$29"
                className="w-full p-2 mb-2 bg-background rounded border border-border"
              />
              <textarea
                defaultValue="Perfect for small teams getting started"
                rows={2}
                className="w-full p-2 bg-background rounded border border-border"
              />
            </div>
            <div className="p-4 bg-muted rounded-lg border-primary/30 border-2">
              <h4 className="font-medium mb-4">Professional Plan</h4>
              <input
                type="text"
                defaultValue="$99"
                className="w-full p-2 mb-2 bg-background rounded border border-border"
              />
              <textarea
                defaultValue="For growing teams with advanced needs"
                rows={2}
                className="w-full p-2 bg-background rounded border border-border"
              />
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-4">Enterprise Plan</h4>
              <input
                type="text"
                defaultValue="Custom"
                className="w-full p-2 mb-2 bg-background rounded border border-border"
              />
              <textarea
                defaultValue="For large organizations with custom needs"
                rows={2}
                className="w-full p-2 bg-background rounded border border-border"
              />
            </div>
          </div>
        )}

        {activeTab === 'seo' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Meta Title</label>
              <input
                type="text"
                defaultValue="TenderIQ - AI-Powered Tender Management Platform"
                className="w-full p-3 bg-muted rounded-lg border border-border"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Meta Description</label>
              <textarea
                defaultValue="Streamline your tender process with TenderIQ's AI-powered automation, risk analysis, and proposal generation."
                rows={3}
                className="w-full p-3 bg-muted rounded-lg border border-border"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Keywords</label>
              <input
                type="text"
                defaultValue="tender management, AI, procurement, proposal automation"
                className="w-full p-3 bg-muted rounded-lg border border-border"
              />
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="sticky bottom-0 bg-background border-t border-border p-4 flex items-center justify-between">
        <button
          onClick={onClose}
          className="px-4 py-2 text-muted-foreground hover:text-foreground"
        >
          Preview Site
        </button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium ${
            hasChanges
              ? 'bg-primary text-white'
              : 'bg-muted text-muted-foreground'
          }`}
        >
          {isSaving ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Changes
            </>
          )}
        </motion.button>
      </div>
    </motion.div>
  );
}