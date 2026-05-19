'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { SignUpButton, useUser } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { 
  ArrowRight, 
  Play, 
  FileText, 
  Shield, 
  Zap,
  Brain,
  Sparkles
} from 'lucide-react';

export function HeroSection() {
  const router = useRouter();
  const { user } = useUser();
  const [isLoaded, setIsLoaded] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setIsLoaded(true);
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100,
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleGetStarted = () => {
    if (user) {
      router.push('/dashboard');
    } else {
      router.push('/onboarding');
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background to-background-dark">
        {/* Grid Pattern */}
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, hsl(var(--primary)) 0%, transparent 50%),
              linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
            backgroundSize: '100% 100%, 50px 50px, 50px 50px',
          }}
        />
        
        {/* Glowing Orbs */}
        <motion.div
          animate={{
            x: mousePosition.x * 3,
            y: mousePosition.y * 2,
          }}
          transition={{ type: 'spring', damping: 20 }}
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px]"
        />
        <motion.div
          animate={{
            x: -mousePosition.x * 2,
            y: -mousePosition.y * 3,
          }}
          transition={{ type: 'spring', damping: 20 }}
          className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/15 rounded-full blur-[100px]"
        />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isLoaded ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">AI-Powered Tender Management</span>
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={isLoaded ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6"
          >
            <span className="bg-gradient-to-r from-foreground via-foreground to-muted-foreground bg-clip-text text-transparent">
              Win More Tenders
            </span>
            <br />
            <span className="bg-gradient-to-r from-primary via-purple-500 to-primary bg-clip-text text-transparent">
              With AI Intelligence
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={isLoaded ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.5 }}
            className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-10"
          >
            Transform your tender process with intelligent automation, risk analysis, 
            and proposal generation. Built for enterprise teams who demand excellence.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isLoaded ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.7 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button 
                size="lg" 
                className="bg-primary hover:bg-primary/90 text-lg px-8 py-6"
                onClick={handleGetStarted}
              >
                Start Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button 
                size="lg" 
                variant="outline" 
                className="text-lg px-8 py-6"
              >
                <Play className="mr-2 w-5 h-5" />
                Watch Demo
              </Button>
            </motion.div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={isLoaded ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.9 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto"
          >
            {[
              { value: '70%', label: 'Time Saved' },
              { value: '3x', label: 'More Tenders' },
              { value: '99%', label: 'Accuracy' },
              { value: '500+', label: 'Companies' },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={isLoaded ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 1 + index * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold text-foreground mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 60, rotateX: 20 }}
          animate={isLoaded ? { opacity: 1, y: 0, rotateX: 0 } : {}}
          transition={{ delay: 1.2, duration: 1 }}
          className="relative mt-20 mx-auto max-w-5xl"
          style={{ perspective: '1000px' }}
        >
          {/* Glow */}
          <div className="absolute -inset-4 bg-gradient-to-r from-primary via-purple-500 to-primary opacity-30 blur-3xl rounded-3xl" />
          
          {/* Dashboard Mockup */}
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            className="relative bg-card dark:bg-card-dark border border-border rounded-2xl overflow-hidden shadow-2xl"
          >
            {/* Browser Header */}
            <div className="flex items-center gap-2 px-4 py-3 bg-muted/50 border-b border-border">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <div className="flex-1 mx-4 bg-background dark:bg-background-dark rounded-md px-4 py-1 text-sm text-muted-foreground">
                tenderiq.com/dashboard
              </div>
            </div>

            {/* Dashboard Content Preview */}
            <div className="p-6 bg-gradient-to-br from-background to-background-dark min-h-[400px]">
              <div className="grid grid-cols-3 gap-4 mb-6">
                {[
                  { icon: FileText, label: 'Active Tenders', value: '24' },
                  { icon: Brain, label: 'AI Analysis', value: '156' },
                  { icon: Shield, label: 'Risk Alerts', value: '3' },
                  { icon: Zap, label: 'Completed', value: '89' },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={isLoaded ? { opacity: 1, scale: 1 } : {}}
                    transition={{ delay: 1.4 + i * 0.1 }}
                    className="bg-card dark:bg-card-dark p-4 rounded-xl border border-border"
                  >
                    <item.icon className="w-6 h-6 text-primary mb-2" />
                    <div className="text-2xl font-bold">{item.value}</div>
                    <div className="text-sm text-muted-foreground">{item.label}</div>
                  </motion.div>
                ))}
              </div>

              {/* Recent Tenders */}
              <div className="space-y-3">
                {[
                  { name: 'IT Infrastructure Services', status: 'Active', progress: 75 },
                  { name: 'Office Supplies 2024', status: 'Review', progress: 100 },
                  { name: 'Construction Materials', status: 'Pending', progress: 45 },
                ].map((tender, i) => (
                  <motion.div
                    key={tender.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={isLoaded ? { opacity: 1, x: 0 } : {}}
                    transition={{ delay: 1.8 + i * 0.1 }}
                    className="flex items-center gap-4 p-3 bg-card/50 dark:bg-card-dark/50 rounded-lg"
                  >
                    <FileText className="w-5 h-5 text-muted-foreground" />
                    <div className="flex-1">
                      <div className="font-medium">{tender.name}</div>
                      <div className="w-full h-1 mt-1 bg-muted rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${tender.progress}%` }}
                          transition={{ delay: 2.2 + i * 0.1, duration: 0.8 }}
                          className="h-full bg-primary rounded-full"
                        />
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      tender.status === 'Active' ? 'bg-green-500/20 text-green-500' :
                      tender.status === 'Review' ? 'bg-blue-500/20 text-blue-500' :
                      'bg-yellow-500/20 text-yellow-500'
                    }`}>
                      {tender.status}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={isLoaded ? { opacity: 1 } : {}}
        transition={{ delay: 2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-6 h-10 rounded-full border-2 border-muted-foreground/30 flex justify-center pt-2"
        >
          <motion.div className="w-1 h-2 bg-muted-foreground/50 rounded-full" />
        </motion.div>
      </motion.div>
    </section>
  );
}