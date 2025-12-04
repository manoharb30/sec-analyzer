import type { Metadata } from 'next';
import { Plus_Jakarta_Sans } from 'next/font/google';
import '@/styles/globals.css';

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['200', '300', '400', '500', '600', '700', '800'],
  variable: '--font-plus-jakarta',
});

export const metadata: Metadata = {
  title: 'LookInsight - SEC Filing Analysis Platform',
  description: 'Comprehensive SEC filing analysis and company insights powered by AI',
  keywords: ['SEC filings', 'financial analysis', 'company research', 'investment analysis'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${plusJakartaSans.className} bg-slate-950 text-slate-100 min-h-screen bg-grid bg-radial-overlay`}>
        <header className="sticky top-0 z-30 backdrop-blur-md supports-[backdrop-filter]:bg-slate-950/60 bg-slate-950/70 border-b border-white/10">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-xl bg-primary-500/20 border border-primary-400/30 grid place-items-center">
                  <svg className="h-4 w-4 text-primary-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-sm tracking-wider text-slate-300/90 uppercase font-semibold">
                    LookInsight
                  </h1>
                  <div className="text-[11px] text-slate-400">Investor-grade filing intelligence</div>
                </div>
              </div>
              <nav className="hidden md:flex space-x-2">
                <a
                  href="/"
                  className="btn-ghost"
                >
                  Home
                </a>
                <a
                  href="/about"
                  className="btn-ghost"
                >
                  About
                </a>
                <a
                  href="/docs"
                  className="btn-ghost"
                >
                  Documentation
                </a>
              </nav>
            </div>
          </div>
        </header>

        <main className="flex-1">
          {children}
        </main>

        <footer className="border-t border-white/10 py-6 text-center text-xs text-slate-500/80 mt-auto">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center">
              <p className="text-slate-400 text-sm">
                © {new Date().getFullYear()} LookInsight — Built for investor‑grade research
              </p>
              <div className="flex space-x-6">
                <a
                  href="/privacy"
                  className="text-slate-400 hover:text-slate-200 text-sm transition-colors"
                >
                  Privacy Policy
                </a>
                <a
                  href="/terms"
                  className="text-slate-400 hover:text-slate-200 text-sm transition-colors"
                >
                  Terms of Service
                </a>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}