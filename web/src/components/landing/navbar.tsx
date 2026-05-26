'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Menu, X } from 'lucide-react';
import { ROUTES } from '@/lib/routes';

const navLinks = [
  { name: 'Features', href: '#features' },
  { name: 'Pricing', href: '#pricing' },
  { name: 'FAQ', href: '#faq' },
  { name: 'Contact', href: '#contact' },
];

export function Navbar({ isSignedIn }: { isSignedIn: boolean }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const router = useRouter();

  const scrollToHome = () => {
    document.querySelector('#home')?.scrollIntoView({ behavior: 'smooth' });
    setIsMobileOpen(false);
  };

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
    setIsMobileOpen(false);
  };

  return (
    <>
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'bg-background/80 dark:bg-background-dark/80 backdrop-blur-xl border-b border-border/10 shadow-lg'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-20">
            <motion.button
              type="button"
              whileHover={{ scale: 1.05 }}
              className="flex-shrink-0 cursor-pointer bg-transparent border-0 p-0"
              onClick={scrollToHome}
            >
              <span className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                TenderIQ
              </span>
            </motion.button>

            <div className="hidden lg:flex items-center space-x-1">
              {navLinks.map((link) => (
                <motion.a
                  key={link.name}
                  href={link.href}
                  onClick={(e) => handleNavClick(e, link.href)}
                  whileHover={{ y: -2 }}
                  className="px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors relative group"
                >
                  {link.name}
                  <span className="absolute bottom-0 left-1/2 h-0.5 w-0 -translate-x-1/2 bg-primary transition-all group-hover:w-3/5" />
                </motion.a>
              ))}
            </div>

            <div className="hidden lg:flex items-center gap-3">
              {isSignedIn ? (
                <Button onClick={() => router.push(ROUTES.dashboard)} className="bg-primary hover:bg-primary/90">
                  Dashboard
                </Button>
              ) : (
                <>
                  <Button variant="ghost" asChild>
                    <Link href={ROUTES.signIn}>Log in</Link>
                  </Button>
                  <Button asChild className="bg-primary hover:bg-primary/90">
                    <Link href={ROUTES.signUp}>Sign up free</Link>
                  </Button>
                </>
              )}
            </div>

            <motion.button
              type="button"
              whileTap={{ scale: 0.9 }}
              className="lg:hidden p-2"
              onClick={() => setIsMobileOpen(!isMobileOpen)}
              aria-label="Toggle menu"
            >
              {isMobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </motion.button>
          </div>
        </div>
      </motion.nav>

      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            transition={{ type: 'spring', damping: 25 }}
            className="fixed inset-0 z-40 lg:hidden bg-background dark:bg-background-dark"
          >
            <div className="flex flex-col h-full pt-20 px-6 pb-6">
              <div className="space-y-2">
                {navLinks.map((link) => (
                  <a
                    key={link.name}
                    href={link.href}
                    onClick={(e) => handleNavClick(e, link.href)}
                    className="block px-4 py-3 text-lg font-medium text-foreground hover:bg-muted rounded-lg"
                  >
                    {link.name}
                  </a>
                ))}
              </div>
              <div className="mt-auto space-y-3">
                {isSignedIn ? (
                  <Button onClick={() => router.push(ROUTES.dashboard)} className="w-full bg-primary">
                    Dashboard
                  </Button>
                ) : (
                  <>
                    <Button asChild variant="outline" className="w-full">
                      <Link href={ROUTES.signIn}>Log in</Link>
                    </Button>
                    <Button asChild className="w-full bg-primary">
                      <Link href={ROUTES.signUp}>Sign up free</Link>
                    </Button>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
