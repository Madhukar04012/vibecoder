import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { DottedSurface } from '@/components/ui/dotted-surface';
import { AnimeNavBar } from '@/components/ui/anime-navbar';
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

const ANIME_NAV_ITEMS = [
  { name: 'Home', url: '#manifesto', icon: Home },
  { name: 'Discover', url: '#discover', icon: Compass },
  { name: 'Pricing', url: '#pricing', icon: CreditCard },
  { name: 'About', url: '#careers', icon: Info },
];

const VibeCober: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [idea, setIdea] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [buildProgress, setBuildProgress] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Manifesto
              </a>
              <a
                href="#careers"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Careers
              </a>
              <a
                href="#discover"
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
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Manifesto
              </a>
              <a
                href="#careers"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Careers
              </a>
              <a
                href="#discover"
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
    const [placeholder, setPlaceholder] = useState('');
    const fullPlaceholder =
      'Make me a SaaS app with authentication and payments...';

    useEffect(() => {
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
    }, []);

    return (
      <div className="relative min-h-screen overflow-hidden">
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

        <section id="manifesto" className="relative z-10 min-h-screen flex items-center justify-center px-4 sm:px-6 pt-28 sm:pt-36 md:pt-32 pb-12 sm:pb-20">
          <div className="max-w-4xl mx-auto text-center space-y-6 sm:space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1
                className={cn(
                  'text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-4 sm:mb-6',
                  theme === 'dark' ? 'text-foreground' : 'text-[#333333]'
                )}
              >
                Vibecoder
              </h1>
              <p
                className={cn(
                  'text-lg sm:text-xl md:text-2xl lg:text-3xl font-normal mb-8 sm:mb-12 px-2',
                  theme === 'dark' ? 'text-muted-foreground' : 'text-[#555555]'
                )}
              >
                Turn ideas into real, runnable code.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative max-w-2xl mx-auto px-2 sm:px-0"
            >
              <div className="relative">
                <Textarea
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  onKeyDown={(e) => {
                    if (
                      e.key === 'Enter' &&
                      !e.shiftKey &&
                      idea.trim()
                    ) {
                      e.preventDefault();
                      handleGenerate();
                    }
                  }}
                  placeholder={placeholder}
                  className={cn(
                    'min-h-[100px] sm:min-h-[120px] text-base sm:text-lg bg-background/80 backdrop-blur-xl border-border focus:border-primary transition-all resize-none pr-12 sm:pr-14 py-4 touch-manipulation',
                    theme === 'light' && 'placeholder:text-[#AAAAAA] bg-white border-[#e5e5e5]'
                  )}
                />
                <Button
                  onClick={handleGenerate}
                  disabled={!idea.trim()}
                  size="icon"
                  className={cn(
                    'absolute bottom-3 right-3 sm:bottom-4 sm:right-4 rounded-full h-10 w-10 sm:h-11 sm:w-11 touch-manipulation',
                    theme === 'light' && 'bg-[#888888] text-white hover:bg-[#777777]'
                  )}
                >
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </div>
              <p
                className={cn(
                  'text-sm font-normal mt-3',
                  theme === 'dark' ? 'text-muted-foreground' : 'text-[#888888]'
                )}
              >
                Press Enter to generate
              </p>
            </motion.div>
          </div>
        </section>

        <section id="how-it-works" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl md:text-5xl font-bold text-center mb-12 sm:mb-16 md:mb-20 text-foreground"
            >
              How it works
            </motion.h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {[
                {
                  icon: Sparkles,
                  title: 'Analyze',
                  desc: 'Team Lead Brain + Planner decide architecture (MetaGPT-style)',
                },
                {
                  icon: Code2,
                  title: 'Generate',
                  desc: 'DB, Auth, Coder agents create production-ready code',
                },
                {
                  icon: Zap,
                  title: 'Run',
                  desc: 'Tester + Deployer finish the pipeline. Ready to ship.',
                },
              ].map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.2 }}
                >
                  <Card className="p-6 sm:p-8 bg-card border border-border shadow-sm hover:border-primary/50 transition-all">
                    <step.icon className="w-10 h-10 sm:w-12 sm:h-12 text-primary mb-4 sm:mb-6" />
                    <h3 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4 text-foreground">{step.title}</h3>
                    <p className="text-muted-foreground text-sm sm:text-base">{step.desc}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="discover" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6 bg-muted/50">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl md:text-5xl font-bold text-center mb-12 sm:mb-16 md:mb-20 text-foreground"
            >
              Why developers like it
            </motion.h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              {[
                {
                  title: 'Production-first output',
                  desc: 'Real, deployable code with proper structure and best practices',
                },
                {
                  title: 'Real files, not snippets',
                  desc: 'Complete project structure with all necessary configurations',
                },
                {
                  title: 'Local AI, zero API cost',
                  desc: 'Powered by DeepSeek via NVIDIA NIM. No local install required.',
                },
                {
                  title: 'CLI + Web support',
                  desc: 'Use it however you prefer. Terminal or browser.',
                },
              ].map((feature, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className="p-5 sm:p-6 bg-card border border-border shadow-sm">
                    <CheckCircle2 className="w-6 h-6 sm:w-8 sm:h-8 text-primary mb-3 sm:mb-4" />
                    <h3 className="text-lg sm:text-xl font-semibold mb-2 text-foreground">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground text-sm sm:text-base">{feature.desc}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="pricing" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl md:text-5xl font-bold text-center mb-12 sm:mb-16 md:mb-20 text-foreground"
            >
              Simple pricing
            </motion.h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {[
                {
                  name: 'Free',
                  price: '$0',
                  features: [
                    'Local AI models',
                    'Unlimited projects',
                    'CLI access',
                    'Community support',
                  ],
                },
                {
                  name: 'Pro',
                  price: '$19',
                  features: [
                    'Everything in Free',
                    'Cloud sync',
                    'Priority support',
                    'Advanced templates',
                  ],
                  highlight: true,
                },
                {
                  name: 'Team',
                  price: '$49',
                  features: [
                    'Everything in Pro',
                    'Team collaboration',
                    'Custom models',
                    'Dedicated support',
                  ],
                },
              ].map((plan, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card
                    className={`p-6 sm:p-8 ${plan.highlight
                      ? 'border-2 border-primary bg-primary/5'
                      : 'bg-card border border-border'
                      } shadow-sm`}
                  >
                    <h3 className="text-xl sm:text-2xl font-bold mb-2 text-foreground">{plan.name}</h3>
                    <div className="text-3xl sm:text-4xl font-bold mb-4 sm:mb-6 text-foreground">
                      {plan.price}
                      <span className="text-lg text-muted-foreground">/mo</span>
                    </div>
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature, j) => (
                        <li key={j} className="flex items-center gap-2">
                          <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                          <span className="text-muted-foreground">
                            {feature}
                          </span>
                        </li>
                      ))}
                    </ul>
                    <Link to="/signup">
                      <Button
                        className="w-full"
                        variant={plan.highlight ? 'default' : 'outline'}
                      >
                        Get started
                      </Button>
                    </Link>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="testimonials" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6 bg-muted/50">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl md:text-5xl font-bold text-center mb-12 sm:mb-16 md:mb-20 text-foreground"
            >
              Trusted by developers
            </motion.h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {[
                {
                  name: 'Alex Chen',
                  role: 'Indie Hacker',
                  text: 'Shipped my MVP in 2 days. This is insane.',
                },
                {
                  name: 'Sarah Kim',
                  role: 'Startup Founder',
                  text: 'Finally, an AI tool that generates real code.',
                },
                {
                  name: 'Mike Johnson',
                  role: 'Senior Dev',
                  text: "Best prototyping tool I've used. Period.",
                },
              ].map((testimonial, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className="p-6 bg-card border border-border shadow-sm">
                    <p className="text-muted-foreground mb-6 italic">
                      &quot;{testimonial.text}&quot;
                    </p>
                    <div>
                      <p className="font-semibold text-foreground">{testimonial.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {testimonial.role}
                      </p>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="faq" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6">
          <div className="max-w-3xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl md:text-5xl font-bold text-center mb-12 sm:mb-16 md:mb-20 text-foreground"
            >
              FAQ
            </motion.h2>
            <div className="space-y-4 sm:space-y-6">
              {[
                {
                  q: 'How does the AI work?',
                  a: 'Vibecoder uses NVIDIA NIM with DeepSeek. Set NIM_API_KEY in .env to connect. No local model install required.',
                },
                {
                  q: 'What languages are supported?',
                  a: 'Currently supports JavaScript, TypeScript, Python, and Go. More coming soon.',
                },
                {
                  q: 'Can I customize the output?',
                  a: 'Yes. You can modify templates and add your own patterns.',
                },
                {
                  q: 'Is it really free?',
                  a: 'Yes. The core tool is open source and free forever.',
                },
              ].map((faq, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className="p-6 bg-card border border-border shadow-sm">
                    <h3 className="text-lg font-semibold mb-2 text-foreground">{faq.q}</h3>
                    <p className="text-muted-foreground">{faq.a}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="careers" className="relative py-16 sm:py-24 md:py-32 px-4 sm:px-6 bg-muted/50">
          <div className="max-w-4xl mx-auto text-center">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6 sm:mb-8 text-foreground"
            >
              Ready to build?
            </motion.h2>
            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-base sm:text-lg md:text-xl text-muted-foreground mb-8 sm:mb-12 px-2"
            >
              Join thousands of developers shipping faster with Vibecoder
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-2"
            >
              <Link to="/signup">
                <Button size="lg" className="text-base sm:text-lg px-6 sm:px-8 w-full sm:w-auto min-h-[44px] touch-manipulation">
                  Get Started Free
                </Button>
              </Link>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className={cn(buttonVariants({ variant: 'outline', size: 'lg' }), 'text-base sm:text-lg px-6 sm:px-8 inline-flex w-full sm:w-auto justify-center min-h-[44px] touch-manipulation')}
              >
                View on GitHub
              </a>
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
                  ].map((agent, i) => (
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
              'px-2.5 py-1 sm:px-3 sm:py-1.5 border-2 rounded-[2px]',
              'transition-colors select-none',
              theme === 'dark'
                ? 'text-white border-white/90 hover:border-white'
                : 'text-gray-900 border-gray-900 hover:border-gray-700'
            )}
          >
            vibecoder
          </a>
          <AnimeNavBar items={ANIME_NAV_ITEMS} defaultActive="Home" />
          <div className="fixed top-[max(1rem,env(safe-area-inset-top))] right-4 sm:right-6 z-[9999] flex items-center gap-2 sm:gap-3">
            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              className={cn(
                'rounded-full backdrop-blur-lg h-9 w-9 sm:h-10 sm:w-10 touch-manipulation',
                theme === 'dark'
                  ? 'bg-black/30 border-white/10'
                  : 'bg-white/80 border-gray-200/80'
              )}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-white" />
              ) : (
                <Moon className="w-4 h-4 text-gray-700" />
              )}
            </Button>
            <Link to="/login">
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  'touch-manipulation min-h-[44px] sm:min-h-0',
                  theme === 'dark'
                    ? 'text-white/80 hover:text-white hover:bg-white/10'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/60'
                )}
              >
                Login
              </Button>
            </Link>
            <Link to="/signup">
              <Button
                size="sm"
                className={cn(
                  'touch-manipulation min-h-[44px] sm:min-h-0 px-3 sm:px-4',
                  theme === 'dark'
                    ? 'bg-white text-black hover:bg-white/90'
                    : 'bg-gray-800 text-white hover:bg-gray-700'
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
