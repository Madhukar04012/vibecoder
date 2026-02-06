import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
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
} from 'lucide-react';

import { Header } from '@/components/ui/header-1';
import { DottedSurface } from '@/components/ui/dotted-surface';

type Page = 'landing' | 'generator' | 'preview' | 'build';

interface FolderNode {
  name: string;
  type: 'file' | 'folder';
  children?: FolderNode[];
}

interface ProjectData {
  idea: string;
  modules: string[];
  techStack: string[];
  structure: FolderNode[];
}

type ButtonVariant = 'default' | 'ghost' | 'outline';

type ButtonSize = 'sm' | 'lg' | 'icon';

function cx(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(' ');
}

function Button({
  children,
  className,
  disabled,
  onClick,
  size = 'sm',
  type = 'button',
  variant = 'default',
  ariaLabel,
}: {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
  size?: ButtonSize;
  type?: 'button' | 'submit';
  variant?: ButtonVariant;
  ariaLabel?: string;
}) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/40 dark:focus:ring-blue-300/30 disabled:opacity-50 disabled:pointer-events-none backdrop-blur-xl border';

  const sizes: Record<ButtonSize, string> = {
    sm: 'h-9 px-3 text-sm',
    lg: 'h-11 px-5 text-base',
    icon: 'h-10 w-10 p-0',
  };

  const variants: Record<ButtonVariant, string> = {
    default:
      'border-gray-200/70 bg-white/70 text-gray-900 hover:bg-white/80 dark:border-gray-800/60 dark:bg-white/10 dark:text-gray-100 dark:hover:bg-white/15',
    ghost: 'border-transparent bg-transparent text-gray-800 hover:bg-gray-100/60 dark:text-gray-200 dark:hover:bg-white/10',
    outline:
      'border-gray-200/70 bg-white/40 text-gray-900 hover:bg-white/60 dark:border-gray-800/60 dark:bg-white/5 dark:text-gray-100 dark:hover:bg-white/10',
  };

  return (
    <button
      type={type}
      className={cx(base, sizes[size], variants[variant], className)}
      disabled={disabled}
      onClick={onClick}
      aria-label={ariaLabel}
      title={ariaLabel}
    >
      {children}
    </button>
  );
}

function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cx(
        'rounded-2xl border border-gray-200/70 bg-white/60 backdrop-blur-xl dark:border-gray-800/60 dark:bg-white/5',
        className
      )}
    >
      {children}
    </div>
  );
}

function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-full border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-700 dark:border-gray-800 dark:bg-white/5 dark:text-gray-200',
        className
      )}
    >
      {children}
    </span>
  );
}

function Separator({ className }: { className?: string }) {
  return <div className={cx('h-px w-full bg-gray-200 dark:bg-gray-800', className)} />;
}

export default function App() {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [idea, setIdea] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [buildProgress, setBuildProgress] = useState(0);

  const handleGenerate = async () => {
    if (!idea.trim()) return;

    setIsGenerating(true);
    setCurrentPage('generator');

    setTimeout(() => {
      setProjectData({
        idea,
        modules: ['Authentication', 'Database', 'API Routes', 'Frontend UI', 'State Management'],
        techStack: ['React', 'TypeScript', 'Tailwind CSS', 'Node.js', 'PostgreSQL', 'Prisma'],
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

    const intervalId = setInterval(() => {
      setBuildProgress((prev) => {
        if (prev >= 100) {
          clearInterval(intervalId);
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  const LandingPage = () => {
    const [placeholder, setPlaceholder] = useState('');
    const fullPlaceholder = 'Make me a SaaS app with authentication and payments...';

    useEffect(() => {
      let index = 0;
      const intervalId = setInterval(() => {
        if (index <= fullPlaceholder.length) {
          setPlaceholder(fullPlaceholder.slice(0, index));
          index++;
        } else {
          clearInterval(intervalId);
        }
      }, 50);

      return () => clearInterval(intervalId);
    }, []);

    return (
      <div className="min-h-screen bg-gradient-to-b from-white via-white to-gray-50 dark:from-gray-950 dark:via-gray-950 dark:to-black">
        <DottedSurface className="opacity-90" />

        <section className="relative z-10 min-h-screen flex items-center justify-center px-6 pt-32 pb-20">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
              <h1 className="text-7xl md:text-8xl font-bold tracking-tight mb-6 bg-gradient-to-br from-gray-900 to-gray-500 bg-clip-text text-transparent dark:from-white dark:to-gray-400">
                VibeCober
              </h1>
              <p className="text-2xl md:text-3xl text-gray-500 mb-12 dark:text-gray-300">Turn ideas into real, runnable code.</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative max-w-2xl mx-auto"
            >
              <div className="relative">
                <textarea
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey && idea.trim()) {
                      e.preventDefault();
                      void handleGenerate();
                    }
                  }}
                  placeholder={placeholder}
                  className="min-h-[120px] w-full text-lg rounded-2xl bg-white/50 text-gray-900 placeholder:text-gray-500 backdrop-blur-xl border border-gray-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 transition-all resize-none pr-14 p-4 outline-none dark:bg-gray-950/40 dark:text-gray-100 dark:placeholder:text-gray-500 dark:border-gray-800"
                />
                <Button
                  onClick={() => void handleGenerate()}
                  disabled={!idea.trim()}
                  size="icon"
                  className="absolute bottom-4 right-4 rounded-full"
                  ariaLabel="Generate"
                >
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </div>
              <p className="text-sm text-gray-500 mt-3 dark:text-gray-300">Press Enter to generate</p>
            </motion.div>
          </div>
        </section>

        <section id="how-it-works" className="relative py-32 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold text-center mb-20 text-gray-900 dark:text-gray-100"
            >
              How it works
            </motion.h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                { icon: Sparkles, title: 'Analyze', desc: 'AI understands your idea and plans the architecture' },
                { icon: Code2, title: 'Generate', desc: 'Creates production-ready code with best practices' },
                { icon: Zap, title: 'Run', desc: 'Get a fully functional project ready to deploy' },
              ].map((step, i) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.2 }}
                >
                  <Card className="p-8 bg-white/50 backdrop-blur-xl border-gray-200 hover:border-blue-300/50 transition-all dark:bg-white/5 dark:border-gray-800">
                    <step.icon className="w-12 h-12 text-blue-600 mb-6" />
                    <h3 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-gray-100">{step.title}</h3>
                    <p className="text-gray-500 dark:text-gray-300">{step.desc}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="features" className="relative py-32 px-6 bg-transparent">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold text-center mb-20 text-gray-900 dark:text-gray-100"
            >
              Why developers like it
            </motion.h2>
            <div className="grid md:grid-cols-2 gap-6">
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
                  desc: 'Runs on your machine with Ollama/Mistral. No subscriptions.',
                },
                {
                  title: 'CLI + Web support',
                  desc: 'Use it however you prefer. Terminal or browser.',
                },
              ].map((feature, i) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className="p-6 bg-white/50 backdrop-blur-xl border-gray-200 dark:bg-white/5 dark:border-gray-800">
                    <CheckCircle2 className="w-8 h-8 text-blue-600 mb-4" />
                    <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">{feature.title}</h3>
                    <p className="text-gray-500 dark:text-gray-300">{feature.desc}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="pricing" className="relative py-32 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold text-center mb-20 text-gray-900 dark:text-gray-100"
            >
              Simple pricing
            </motion.h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  name: 'Free',
                  price: '$0',
                  features: ['Local AI models', 'Unlimited projects', 'CLI access', 'Community support'],
                },
                {
                  name: 'Pro',
                  price: '$19',
                  features: ['Everything in Free', 'Cloud sync', 'Priority support', 'Advanced templates'],
                  highlight: true,
                },
                {
                  name: 'Team',
                  price: '$49',
                  features: ['Everything in Pro', 'Team collaboration', 'Custom models', 'Dedicated support'],
                },
              ].map((plan, i) => (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card
                    className={cx(
                      'p-8 bg-white/50 backdrop-blur-xl dark:bg-white/5',
                      plan.highlight && 'border-blue-600/40 bg-blue-50/40 dark:bg-blue-500/10'
                    )}
                  >
                    <h3 className="text-2xl font-bold mb-2 text-gray-900 dark:text-gray-100">{plan.name}</h3>
                    <div className="text-4xl font-bold mb-6 text-gray-900 dark:text-gray-100">
                      {plan.price}
                      <span className="text-lg text-gray-500 font-normal dark:text-gray-300">/mo</span>
                    </div>
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-center gap-2">
                          <CheckCircle2 className="w-5 h-5 text-blue-600 flex-shrink-0" />
                          <span className="text-gray-600 dark:text-gray-300">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button
                      className="w-full"
                      variant={plan.highlight ? 'default' : 'outline'}
                      size="lg"
                      onClick={() => navigate('/signup')}
                    >
                      Get started
                    </Button>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="testimonials" className="relative py-32 px-6 bg-transparent">
          <div className="max-w-6xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold text-center mb-20 text-gray-900 dark:text-gray-100"
            >
              Trusted by developers
            </motion.h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                { name: 'Alex Chen', role: 'Indie Hacker', text: 'Shipped my MVP in 2 days. This is insane.' },
                { name: 'Sarah Kim', role: 'Startup Founder', text: 'Finally, an AI tool that generates real code.' },
                { name: 'Mike Johnson', role: 'Senior Dev', text: "Best prototyping tool I've used. Period." },
              ].map((testimonial, i) => (
                <motion.div
                  key={testimonial.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className="p-6 bg-white/50 backdrop-blur-xl border-gray-200 dark:bg-white/5 dark:border-gray-800">
                    <p className="text-gray-600 mb-6 italic dark:text-gray-300">"{testimonial.text}"</p>
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">{testimonial.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-300">{testimonial.role}</p>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="faq" className="relative py-32 px-6">
          <div className="max-w-3xl mx-auto">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold text-center mb-20 text-gray-900 dark:text-gray-100"
            >
              FAQ
            </motion.h2>
            <div className="space-y-6">
              {[
                {
                  q: 'How does local AI work?',
                  a: 'VibeCober uses Ollama to run AI models directly on your machine. No data leaves your computer.',
                },
                {
                  q: 'What languages are supported?',
                  a: 'Currently supports JavaScript, TypeScript, Python, and Go. More coming soon.',
                },
                { q: 'Can I customize the output?', a: 'Yes. You can modify templates and add your own patterns.' },
                { q: 'Is it really free?', a: 'Yes. The core tool is open source and free forever.' },
              ].map((faq) => (
                <motion.div
                  key={faq.q}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.1 }}
                >
                  <Card className="p-6 bg-white/50 backdrop-blur-xl border-gray-200 dark:bg-white/5 dark:border-gray-800">
                    <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100">{faq.q}</h3>
                    <p className="text-gray-600 dark:text-gray-300">{faq.a}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="contact" className="relative py-32 px-6 bg-transparent">
          <div className="max-w-4xl mx-auto text-center">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold mb-8 text-gray-900 dark:text-gray-100"
            >
              Ready to build?
            </motion.h2>
            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-xl text-gray-500 mb-12 dark:text-gray-300"
            >
              Join thousands of developers shipping faster with VibeCober
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Button size="lg" className="text-lg px-8" onClick={() => navigate('/signup')}>
                Get Started Free
              </Button>
              <Button size="lg" variant="outline" className="text-lg px-8">
                View on GitHub
              </Button>
            </motion.div>
          </div>
        </section>

        <footer className="relative border-t border-gray-200 py-12 px-6 dark:border-gray-800">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8 mb-8">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-gray-900 dark:text-gray-100">VibeCober</span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-300">Turn ideas into real, runnable code.</p>
              </div>
              <div>
                <h4 className="font-semibold mb-4 text-gray-900 dark:text-gray-100">Product</h4>
                <ul className="space-y-2 text-sm text-gray-500 dark:text-gray-300">
                  <li>
                    <a href="#features" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                      Features
                    </a>
                  </li>
                  <li>
                    <a href="#pricing" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                      Pricing
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                      Docs
                    </a>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4 text-gray-900 dark:text-gray-100">Company</h4>
                <ul className="space-y-2 text-sm text-gray-500 dark:text-gray-300">
                  <li>
                    <a href="#" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                      About
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                      Blog
                    </a>
                  </li>
                  <li>
                    <a href="#careers" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                      Careers
                    </a>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4 text-gray-900 dark:text-gray-100">Connect</h4>
                <div className="flex gap-4">
                  <a
                    href="#"
                    className="text-gray-500 hover:text-gray-900 transition-colors dark:text-gray-300 dark:hover:text-gray-100"
                    aria-label="GitHub"
                    title="GitHub"
                  >
                    <Github className="w-5 h-5" />
                  </a>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-gray-900 transition-colors dark:text-gray-300 dark:hover:text-gray-100"
                    aria-label="Twitter"
                    title="Twitter"
                  >
                    <Twitter className="w-5 h-5" />
                  </a>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-gray-900 transition-colors dark:text-gray-300 dark:hover:text-gray-100"
                    aria-label="Email"
                    title="Email"
                  >
                    <Mail className="w-5 h-5" />
                  </a>
                </div>
              </div>
            </div>
            <Separator className="mb-8" />
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-500 dark:text-gray-300">
              <p>© 2026 VibeCober. All rights reserved.</p>
              <div className="flex gap-6">
                <a href="#" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                  Privacy
                </a>
                <a href="#" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                  Terms
                </a>
                <a href="#" className="hover:text-gray-900 transition-colors dark:hover:text-gray-100">
                  License
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    );
  };

  const GeneratorPage = () => (
    <div className="min-h-screen pt-32 pb-20 px-6 bg-white dark:bg-gray-950">
      <div className="max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold mb-4 text-gray-900 dark:text-gray-100">Generate Project</h1>
            <p className="text-gray-500 dark:text-gray-300">Describe your project and let AI build it for you.</p>
          </div>

          <Card className="p-8">
            <textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              placeholder="Describe your project idea..."
              className="min-h-[200px] w-full text-lg mb-6 resize-none rounded-2xl bg-white/60 text-gray-900 placeholder:text-gray-500 backdrop-blur-xl border border-gray-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 transition-all p-4 outline-none dark:bg-gray-950/40 dark:text-gray-100 dark:placeholder:text-gray-500 dark:border-gray-800"
            />
            <Button
              onClick={() => void handleGenerate()}
              disabled={!idea.trim() || isGenerating}
              size="lg"
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin dark:border-gray-900 dark:border-t-transparent" />
                  Generating...
                </>
              ) : (
                <>
                  Generate Project
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </Button>
          </Card>

          {isGenerating && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="p-6">
                  <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-gray-200 rounded w-3/4 dark:bg-gray-800" />
                    <div className="h-4 bg-gray-200 rounded w-1/2 dark:bg-gray-800" />
                  </div>
                </Card>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );

  const FolderTree = ({ node, level = 0 }: { node: FolderNode; level?: number }) => {
    const [isOpen, setIsOpen] = useState(level < 2);

    return (
      <div className="select-none">
        <div
          className="flex items-center gap-2 py-1 px-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded cursor-pointer"
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={() => node.type === 'folder' && setIsOpen(!isOpen)}
        >
          {node.type === 'folder' ? (
            <>
              {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <Folder className="w-4 h-4 text-blue-600" />
            </>
          ) : (
            <>
              <div className="w-4" />
              <Terminal className="w-4 h-4 text-gray-400 dark:text-gray-500" />
            </>
          )}
          <span className="text-sm text-gray-800 dark:text-gray-200">{node.name}</span>
        </div>
        {node.type === 'folder' && isOpen && node.children && (
          <div>
            {node.children.map((child) => (
              <FolderTree key={`${level}-${child.name}`} node={child} level={level + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  const PreviewPage = () => (
    <div className="min-h-screen pt-32 pb-20 px-6 bg-white dark:bg-gray-950">
      <div className="max-w-6xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold mb-4 text-gray-900 dark:text-gray-100">Project Preview</h1>
            <p className="text-gray-500 dark:text-gray-300">Review your project before building.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <Card className="p-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Project Summary</h2>
              <p className="text-gray-600 mb-6 dark:text-gray-300">{projectData?.idea}</p>

              <h3 className="font-semibold mb-3 text-gray-900 dark:text-gray-100">Detected Modules</h3>
              <div className="space-y-2 mb-6">
                {projectData?.modules.map((module) => (
                  <div key={module} className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-600" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{module}</span>
                  </div>
                ))}
              </div>

              <h3 className="font-semibold mb-3 text-gray-900 dark:text-gray-100">Tech Stack</h3>
              <div className="flex flex-wrap gap-2">
                {projectData?.techStack.map((tech) => (
                  <Badge key={tech}>{tech}</Badge>
                ))}
              </div>
            </Card>

            <Card className="p-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Project Structure</h2>
              <div className="rounded-lg p-4 max-h-[500px] overflow-auto border border-gray-200/70 bg-white/40 backdrop-blur-xl dark:border-gray-800/60 dark:bg-white/5">
                {projectData?.structure.map((node) => (
                  <FolderTree key={node.name} node={node} />
                ))}
              </div>
            </Card>
          </div>

          <div className="flex gap-4">
            <Button size="lg" variant="outline" className="flex-1">
              <Play className="w-5 h-5" />
              Preview
            </Button>
            <Button size="lg" onClick={handleBuild} className="flex-1">
              Build Project
              <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );

  const BuildPage = () => {
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
      <div className="min-h-screen pt-32 pb-20 px-6 bg-white dark:bg-gray-950">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <div>
              <h1 className="text-4xl font-bold mb-4 text-gray-900 dark:text-gray-100">Building Project</h1>
              <p className="text-gray-500 dark:text-gray-300">
                {buildProgress === 100 ? 'Your project is ready!' : 'Please wait while we build your project...'}
              </p>
            </div>

            <Card className="p-8">
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2 text-gray-700 dark:text-gray-300">
                    <span>Progress</span>
                    <span>{buildProgress}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden dark:bg-gray-800">
                    <motion.div
                      className="h-full bg-blue-600"
                      initial={{ width: 0 }}
                      animate={{ width: `${buildProgress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  {steps.map((step, i) => (
                    <div
                      key={step}
                      className={cx(
                        'flex items-center gap-3 p-3 rounded-lg transition-all',
                        i < currentStep
                          ? 'bg-blue-50 text-gray-900 dark:bg-blue-500/10 dark:text-gray-100'
                          : i === currentStep
                          ? 'bg-blue-100/60 text-gray-900 dark:bg-blue-500/15 dark:text-gray-100'
                          : 'text-gray-500 dark:text-gray-300'
                      )}
                    >
                      {i < currentStep ? (
                        <CheckCircle2 className="w-5 h-5 text-blue-600 flex-shrink-0" />
                      ) : i === currentStep ? (
                        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                      ) : (
                        <div className="w-5 h-5 border-2 border-gray-200 rounded-full flex-shrink-0 dark:border-gray-700" />
                      )}
                      <span>{step}</span>
                    </div>
                  ))}
                </div>

                <Card className="p-4 bg-white/40 dark:bg-white/5">
                  <div className="font-mono text-sm space-y-1">
                    <div className="text-blue-600">$ npm install</div>
                    <div className="text-gray-500 dark:text-gray-300">✓ Dependencies installed</div>
                    <div className="text-blue-600">$ npm run build</div>
                    <div className="text-gray-500 dark:text-gray-300">✓ Build completed successfully</div>
                    {buildProgress === 100 && <div className="text-green-600">✓ Project ready to use</div>}
                  </div>
                </Card>

                {buildProgress === 100 && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4">
                    <Button size="lg" className="flex-1">
                      <Download className="w-5 h-5" />
                      Download Project
                    </Button>
                    <Button size="lg" variant="outline" onClick={() => setCurrentPage('landing')}>
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
    <div className="min-h-screen bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      <Header
        onLogoClick={() => {
          setCurrentPage('landing');
          navigate('/');
        }}
        onSignIn={() => navigate('/login')}
        onGetStarted={() => navigate('/signup')}
      />
      <AnimatePresence mode="wait">
        {currentPage === 'landing' && <LandingPage key="landing" />}
        {currentPage === 'generator' && <GeneratorPage key="generator" />}
        {currentPage === 'preview' && <PreviewPage key="preview" />}
        {currentPage === 'build' && <BuildPage key="build" />}
      </AnimatePresence>
    </div>
  );
}
