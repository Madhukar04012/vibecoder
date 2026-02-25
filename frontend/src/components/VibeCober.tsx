import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  SiPython,
  SiFastapi,
  SiReact,
  SiTypescript,
  SiDocker,
  SiPostgresql,
  SiVercel,
  SiGithub,
  SiAnthropic,
  SiNvidia,
  SiOpenai,
  SiSqlite,
  SiTailwindcss,
  SiVite,
  SiNodedotjs,
} from 'react-icons/si';
import {
  ArrowRight,
  Sparkles,
  Code2,
  Zap,
  CheckCircle2,
  Terminal,
  Folder,
  ChevronRight,
  ChevronDown,
  Play,
  Download,
  Github,
  Twitter,
  Mail,
  Menu,
  X,
  Sun,
  Moon,
  Home,
  Compass,
  CreditCard,
  Info,
  Users,
  Layers,
  Globe,
  Cpu,
  Rocket,
} from 'lucide-react';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { DottedSurface } from '@/components/ui/dotted-surface';
import { AnimeNavBar } from '@/components/ui/anime-navbar';
import { PricingSection } from '@/components/blocks/pricing-section';
import { useTheme } from '@/contexts/ThemeContext';
import { cn } from '@/lib/utils';

type Page = 'landing' | 'generator' | 'preview' | 'build';

interface ProjectData {
  idea: string;
  modules: string[];
  techStack: string[];
  structure: FolderNode[];
}

interface FolderNode {
  name: string;
  type: 'file' | 'folder';
  children?: FolderNode[];
}

const PAYMENT_FREQUENCIES = ["monthly", "yearly"]

const PRICING_TIERS = [
  {
    id: "individuals",
    name: "Individuals",
    price: { monthly: "Free", yearly: "Free" },
    description: "For your hobby projects",
    features: [
      "Free email alerts",
      "3-minute checks",
      "Automatic data enrichment",
      "10 monitors",
      "Up to 3 seats",
    ],
    cta: "Get started",
  },
  {
    id: "teams",
    name: "Teams",
    price: { monthly: 90, yearly: 75 },
    description: "Great for small businesses",
    features: [
      "Unlimited phone calls",
      "30 second checks",
      "Single-user account",
      "20 monitors",
      "Up to 6 seats",
    ],
    cta: "Get started",
    popular: true,
  },
  {
    id: "organizations",
    name: "Organizations",
    price: { monthly: 120, yearly: 100 },
    description: "Great for large businesses",
    features: [
      "Unlimited phone calls",
      "15 second checks",
      "Single-user account",
      "50 monitors",
      "Up to 10 seats",
    ],
    cta: "Get started",
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: { monthly: "Custom", yearly: "Custom" },
    description: "For multiple teams",
    features: [
      "Everything in Organizations",
      "Up to 5 team members",
      "100 monitors",
      "15 status pages",
      "200+ integrations",
    ],
    cta: "Contact Us",
    highlighted: true,
  },
]

const ANIME_NAV_ITEMS = [
  { name: 'Home', url: '#manifesto', icon: Home },
  { name: 'Discover', url: '#discover', icon: Compass },
  { name: 'Pricing', url: '#pricing', icon: CreditCard },
  { name: 'About', url: '#careers', icon: Info },
];

const TECH_LOGOS: { icon: React.ElementType; label: string; color: string }[] = [
  { icon: SiPython, label: 'Python', color: '#3776AB' },
  { icon: SiFastapi, label: 'FastAPI', color: '#009688' },
  { icon: SiReact, label: 'React', color: '#61DAFB' },
  { icon: SiTypescript, label: 'TypeScript', color: '#3178C6' },
  { icon: SiDocker, label: 'Docker', color: '#2496ED' },
  { icon: SiPostgresql, label: 'PostgreSQL', color: '#336791' },
  { icon: SiVercel, label: 'Vercel', color: '#ffffff' },
  { icon: SiGithub, label: 'GitHub', color: '#ffffff' },
  { icon: SiAnthropic, label: 'Anthropic', color: '#D4956A' },
  { icon: SiNvidia, label: 'NVIDIA', color: '#76B900' },
  { icon: SiOpenai, label: 'OpenAI', color: '#74aa9c' },
  { icon: SiSqlite, label: 'SQLite', color: '#003B57' },
  { icon: SiTailwindcss, label: 'Tailwind CSS', color: '#06B6D4' },
  { icon: SiVite, label: 'Vite', color: '#646CFF' },
  { icon: SiNodedotjs, label: 'Node.js', color: '#339933' },
];

const VibeCober: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [idea, setIdea] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [buildProgress, setBuildProgress] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isChatFocused, setIsChatFocused] = useState(false);
  const [cookFontIndex, setCookFontIndex] = useState(0);
  const landingTextareaRef = React.useRef<HTMLTextAreaElement>(null);

  // 7 fonts + colors for the cycling "cook" word
  const cookStyles = [
    { fontFamily: "'Playfair Display', serif", color: '#818cf8' },   // indigo-400
    { fontFamily: "'Pacifico', cursive", color: '#a78bfa' },          // violet-400
    { fontFamily: "'Space Mono', monospace", color: '#38bdf8' },      // sky-400
    { fontFamily: "'Permanent Marker', cursive", color: '#f472b6' },  // pink-400
    { fontFamily: "'Satisfy', cursive", color: '#34d399' },           // emerald-400
    { fontFamily: "'Righteous', sans-serif", color: '#fb923c' },      // orange-400
    { fontFamily: "'Orbitron', sans-serif", color: '#c084fc' },       // purple-400
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCookFontIndex(prev => (prev + 1) % 7);
    }, 800);
    return () => clearInterval(interval);
  }, []);

  // Typing placeholder animation (moved from renderLandingPage to top level to obey React hooks rules)
  const [placeholder, setPlaceholder] = useState('');
  const fullPlaceholder = 'Make me a SaaS app with authentication and payments...';

  useEffect(() => {
    if (isChatFocused || idea.length > 0) return;
    let index = 0;
    const interval = setInterval(() => {
      if (index <= fullPlaceholder.length) {
        setPlaceholder(fullPlaceholder.slice(0, index));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [isChatFocused, idea]);

  const handleGenerate = async () => {
    if (!idea.trim()) return;

    setIsGenerating(true);
    setCurrentPage('generator');

    setTimeout(() => {
      setProjectData({
        idea,
        modules: [
          'Authentication',
          'Database',
          'API Routes',
          'Frontend UI',
          'State Management',
        ],
        techStack: [
          'React',
          'TypeScript',
          'Tailwind CSS',
          'Node.js',
          'PostgreSQL',
          'Prisma',
        ],
        structure: [
          {
            name: 'src',
            type: 'folder',
            children: [
              {
                name: 'components',
                type: 'folder',
                children: [
                  { name: 'ui', type: 'folder' },
                  { name: 'layout', type: 'folder' },
                ],
              },
              {
                name: 'pages',
                type: 'folder',
                children: [
                  { name: 'index.tsx', type: 'file' },
                  { name: 'dashboard.tsx', type: 'file' },
                ],
              },
              { name: 'lib', type: 'folder' },
              { name: 'hooks', type: 'folder' },
            ],
          },
          {
            name: 'server',
            type: 'folder',
            children: [
              { name: 'routes', type: 'folder' },
              { name: 'middleware', type: 'folder' },
            ],
          },
          { name: 'package.json', type: 'file' },
          { name: 'tsconfig.json', type: 'file' },
        ],
      });
      setIsGenerating(false);
      setCurrentPage('preview');
    }, 2000);
  };

  const handleBuild = () => {
    setCurrentPage('build');
    setBuildProgress(0);

    const interval = setInterval(() => {
      setBuildProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  const renderNavbar = () => (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-6 py-3 sm:py-4 pt-[env(safe-area-inset-top)]"
    >
      <div className="max-w-7xl mx-auto">
        <div className="bg-background/80 backdrop-blur-xl border border-border rounded-full px-4 sm:px-6 py-2.5 sm:py-3 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-8">
            <button
              onClick={() => setCurrentPage('landing')}
              className="flex items-center gap-2 text-lg font-semibold text-foreground"
            >
              <Sparkles className="w-5 h-5 text-primary" />
              <span>Vibecoder</span>
            </button>
            <div className="hidden md:flex items-center gap-6 text-sm">
              <a
                href="#manifesto"
                onClick={(e) => { e.preventDefault(); document.querySelector('#manifesto')?.scrollIntoView({ behavior: 'smooth' }); }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Manifesto
              </a>
              <a
                href="#careers"
                onClick={(e) => { e.preventDefault(); document.querySelector('#careers')?.scrollIntoView({ behavior: 'smooth' }); }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Careers
              </a>
              <a
                href="#discover"
                onClick={(e) => { e.preventDefault(); document.querySelector('#discover')?.scrollIntoView({ behavior: 'smooth' }); }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Discover
              </a>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              className="rounded-lg"
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </Button>
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Login
              </Button>
            </Link>
            <Link to="/signup">
              <Button size="sm">Sign Up</Button>
            </Link>
          </div>
          <button
            className="md:hidden p-2 -m-2 min-h-[44px] min-w-[44px] flex items-center justify-center touch-manipulation"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden mt-4 bg-background/95 backdrop-blur-xl border border-border rounded-2xl p-6 max-w-7xl mx-auto"
          >
            <div className="flex flex-col gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  toggleTheme();
                  setMobileMenuOpen(false);
                }}
                className="justify-start"
              >
                {theme === 'dark' ? (
                  <Sun className="w-4 h-4 mr-2" />
                ) : (
                  <Moon className="w-4 h-4 mr-2" />
                )}
                {theme === 'dark' ? 'Light mode' : 'Dark mode'}
              </Button>
              <a
                href="#manifesto"
                onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); document.querySelector('#manifesto')?.scrollIntoView({ behavior: 'smooth' }); }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Manifesto
              </a>
              <a
                href="#careers"
                onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); document.querySelector('#careers')?.scrollIntoView({ behavior: 'smooth' }); }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Careers
              </a>
              <a
                href="#discover"
                onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); document.querySelector('#discover')?.scrollIntoView({ behavior: 'smooth' }); }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Discover
              </a>
              <Separator />
              <Link to="/login">
                <Button variant="ghost" className="w-full justify-start">Login</Button>
              </Link>
              <Link to="/signup">
                <Button className="w-full justify-start">Sign Up</Button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );

  const renderLandingPage = () => {
    return (
      <div className="relative min-h-screen">
        <DottedSurface className="opacity-90" />
        <div
          aria-hidden="true"
          className={cn(
            'pointer-events-none fixed inset-0 z-[1]',
            'bg-[radial-gradient(ellipse_at_center,hsl(var(--foreground)/0.06),transparent_60%)]',
            'blur-[15px]'
          )}
        />
        <div
          className={cn(
            'pointer-events-none fixed inset-0 z-[2]',
            theme === 'dark'
              ? 'bg-gradient-to-b from-background/40 via-background/20 to-background/50'
              : 'bg-gradient-to-b from-background/25 via-background/10 to-background/35'
          )}
        />

        <section id="manifesto" className="relative z-20 min-h-screen flex items-center justify-center px-4 sm:px-6 pt-28 sm:pt-36 md:pt-32 pb-12 sm:pb-20">
          <div className="max-w-4xl mx-auto text-center space-y-6 sm:space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1
                className={cn(
                  'text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter mb-4 sm:mb-6 uppercase',
                )}
              >
                <span
                  className={theme === 'dark' ? 'text-white' : 'text-[#1a1a2e]'}
                >
                  VIDE
                </span>
                <span
                  style={{
                    background: 'linear-gradient(135deg, #2D5CFE 0%, #6366f1 35%, #7c3aed 60%, #a855f7 85%, #9333ea 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  CODER
                </span>
              </h1>
              <p
                className={cn(
                  'text-lg sm:text-xl md:text-2xl lg:text-3xl font-normal mb-8 sm:mb-12 px-2',
                  theme === 'dark' ? 'text-muted-foreground' : 'text-[#555555]'
                )}
              >
                Code At Vibe{' '}
                <span
                  style={{
                    fontFamily: cookStyles[cookFontIndex].fontFamily,
                    transition: 'font-family 0.4s ease-in-out',
                    display: 'inline-block',
                  }}
                >
                  Speed
                </span>
              </p>
            </motion.div>

            {/* ── Minimal Expanding Chat Box ── */}
            <div
              className={cn(
                'relative mx-auto w-full px-3 sm:px-0 transition-all duration-500 ease-in-out',
                isChatFocused ? 'sm:max-w-[52rem]' : 'sm:max-w-[40rem]'
              )}
              style={{ zIndex: 9999 }}
            >
              <div
                className={cn(
                  'relative rounded-2xl transition-all duration-300 cursor-text',
                  theme === 'dark'
                    ? 'bg-[#111318] border border-white/[0.06]'
                    : 'bg-white border border-neutral-200/80',
                  isChatFocused
                    ? theme === 'dark'
                      ? 'shadow-[0_0_0_1px_rgba(99,102,241,0.2),0_2px_20px_-4px_rgba(99,102,241,0.1)]'
                      : 'shadow-[0_0_0_1px_rgba(99,102,241,0.15),0_2px_20px_-4px_rgba(99,102,241,0.08)]'
                    : theme === 'dark'
                      ? 'shadow-md'
                      : 'shadow-sm'
                )}
              >
                {/* Textarea */}
                <textarea
                  ref={landingTextareaRef}
                  id="landing-chat-textarea"
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  onFocus={() => setIsChatFocused(true)}
                  onBlur={() => setIsChatFocused(false)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey && idea.trim()) {
                      e.preventDefault();
                      handleGenerate();
                    }
                  }}
                  placeholder={placeholder || 'What are we building today?'}
                  rows={isChatFocused ? 4 : 2}
                  className={cn(
                    'w-full border-none bg-transparent outline-none ring-0 focus:ring-0 focus:outline-none',
                    'resize-none leading-relaxed transition-all duration-300',
                    'text-base sm:text-lg px-5 pt-5 pb-3',
                    theme === 'dark'
                      ? 'text-white/90 placeholder:text-white/25'
                      : 'text-neutral-900 placeholder:text-neutral-400'
                  )}
                />

                {/* Suggestion chips — only visible when focused & empty */}
                <AnimatePresence>
                  {isChatFocused && !idea.trim() && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden px-5 pb-2"
                    >
                      <div className="flex flex-wrap gap-2">
                        {[
                          { label: 'SaaS App', icon: Layers },
                          { label: 'API Backend', icon: Cpu },
                          { label: 'Portfolio Site', icon: Globe },
                          { label: 'E-commerce', icon: Rocket },
                        ].map(({ label, icon: Icon }) => (
                          <button
                            key={label}
                            onMouseDown={(e) => {
                              e.preventDefault();
                              setIdea(label);
                            }}
                            className={cn(
                              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium',
                              'transition-all duration-150 border',
                              theme === 'dark'
                                ? 'border-white/[0.06] bg-white/[0.03] text-white/40 hover:text-white/60 hover:border-white/[0.12]'
                                : 'border-neutral-200 bg-neutral-50 text-neutral-400 hover:text-neutral-600 hover:border-neutral-300'
                            )}
                          >
                            <Icon className="w-3 h-3" />
                            {label}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Bottom bar */}
                <div
                  className={cn(
                    'flex items-center justify-between px-5 py-3',
                    theme === 'dark'
                      ? 'border-t border-white/[0.04]'
                      : 'border-t border-neutral-100'
                  )}
                >
                  <span className={cn(
                    'text-[11px] tracking-wide',
                    theme === 'dark' ? 'text-white/20' : 'text-neutral-300'
                  )}>
                    <kbd className="font-mono text-[10px]">⏎</kbd> to generate
                  </span>

                  <Button
                    onClick={handleGenerate}
                    disabled={!idea.trim()}
                    size="sm"
                    className={cn(
                      'rounded-full px-5 h-9 text-sm font-medium transition-all duration-200',
                      idea.trim()
                        ? 'bg-[#6366f1] hover:bg-[#5558e6] text-white'
                        : theme === 'dark'
                          ? 'bg-white/[0.04] text-white/20 cursor-not-allowed'
                          : 'bg-neutral-100 text-neutral-300 cursor-not-allowed'
                    )}
                  >
                    Generate
                    <ArrowRight className="ml-1.5 w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Tech Logo Marquee ── */}
        <section className="relative py-10 sm:py-14 overflow-hidden border-y border-border/40">
          <p className="text-center text-xs uppercase tracking-[0.25em] text-muted-foreground/50 mb-6 sm:mb-8 font-medium">
            Built with the world's best tech
          </p>
          <div className="relative flex">
            {/* fade edges */}
            <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-r from-background to-transparent" />
            <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-l from-background to-transparent" />

            <div
              className="flex gap-12 sm:gap-16 items-center animate-marquee whitespace-nowrap"
              style={{ animation: 'marquee 28s linear infinite' }}
            >
              {TECH_LOGOS.concat(TECH_LOGOS).map((tech, i) => (
                <div
                  key={i}
                  className="flex flex-col items-center gap-2 group flex-shrink-0"
                  title={tech.label}
                >
                  <tech.icon
                    size={36}
                    style={{ color: tech.color }}
                    className="opacity-60 group-hover:opacity-100 transition-opacity duration-300"
                  />
                  <span className="text-[10px] text-muted-foreground/50 group-hover:text-muted-foreground transition-colors duration-300 tracking-wide uppercase">
                    {tech.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <style>{`
            @keyframes marquee {
              0%   { transform: translateX(0); }
              100% { transform: translateX(-50%); }
            }
          `}</style>
        </section>

        <section id="how-it-works" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6">
          <div className="max-w-5xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16 sm:mb-20"
            >
              <span className="inline-block text-xs font-semibold uppercase tracking-widest text-primary/70 mb-3">The process</span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground">From idea to running code</h2>
              <p className="mt-4 text-muted-foreground text-base sm:text-lg max-w-xl mx-auto">No boilerplate. No copy-pasting Stack Overflow. Just describe what you need.</p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 relative">
              {/* connector line — desktop only */}
              <div className="hidden md:block absolute top-8 left-[calc(16.67%+1rem)] right-[calc(16.67%+1rem)] h-px bg-border/60" />

              {[
                {
                  num: '01',
                  icon: Sparkles,
                  title: 'Describe your idea',
                  desc: 'Type a plain sentence — "FastAPI backend with JWT auth and PostgreSQL". That\'s it. No templates, no wizards.',
                  hint: 'Natural language input',
                },
                {
                  num: '02',
                  icon: Code2,
                  title: 'Agents build it',
                  desc: '7 specialised agents coordinate — PM, Architect, Engineer, QA, DevOps — each doing exactly one job, correctly.',
                  hint: 'MetaGPT-inspired pipeline',
                },
                {
                  num: '03',
                  icon: Zap,
                  title: 'Ship it',
                  desc: 'Download a zip, push to GitHub, or deploy straight to Vercel. The project is already tested and Dockerised.',
                  hint: 'Production-ready output',
                },
              ].map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.15 }}
                  className="relative"
                >
                  <div className={cn(
                    'relative rounded-2xl border p-6 sm:p-8 h-full transition-all duration-300',
                    'bg-card hover:bg-card/80 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5',
                    'border-border'
                  )}>
                    {/* step number */}
                    <span className="text-[11px] font-mono font-bold text-primary/50 tracking-widest mb-4 block">{step.num}</span>
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-5" style={{ background: 'hsl(var(--primary)/0.1)' }}>
                      <step.icon className="w-5 h-5 text-primary" />
                    </div>
                    <h3 className="text-lg sm:text-xl font-semibold text-foreground mb-2">{step.title}</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">{step.desc}</p>
                    <span className="mt-5 inline-block text-[11px] font-medium text-primary/60 bg-primary/5 px-2.5 py-1 rounded-full">{step.hint}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="discover" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16 sm:mb-20"
            >
              <span className="inline-block text-xs font-semibold uppercase tracking-widest text-primary/70 mb-3">Why it works</span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground">Built for developers who ship</h2>
              <p className="mt-4 text-muted-foreground text-base sm:text-lg max-w-xl mx-auto">No toy demos. No hallucinated code. Just real projects you can actually push to production.</p>
            </motion.div>

            {/* Stats row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-12">
              {[
                { stat: '7', label: 'Specialised agents' },
                { stat: '< 2 min', label: 'Avg. gen time' },
                { stat: '100%', label: 'Real file output' },
                { stat: '$0', label: 'To get started' },
              ].map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  className="text-center rounded-2xl border border-border/60 bg-card/50 px-4 py-6"
                >
                  <p className="text-2xl sm:text-3xl font-bold text-foreground">{s.stat}</p>
                  <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
                </motion.div>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              {[
                {
                  icon: Terminal,
                  title: 'Real files, not snippets',
                  desc: 'You get a full project with folders, configs, migrations and a working entry point — not a gist you have to hack together.',
                },
                {
                  icon: Zap,
                  title: 'Production-first, always',
                  desc: 'Every project ships with error handling, env management, and a test suite. It\'s how a senior dev would actually set things up.',
                },
                {
                  icon: Globe,
                  title: 'Any stack, your way',
                  desc: 'Ask for Django or Go and you\'ll get Django or Go — not React and FastAPI by default. The AI reads what you actually wrote.',
                },
                {
                  icon: Cpu,
                  title: 'Agent teamwork, not autocomplete',
                  desc: 'Multiple agents argue about architecture, write tests, review each other\'s code. That tension is what makes the output solid.',
                },
              ].map((feature, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: i % 2 === 0 ? -16 : 16 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <div className={cn(
                    'flex gap-4 p-5 sm:p-6 rounded-2xl border border-border/60 bg-card',
                    'hover:border-primary/30 hover:shadow-sm transition-all duration-300 h-full'
                  )}>
                    <div className="shrink-0 w-10 h-10 rounded-xl flex items-center justify-center mt-0.5" style={{ background: 'hsl(var(--primary)/0.1)' }}>
                      <feature.icon className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-base sm:text-lg font-semibold text-foreground mb-1.5">{feature.title}</h3>
                      <p className="text-muted-foreground text-sm leading-relaxed">{feature.desc}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="pricing" className="relative overflow-hidden py-24 sm:py-32 px-4 sm:px-6">
          {/* Ambient Background Glows */}
          <div className="pointer-events-none absolute -top-24 left-1/2 -z-10 h-[500px] w-[800px] -translate-x-1/2 bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.15),transparent_70%)] blur-[100px]" />
          <div className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[400px] w-[600px] -translate-x-1/2 -translate-y-1/2 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.1),transparent_70%)] blur-[80px]" />
          
          <div className="text-center mb-16 relative z-10">
            <span className="inline-block text-xs font-bold uppercase tracking-[0.2em] text-indigo-400/80 mb-4">Pricing</span>
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight text-white mb-6">
              Pay for what you <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">actually use</span>
            </h2>
            <p className="mt-4 text-gray-400 text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed">
              Start free, no card required. Scale as you grow. <br className="hidden sm:block" />
              MIT licensed code that you own forever.
            </p>
          </div>

          <div className="relative -z-10 mx-auto max-w-6xl pointer-events-none">
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:40px_40px] opacity-20 [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] pointer-events-none" />
          </div>

          <PricingSection
            title=""
            subtitle=""
            frequencies={PAYMENT_FREQUENCIES}
            tiers={PRICING_TIERS}
          />
        </section>

        <section id="testimonials" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6 bg-muted/30">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16 sm:mb-20"
            >
              <span className="inline-block text-xs font-semibold uppercase tracking-widest text-primary/70 mb-3">Social proof</span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground">Developers who tried it, kept it</h2>
            </motion.div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {[
                {
                  name: 'Alex Chen',
                  handle: '@alexc_dev',
                  role: 'Indie Hacker · YC W24',
                  avatar: 'AC',
                  avatarBg: '#6366f1',
                  text: 'I described a SaaS with Stripe and Supabase on a Saturday morning. By lunch I had a repo I could actually deploy. Other tools give you snippets — this gave me a business.',
                  stars: 5,
                },
                {
                  name: 'Priya Nair',
                  handle: '@priya_builds',
                  role: 'Staff Engineer · Fintech',
                  avatar: 'PN',
                  avatarBg: '#0ea5e9',
                  text: 'The architecture the agents produce is surprisingly opinionated in a good way. Proper separation of concerns, real tests, a working Dockerfile. It\'s not a toy.',
                  stars: 5,
                },
                {
                  name: 'Marcus Webb',
                  handle: '@marcuswebb',
                  role: 'Startup Founder · 2× exit',
                  avatar: 'MW',
                  avatarBg: '#f59e0b',
                  text: "I cut my prototyping time from 3 days to 3 hours. The QA agent actually catches real bugs — I've seen it rewrite a whole auth layer because the first pass had a race condition.",
                  stars: 5,
                },
              ].map((t, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.12 }}
                >
                  <div className="rounded-2xl border border-border/60 bg-card p-6 h-full flex flex-col gap-4 hover:border-primary/30 hover:shadow-sm transition-all duration-300">
                    {/* Stars */}
                    <div className="flex gap-0.5">
                      {Array.from({ length: t.stars }).map((_, si) => (
                        <svg key={si} className="w-4 h-4 fill-amber-400 text-amber-400" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                      ))}
                    </div>
                    {/* Quote */}
                    <p className="text-sm sm:text-base text-foreground/80 leading-relaxed flex-1">"{t.text}"</p>
                    {/* Author */}
                    <div className="flex items-center gap-3 pt-2 border-t border-border/40">
                      <div
                        className="w-9 h-9 rounded-full flex items-center justify-center text-[11px] font-bold text-white shrink-0"
                        style={{ background: t.avatarBg }}
                      >
                        {t.avatar}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-foreground leading-none">{t.name}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{t.role}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="faq" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6">
          <div className="max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-12 sm:mb-16"
            >
              <span className="inline-block text-xs font-semibold uppercase tracking-widest text-primary/70 mb-3">Common questions</span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground">Things people ask before trying it</h2>
            </motion.div>
            <div className="divide-y divide-border/60">
              {[
                {
                  q: 'Does it actually write working code?',
                  a: 'Yes — not pseudocode, not snippets. When you ask for a FastAPI backend with PostgreSQL, you get a project with working routes, SQLAlchemy models, Alembic migrations, and a test suite. It runs.',
                },
                {
                  q: 'Which AI model powers it?',
                  a: 'By default, DeepSeek V3.2 via NVIDIA NIM. Set your NIM_API_KEY in .env and you\'re live — no local GPU, no Ollama setup. You can also swap in any OpenAI-compatible endpoint.',
                },
                {
                  q: 'What languages and frameworks are supported?',
                  a: 'Python (FastAPI, Django, Flask), Node.js (Express, NestJS), Go, TypeScript + React. The stack detector reads your prompt and chooses — or you can be explicit.',
                },
                {
                  q: 'Can I use it for a real client project?',
                  a: 'Plenty of people do. Treat the output the same way you\'d treat a senior dev\'s first draft — review it, customise it, and ship it. The MIT licence means no restrictions.',
                },
                {
                  q: 'Is the free plan actually free?',
                  a: 'Yes. The core CLI and web IDE are open source (MIT). The paid plans give you higher rate limits, team seats, and hosted deployments — but the engine itself is always free.',
                },
              ].map((faq, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.07 }}
                  className="py-6"
                >
                  <h3 className="text-base sm:text-lg font-semibold text-foreground mb-2 flex items-start gap-3">
                    <span className="text-primary/50 font-mono text-sm mt-1 shrink-0">{String(i + 1).padStart(2, '0')}</span>
                    {faq.q}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed pl-8">{faq.a}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="careers" className="relative py-20 sm:py-32 px-4 sm:px-6 overflow-hidden">
          {/* subtle radial glow */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 flex items-center justify-center"
          >
            <div className="w-[600px] h-[400px] rounded-full opacity-20 blur-[100px]" style={{ background: 'radial-gradient(ellipse, #6366f1 0%, transparent 70%)' }} />
          </div>

          <div className="relative max-w-3xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-primary/70 mb-6">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                Open beta · free to start
              </span>
              <h2 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight text-foreground mb-6">
                Stop describing code.<br />
                <span style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                  Start shipping it.
                </span>
              </h2>
              <p className="text-muted-foreground text-lg sm:text-xl mb-10 max-w-xl mx-auto leading-relaxed">
                One prompt. Seven agents. A production-ready codebase in minutes — not days.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
                <Link to="/signup">
                  <Button
                    size="lg"
                    className="text-base sm:text-lg px-8 h-12 w-full sm:w-auto font-semibold shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-shadow"
                  >
                    Build something now
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </Button>
                </Link>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    buttonVariants({ variant: 'outline', size: 'lg' }),
                    'text-base sm:text-lg px-8 h-12 inline-flex w-full sm:w-auto justify-center gap-2 font-medium'
                  )}
                >
                  <Github className="w-4 h-4" />
                  Star on GitHub
                </a>
              </div>

              <p className="mt-8 text-xs text-muted-foreground/50">No credit card. MIT licence. Works with your own NIM key.</p>
            </motion.div>
          </div>
        </section>

        <footer id="contact" className="relative border-t border-border py-10 sm:py-12 px-4 sm:px-6 bg-background pb-[max(2.5rem,env(safe-area-inset-bottom))]">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 mb-6 sm:mb-8">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-5 h-5 text-primary" />
                  <span className="font-semibold text-foreground">Vibecoder</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Turn ideas into real, runnable code.
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-4 text-foreground">Product</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>
                    <a href="#features" className="hover:text-foreground transition-colors">
                      Features
                    </a>
                  </li>
                  <li>
                    <a href="#pricing" className="hover:text-foreground transition-colors">
                      Pricing
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-foreground transition-colors">
                      Docs
                    </a>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4 text-foreground">Company</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>
                    <a href="#contact" className="hover:text-foreground transition-colors">
                      About
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-foreground transition-colors">
                      Blog
                    </a>
                  </li>
                  <li>
                    <a href="#careers" className="hover:text-foreground transition-colors">
                      Careers
                    </a>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4 text-foreground">Connect</h4>
                <div className="flex gap-4">
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Github className="w-5 h-5" />
                  </a>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Twitter className="w-5 h-5" />
                  </a>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Mail className="w-5 h-5" />
                  </a>
                </div>
              </div>
            </div>
            <Separator className="mb-8" />
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-muted-foreground text-center sm:text-left">
              <p>© 2024 Vibecoder. All rights reserved.</p>
              <div className="flex gap-6">
                <a href="#" className="hover:text-foreground transition-colors">
                  Privacy
                </a>
                <a href="#" className="hover:text-foreground transition-colors">
                  Terms
                </a>
                <a href="#" className="hover:text-foreground transition-colors">
                  License
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    );
  };

  const renderGeneratorPage = () => (
    <div className="min-h-screen pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6 bg-background">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4 text-foreground">Generate Project</h1>
            <p className="text-muted-foreground text-sm sm:text-base">
              Describe your project and let AI build it for you.
            </p>
          </div>

          <Card className="p-5 sm:p-8 bg-card border border-border shadow-sm">
            <Textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              placeholder="Describe your project idea..."
              className="min-h-[160px] sm:min-h-[200px] text-base sm:text-lg mb-6 resize-none touch-manipulation"
            />
            <Button
              onClick={handleGenerate}
              disabled={!idea.trim() || isGenerating}
              size="lg"
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  Generate Project
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </Card>

          {isGenerating && (
            <div className="space-y-4">
              <Card className="p-6 bg-card border border-border shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-primary" />
                  <span className="font-medium text-foreground">MetaGPT-style agent pipeline</span>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  {[
                    { name: 'Team Lead', status: 'active', icon: '🧠' },
                    { name: 'Planner', status: 'pending', icon: '📋' },
                    { name: 'DB Schema', status: 'pending', icon: '🗄️' },
                    { name: 'Auth', status: 'pending', icon: '🔐' },
                    { name: 'Coder', status: 'pending', icon: '⚙️' },
                    { name: 'Tester', status: 'pending', icon: '🧪' },
                    { name: 'Deployer', status: 'pending', icon: '🚀' },
                  ].map((agent, _i) => (
                    <div
                      key={agent.name}
                      className={cn(
                        'flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all',
                        agent.status === 'active'
                          ? 'bg-primary/10 border-primary text-foreground'
                          : 'bg-muted/30 border-border text-muted-foreground'
                      )}
                    >
                      <span>{agent.icon}</span>
                      <span>{agent.name}</span>
                      {agent.status === 'active' && (
                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                      )}
                    </div>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  Code = SOP(Team) — roles collaborate sequentially
                </p>
              </Card>
              {[1, 2, 3].map((i) => (
                <Card
                  key={i}
                  className="p-6 bg-card border border-border shadow-sm"
                >
                  <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-muted rounded w-3/4" />
                    <div className="h-4 bg-muted rounded w-1/2" />
                  </div>
                </Card>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );

  const FolderTree: React.FC<{
    node: FolderNode;
    level?: number;
  }> = ({ node, level = 0 }) => {
    const [isOpen, setIsOpen] = useState(level < 2);

    return (
      <div className="select-none">
        <div
          className="flex items-center gap-2 py-1 px-2 hover:bg-muted/50 rounded cursor-pointer"
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={() => node.type === 'folder' && setIsOpen(!isOpen)}
        >
          {node.type === 'folder' ? (
            <>
              {isOpen ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              <Folder className="w-4 h-4 text-primary" />
            </>
          ) : (
            <>
              <div className="w-4" />
              <Terminal className="w-4 h-4 text-muted-foreground" />
            </>
          )}
          <span className="text-sm text-foreground">{node.name}</span>
        </div>
        {node.type === 'folder' && isOpen && node.children && (
          <div>
            {node.children.map((child, i) => (
              <FolderTree key={i} node={child} level={level + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderPreviewPage = () => (
    <div className="min-h-screen pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6 bg-background">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4 text-foreground">Project Preview</h1>
            <p className="text-muted-foreground text-sm sm:text-base">
              Review your project before building.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            <Card className="p-5 sm:p-8 bg-card border border-border shadow-sm">
              <h2 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4 text-foreground">Project Summary</h2>
              <p className="text-muted-foreground mb-6">{projectData?.idea}</p>

              <h3 className="font-semibold mb-3 text-foreground">Detected Modules</h3>
              <div className="space-y-2 mb-6">
                {projectData?.modules.map((module, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary" />
                    <span className="text-sm text-muted-foreground">{module}</span>
                  </div>
                ))}
              </div>

              <h3 className="font-semibold mb-3 text-foreground">Tech Stack</h3>
              <div className="flex flex-wrap gap-2">
                {projectData?.techStack.map((tech, i) => (
                  <Badge key={i} variant="secondary">
                    {tech}
                  </Badge>
                ))}
              </div>
            </Card>

            <Card className="p-5 sm:p-8 bg-card border border-border shadow-sm">
              <h2 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4 text-foreground">Project Structure</h2>
              <div className="bg-muted/30 rounded-lg p-3 sm:p-4 max-h-[350px] sm:max-h-[500px] overflow-auto border border-border">
                {projectData?.structure.map((node, i) => (
                  <FolderTree key={i} node={node} />
                ))}
              </div>
            </Card>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
            <Button size="lg" variant="outline" className="flex-1 min-h-[44px] touch-manipulation">
              <Play className="w-5 h-5 mr-2" />
              Preview
            </Button>
            <Button size="lg" onClick={handleBuild} className="flex-1 min-h-[44px] touch-manipulation">
              Build Project
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );

  const renderBuildPage = () => {
    const steps = [
      'Initializing project structure',
      'Installing dependencies',
      'Generating components',
      'Setting up configuration',
      'Building assets',
      'Running tests',
      'Finalizing project',
    ];

    const currentStep = Math.floor((buildProgress / 100) * steps.length);

    return (
      <div className="min-h-screen pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6 bg-background">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4 text-foreground">Building Project</h1>
              <p className="text-muted-foreground text-sm sm:text-base">
                {buildProgress === 100
                  ? 'Your project is ready!'
                  : 'Please wait while we build your project...'}
              </p>
            </div>

            <Card className="p-5 sm:p-8 bg-card border border-border shadow-sm">
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2 text-foreground">
                    <span>Progress</span>
                    <span>{buildProgress}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-primary"
                      initial={{ width: 0 }}
                      animate={{ width: `${buildProgress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  {steps.map((step, i) => (
                    <div
                      key={i}
                      className={`flex items-center gap-3 p-3 rounded-lg transition-all ${i < currentStep
                        ? 'bg-primary/10 text-foreground'
                        : i === currentStep
                          ? 'bg-primary/20 text-foreground'
                          : 'text-muted-foreground'
                        }`}
                    >
                      {i < currentStep ? (
                        <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                      ) : i === currentStep ? (
                        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin flex-shrink-0" />
                      ) : (
                        <div className="w-5 h-5 border-2 border-muted rounded-full flex-shrink-0" />
                      )}
                      <span>{step}</span>
                    </div>
                  ))}
                </div>

                <Card className="p-4 bg-muted/30 border border-border">
                  <div className="font-mono text-sm space-y-1">
                    <div className="text-primary">$ npm install</div>
                    <div className="text-muted-foreground">
                      ✓ Dependencies installed
                    </div>
                    <div className="text-primary">$ npm run build</div>
                    <div className="text-muted-foreground">
                      ✓ Build completed successfully
                    </div>
                    {buildProgress === 100 && (
                      <div className="text-green-500">✓ Project ready to use</div>
                    )}
                  </div>
                </Card>

                {buildProgress === 100 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-4"
                  >
                    <Button size="lg" className="flex-1 min-h-[44px] touch-manipulation">
                      <Download className="w-5 h-5 mr-2" />
                      Download Project
                    </Button>
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={() => setCurrentPage('landing')}
                      className="min-h-[44px] touch-manipulation"
                    >
                      Create Another
                    </Button>
                  </motion.div>
                )}
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {currentPage === 'landing' ? (
        <>
          <a
            href="#manifesto"
            onClick={() => setCurrentPage('landing')}
            className={cn(
              'vibe-coder-logo fixed z-[9999] flex items-center',
              'top-[max(1rem,env(safe-area-inset-top))] left-4 sm:left-6',
              'text-base sm:text-xl md:text-2xl uppercase tracking-tight',
              'px-3 py-1 sm:px-4 sm:py-2 border rounded-full',
              'transition-all duration-300 select-none backdrop-blur-xl shadow-lg',
              theme === 'dark'
                ? 'text-white bg-white/[0.04] border-white/[0.1] hover:bg-white/[0.08] hover:border-white/[0.2]'
                : 'text-gray-900 bg-white/70 border-black/[0.06] hover:bg-white/90 hover:border-black/[0.12]'
            )}
          >
            vibecoder
          </a>
          <AnimeNavBar items={ANIME_NAV_ITEMS} defaultActive="Home" />
          <div className={cn(
            "fixed top-[max(1rem,env(safe-area-inset-top))] right-4 sm:right-6 z-[9999]",
            "flex items-center gap-2 sm:gap-3 px-2 py-1.5 rounded-full border backdrop-blur-xl shadow-lg transition-all duration-300",
            theme === 'dark'
              ? 'bg-white/[0.04] border-white/[0.1] shadow-black/20'
              : 'bg-white/70 border-black/[0.06] shadow-black/5'
          )}>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className={cn(
                'rounded-full h-8 w-8 sm:h-9 sm:w-9 transition-colors',
                theme === 'dark'
                  ? 'hover:bg-white/10 text-white'
                  : 'hover:bg-black/5 text-gray-700'
              )}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </Button>
            <Separator orientation="vertical" className="h-4 bg-border/20" />
            <Link to="/login">
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  'h-8 sm:h-9 px-3 sm:px-4 rounded-full transition-all',
                  theme === 'dark'
                    ? 'text-white/80 hover:text-white hover:bg-white/10'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-black/5'
                )}
              >
                Login
              </Button>
            </Link>
            <Link to="/signup">
              <Button
                size="sm"
                className={cn(
                  'h-8 sm:h-9 px-4 sm:px-5 rounded-full transition-all font-semibold',
                  theme === 'dark'
                    ? 'bg-white text-black hover:bg-neutral-200'
                    : 'bg-black text-white hover:bg-neutral-800'
                )}
              >
                Sign Up
              </Button>
            </Link>
          </div>
        </>
      ) : (
        renderNavbar()
      )}
      {currentPage === 'landing' && renderLandingPage()}
      {currentPage === 'generator' && renderGeneratorPage()}
      {currentPage === 'preview' && renderPreviewPage()}
      {currentPage === 'build' && renderBuildPage()}
    </div>
  );
};

export default VibeCober;
