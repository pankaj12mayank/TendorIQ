'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, Menu, X } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { cn } from '@/lib/utils';

const navLinks = [
  { name: 'Features', href: '#features' },
  { name: 'Pricing', href: '#pricing' },
  { name: 'FAQ', href: '#faq' },
  { name: 'Contact', href: '#contact' },
];

export function Navbar({
  isSignedIn,
  branding,
}: {
  isSignedIn: boolean;
  branding?: { logo_url?: string; brand_name?: string };
}) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 24);
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
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className={cn(
          'fixed top-0 left-0 right-0 z-50 transition-all duration-500',
          isScrolled ? 'nav-glass py-2' : 'bg-transparent py-4'
        )}
      >
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl bg-primary/20 ring-1 ring-primary/30 transition group-hover:ring-primary/50">
              {branding?.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={branding.logo_url} alt="Brand logo" className="h-9 w-9 object-cover" />
              ) : (
                <LayoutDashboard className="h-4 w-4 text-primary" />
              )}
            </div>
            <span className="font-display text-lg font-semibold tracking-tight text-gradient-cinematic-accent">
              {branding?.brand_name || 'TenderIQ'}
            </span>
          </Link>

          <nav className="hidden items-center gap-1 lg:flex">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition hover:bg-white/5 hover:text-foreground"
              >
                {link.name}
              </a>
            ))}
          </nav>

          <div className="hidden items-center gap-2 lg:flex">
            {isSignedIn ? (
              <Button className="btn-cinematic" onClick={() => router.push(ROUTES.dashboard)}>
                Open dashboard
              </Button>
            ) : (
              <>
                <Button variant="ghost" asChild className="text-muted-foreground hover:text-foreground">
                  <Link href={ROUTES.signIn}>Log in</Link>
                </Button>
                <Button asChild className="btn-cinematic">
                  <Link href={ROUTES.signUp}>Start now</Link>
                </Button>
              </>
            )}
          </div>

          <button
            type="button"
            className="rounded-lg p-2 text-foreground lg:hidden"
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            aria-label="Menu"
          >
            {isMobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </motion.header>

      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-background/95 backdrop-blur-xl lg:hidden"
          >
            <div className="flex h-full flex-col px-6 pb-8 pt-24">
              <div className="space-y-1">
                {navLinks.map((link) => (
                  <a
                    key={link.name}
                    href={link.href}
                    onClick={(e) => handleNavClick(e, link.href)}
                    className="block rounded-xl px-4 py-3 text-lg font-medium hover:bg-white/5"
                  >
                    {link.name}
                  </a>
                ))}
              </div>
              <div className="mt-auto space-y-3">
                {isSignedIn ? (
                  <Button className="btn-cinematic w-full" onClick={() => router.push(ROUTES.dashboard)}>
                    Dashboard
                  </Button>
                ) : (
                  <>
                    <Button asChild variant="outline" className="btn-cinematic-outline w-full">
                      <Link href={ROUTES.signIn}>Log in</Link>
                    </Button>
                    <Button asChild className="btn-cinematic w-full">
                      <Link href={ROUTES.signUp}>Start now</Link>
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
