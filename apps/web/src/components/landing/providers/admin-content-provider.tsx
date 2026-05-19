'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';

interface WebsiteContent {
  hero: {
    title: string;
    subtitle: string;
    cta_primary: string;
    cta_secondary: string;
  };
  features: Array<{
    id: string;
    title: string;
    description: string;
    icon: string;
  }>;
  pricing: {
    free: { name: string; price: string; features: string[] };
    pro: { name: string; price: string; features: string[] };
    enterprise: { name: string; price: string; features: string[] };
  };
  testimonials: Array<{
    id: string;
    name: string;
    role: string;
    company: string;
    content: string;
    avatar?: string;
  }>;
  faq: Array<{
    id: string;
    question: string;
    answer: string;
  }>;
}

interface WebsiteContentContextType {
  content: WebsiteContent | null;
  isLoading: boolean;
  isAdmin: boolean;
  updateContent: (section: string, data: any) => void;
}

const defaultContent: WebsiteContent = {
  hero: {
    title: 'AI-Powered Tender Management',
    subtitle: 'Streamline your tender process with intelligent automation, risk analysis, and proposal generation.',
    cta_primary: 'Start Free',
    cta_secondary: 'Book Demo',
  },
  features: [
    { id: '1', title: 'AI Extraction', description: 'Extract key data from documents automatically', icon: 'FileText' },
    { id: '2', title: 'Risk Analysis', description: 'Identify and assess tender risks instantly', icon: 'Shield' },
    { id: '3', title: 'Smart Checklists', description: 'Generate compliance checklists automatically', icon: 'CheckSquare' },
    { id: '4', title: 'Proposal Builder', description: 'Create winning proposals in minutes', icon: 'FileEdit' },
    { id: '5', title: 'Analytics', description: 'Track performance and insights', icon: 'BarChart' },
    { id: '6', title: 'Team Collaboration', description: 'Work together seamlessly', icon: 'Users' },
  ],
  pricing: {
    free: { name: 'Starter', price: '$0', features: ['5 Users', '100 Documents/mo', 'Basic Analytics'] },
    pro: { name: 'Professional', price: '$99', features: ['20 Users', '500 Documents/mo', 'AI Features', 'Priority Support'] },
    enterprise: { name: 'Enterprise', price: 'Custom', features: ['Unlimited Users', 'Unlimited Documents', 'Custom Integration', 'Dedicated Support'] },
  },
  testimonials: [
    { id: '1', name: 'Sarah Johnson', role: 'Procurement Manager', company: 'TechCorp', content: 'TenderIQ transformed our tender process. We\'ve saved 70% of time on document review.' },
    { id: '2', name: 'Michael Chen', role: 'CEO', company: 'BuildRight Inc', content: 'The AI risk analysis feature alone is worth it. It caught issues we would have missed.' },
    { id: '3', name: 'Emily Davis', role: 'Operations Director', company: 'GlobalServices', content: 'Finally, a tool that understands procurement. Our team loves it.' },
  ],
  faq: [
    { id: '1', question: 'How does AI extraction work?', answer: 'Our AI analyzes your tender documents and automatically extracts key information like dates, requirements, and deliverables.' },
    { id: '2', question: 'Is my data secure?', answer: 'Yes, we use enterprise-grade encryption and are SOC 2 compliant. Your data is never shared.' },
    { id: '3', question: 'Can I integrate with my existing tools?', answer: 'Yes, we offer API access and integrations with popular tools like Salesforce, SAP, and more.' },
  ],
};

const WebsiteContentContext = createContext<WebsiteContentContextType>({
  content: defaultContent,
  isLoading: false,
  isAdmin: false,
  updateContent: () => {},
});

export function useWebsiteContent() {
  return useContext(WebsiteContentContext);
}

export function AdminContentProvider({ children }: { children: ReactNode }) {
  const [content, setContent] = useState<WebsiteContent>(defaultContent);
  const [isAdmin, setIsAdmin] = useState(false);

  // In real app, fetch from API
  const { data, isLoading } = useQuery({
    queryKey: ['website-content'],
    queryFn: async () => {
      // Simulate API call - replace with actual fetch
      return defaultContent;
    },
    staleTime: Infinity,
  });

  useEffect(() => {
    if (data) {
      setContent(data);
    }
  }, [data]);

  const updateContent = (section: string, data: any) => {
    setContent((prev) => ({
      ...prev,
      [section]: { ...prev[section as keyof WebsiteContent], ...data },
    }));
  };

  return (
    <WebsiteContentContext.Provider value={{ content, isLoading, isAdmin, updateContent }}>
      {children}
    </WebsiteContentContext.Provider>
  );
}