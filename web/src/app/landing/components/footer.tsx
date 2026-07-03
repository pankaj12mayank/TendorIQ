import Link from 'next/link';

export function Footer() {
  return (
    <footer className="w-full border-t bg-muted/30 py-12">
      <div className="container mx-auto px-4">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <h3 className="font-bold text-lg mb-3">TenderIQ</h3>
            <p className="text-sm text-muted-foreground">AI-powered tender analysis and proposal generation platform.</p>
          </div>
          <div>
            <h4 className="font-semibold mb-3">Product</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="/#features">Features</Link></li>
              <li><Link href="/#pricing">Pricing</Link></li>
              <li><Link href="/#faq">FAQ</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">Company</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><span>About</span></li>
              <li><span>Contact</span></li>
              <li><span>Privacy</span></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">Legal</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><span>Terms of service</span></li>
              <li><span>Privacy policy</span></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t pt-6 text-center text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} TenderIQ. All rights reserved.
        </div>
      </div>
    </footer>
  );
}